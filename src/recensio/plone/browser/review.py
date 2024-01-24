from AccessControl.SecurityManagement import getSecurityManager
from html import escape
from plone import api
from plone.autoform.interfaces import WIDGETS_KEY
from plone.autoform.utils import _process_widgets
from plone.dexterity.utils import iterSchemata
from plone.memoize.view import memoize
from plone.supermodel.utils import mergedTaggedValueDict
from Products.Five.browser import BrowserView
from Products.PortalTransforms.libtransforms.utils import scrubHTML
from recensio.plone import _
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.behaviors.authors import IAuthors
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.base_review import generateDoi
from recensio.plone.behaviors.editorial import IEditorial
from recensio.plone.browser.canonical import CanonicalURLHelper
from recensio.plone.utils import get_formatted_names
from recensio.plone.utils import getFormatter
from recensio.plone.utils import punctuated_title_and_subtitle
from z3c.form.field import Fields
from z3c.form.form import DisplayForm
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import IWidgets
from zope.component import getMultiAdapter
from ZTUtils import make_query


class View(BrowserView, CanonicalURLHelper):
    """Moderation View."""

    openurl_terms = {
        "title": "rft.btitle",
        "issn": "rft.issn",
        "isbn": "rft.isbn",
        "publisher": "rft.pub",
        "metadata_review_author": "rft.au",
        "placeOfPublication": "rft.place",
        "yearOfPublication": "rft.date",
        "series": "rft.series",
        "pageStartOfReviewInJournal": "rft.spage",
        "pageEndOfReviewInJournal": "rft.epage",
        "get_journal_title": "rft.jtitle",
        "pages": "rft.pages",
    }

    @property
    def metadata_fields(self):
        # Return an ordered list of fields used for the metadata area of the
        # view, depending on the content type.
        raise NotImplementedError("Subclasses must implement this method")

    @property
    @memoize
    def fields(self):
        """Get all the fields of all schemata, including behaviors."""
        fields = []
        schemata = iterSchemata(self.context)
        for schema in schemata:
            for attr in schema.names():
                fields.append(schema.get(attr))
        return fields

    @property
    @memoize
    def widgets(self):
        """Get all the widgets for all the fields fields in display mode.

        Difference to the plone.dexterity DefaultView:
        - Shows all widgets, regardless of their omit settings.
        - Does not group the widgets in main and fieldset groups.

        See also:
        - plone.dexterity.browser.view.DefaultView
        - plone.autoform.view.WidgetsView
        - z3c.form.form.DisplayForm
        """
        form = DisplayForm(self.context, self.request)
        form.fields = Fields(*self.fields)

        # honor widget hints so that DataGridField works
        for schema in iterSchemata(self.context):
            widget_hints = mergedTaggedValueDict(schema, WIDGETS_KEY)
            _process_widgets(form, widget_hints, {}, form.fields)

        widgets = getMultiAdapter((form, self.request, self.context), IWidgets)
        widgets.mode = DISPLAY_MODE
        widgets.ignoreContext = False
        widgets.ignoreReadonly = False
        widgets.ignoreRequest = True
        widgets.prefix = ""
        widgets.update()

        return widgets

    def get_label(self, field):
        """Return the metadata label for a field of a particular
        portal_type."""
        return self.widgets[field].label

    def get_metadata_review_author(self):
        return get_formatted_names(
            self.context.reviewAuthors,
            lastname_first=True,
            full_name_separator=" <br/> ",
        )

    def _get_gnd_link(self, gnd_id):
        return (
            '&nbsp;<span class="gnd-link">'
            '<a href="https://d-nb.info/gnd/%s" title="%s" target="_blank">'
            '<img src="++resource++recensio.theme.images/gnd.svg"'
            'class="gnd" alt="GND" />'
            "</a>"
            "</span>"
        ) % (
            gnd_id,
            self.context.translate(_("Person in the Integrated Authority File")),
        )

    def list_rows(self, rows, *keys):
        _keys = keys

        def _gettr(row, key):
            return getattr(row, key, row.get(key, ""))

        # Get the target objects in case of a RelationValue object.
        rows = map(lambda row: getattr(row, "to_object", row), rows)
        # Remove empty rows.
        rows = filter(lambda row: any([_gettr(row, key) for key in _keys]), rows)
        result = ""
        for row in rows:
            inner = ", ".join(
                [escape(_gettr(row, key)) for key in keys if _gettr(row, key)]
            )
            if hasattr(row, "UID"):
                inner = (
                    '<a title="%s" href="%s/search?authorsUID:list='
                    "%s&amp;advanced_search:boolean=True&amp;"
                    'use_navigation_root:boolean=True">%s</a>'
                ) % (
                    self.context.translate(_("label_search")),
                    api.portal.get().absolute_url(),
                    row.UID(),
                    inner,
                )
            result += "<li>{}{}</li>".format(
                inner,
                self._get_gnd_link(row.gndId) if getattr(row, "gndId", None) else "",
            )

        return f'<ul class="rows_list">{result}</ul>' if result else ""

    def get_doi_url_if_active(self):
        context = self.context
        try:
            doi_active = context.doiRegistrationActive
        except AttributeError:
            doi_active = False
        # If DOI registration is not active and the object has only the
        # auto-generated DOI, i.e. the user has not supplied their own,
        # then we don't want to show the DOI. See #12126-86
        if not doi_active and context.doi == generateDoi(context):
            return False
        else:
            return f"http://dx.doi.org/{context.doi}"
        return False

    def get_metadata(self):  # noqa: C901
        context = self.context
        meta = {}

        for field in self.metadata_fields:
            value = False  # A field is only displayed if it has a value
            use_widget_view = False
            if field == "get_journal_title":
                label = _("heading_metadata_journal")
                value = IParentGetter(self.context).get_title_from_parent_of_type(
                    "Publication"
                )
            elif field == "metadata_start_end_pages":
                if "metadata_start_end_pages_article" in self.metadata_fields:
                    label = _("metadata_pages_review")
                else:
                    label = _("metadata_pages")
                value = self.page_start_end_in_print
            elif field == "metadata_start_end_pages_article":
                label = _("metadata_pages_article")
                value = self.page_start_end_in_print_article
            elif field == "metadata_review_author":
                label = _("label_metadata_review_author")
                value = self.list_rows(context.reviewAuthors, "lastname", "firstname")
            elif field == "metadata_presentation_author":
                label = _("label_metadata_presentation_author")
                value = self.list_rows(context.reviewAuthors, "lastname", "firstname")
            elif field == "authors":
                label = self.get_label(field)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "editorial":
                label = self.get_label(field)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "editorsCollectedEdition":
                label = self.get_label(field)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "curators":
                label = self.get_label(field)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field in ["exhibiting_institution", "exhibiting_organisation"]:
                label = self.get_label(field)
                value = self.list_rows(getattr(context, field), "name")
            elif field == "metadata_review_type_code":
                label = _("metadata_review_type_code")
                value = context.translate(context.portal_type)
            elif field == "referenceAuthors":
                label = _("label_metadata_reference_authors")
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "institution":
                label = _("label_metadata_institution")
                value = self.list_rows(getattr(context, field), "name")
            elif field == "metadata_recensioID":
                label = _("metadata_recensio_id")
                value = context.UID()
            elif field == "canonical_uri":
                url = context.canonical_uri
                if url:
                    label = self.get_label(field)
                    value = '<a rel="canonical_uri" href="{}" title="{}">{}</a>'.format(
                        url,
                        url,
                        url,
                    )
            elif field in [
                "uri",
                "url_monograph",
                "url_journal",
                "url_article",
                "url_exhibition",
                "urn",
                "urn_monograph",
                "urn_journal",
                "urn_article",
            ]:
                url = getattr(context, field, None)
                if url:
                    label = self.get_label(field)
                    value = f'<a href="{url}" title="{url}">{url}</a>'
            elif field == "doi":
                doi_url = self.get_doi_url_if_active()
                if doi_url:
                    value = '<a rel="doi" href="{}" title="{}">{}</a>'.format(
                        doi_url,
                        doi_url,
                        context.doi,
                    )
                    label = self.get_label(field)
                else:
                    label = None
            elif field in [
                "doi_monograph",
                "doi_journal",
                "doi_article",
                "doi_exhibition",
            ]:
                doi = getattr(context, field, None)
                if doi:
                    doi_url = f"http://dx.doi.org/{doi}"
                    value = '<a rel="doi" href="{}" title="{}">{}</a>'.format(
                        doi_url,
                        doi_url,
                        doi,
                    )
                    label = self.get_label(field)
                else:
                    label = None
            elif field == "title":
                label = self.get_label(field)
                titles = [context.title]
                additional_titles = getattr(context, "additionalTitles", [])
                if additional_titles:
                    titles.extend(
                        [additional["title"] for additional in additional_titles]
                    )
                value = " / ".join(titles)
            elif field == "subtitle":
                if context.subtitle:
                    label = self.get_label(field)
                    subtitles = [context.subtitle]
                    additional_titles = getattr(context, "additionalTitles", [])
                    if additional_titles:
                        subtitles.extend(
                            [
                                additional["subtitle"]
                                for additional in additional_titles
                                if additional["subtitle"]
                            ]
                        )
                    value = " / ".join(subtitles)
            elif field == "dates":
                label = self.get_label(field)
                values = getattr(context, field)
                if getattr(context, "isPermanentExhibition", False):
                    permanent_ex = _("Dauerausstellung")
                    values = [
                        {
                            "place": value["place"],
                            "runtime": " ".join([permanent_ex, value["runtime"]]),
                        }
                        for value in values
                    ]
                value = self.list_rows(values, "place", "runtime")
            elif field == "effective_date":
                effective_date = getattr(context, "effective_date", None)
                if effective_date:
                    label = _("label_metadata_recensio_date")
                    ploneview = api.content.get_view(
                        context=context, request=self.request, name="plone"
                    )
                    value = ploneview.toLocalizedTime(effective_date, long_format=False)
            elif field == "subjects":
                label = self.get_label(field)
                # NOTE: the behavior field is `subjects` but it's stored as
                #       `subject` on the context.
                value = "<br/>".join(getattr(context, "subject", []))
            else:
                if field == "ddcSubject":
                    label = _("Subject classification")
                elif field == "ddcTime":
                    label = _("Time classification")
                elif field == "ddcPlace":
                    label = _("Regional classification")
                else:
                    label = self.get_label(field)
                # The macro is used in the template, the value is
                # used to determine whether to display that row or not
                value = True if getattr(context, field) else False
                use_widget_view = True
            meta[field] = {
                "label": label,
                "value": value,
                "use_widget_view": use_widget_view,
            }
        return meta

    def get_metadata_context_object(self):
        context = self.context

        terms = {}
        introstr = "ctx_ver=Z39.88-2004&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook"

        for field in self.metadata_fields:
            if field in self.openurl_terms:
                name = self.openurl_terms[field]

                if field == "metadata_review_author":
                    terms.update(
                        {
                            name: [
                                f"{au.firstname} {au.lastname}"
                                for au in [au.to_object for au in context.reviewAuthors]
                            ]
                        }
                    )
                elif field == "title":
                    authors = ", ".join(
                        [
                            f"{au.firstname} {au.lastname}"
                            for au in [
                                au.to_object for au in getattr(context, "authors", [])
                            ]
                        ]
                    )
                    terms.update({name: f"{authors}: {getattr(context, field)}"})
                elif field == "pages":
                    value = self.page_start_end_in_print
                    terms.update({name: value})
                elif field == "get_journal_title":
                    value = IParentGetter(self.context).get_title_from_parent_of_type(
                        "Publication"
                    )
                else:
                    value = getattr(context, field)
                    if callable(value):
                        value = value()
                    terms.update({name: value})
        new_terms = {}
        for key, value in terms.items():
            if isinstance(value, list):
                new_value = []
                for inner_value in value:
                    new_value.append(inner_value)
                new_terms[key] = new_value
            else:
                new_terms[key] = value
        return introstr + "&" + make_query(new_terms)

    def get_online_review_urls(self):
        existing_online_review_urls = getattr(
            self.context, "existingOnlineReviews", None
        )
        if existing_online_review_urls and existing_online_review_urls != (
            {"name": "", "url": ""},
        ):
            existing_online_review_urls = [
                url
                for url in existing_online_review_urls
                if url["name"].strip() != "" and url["url"].strip() != ""
            ]
        return existing_online_review_urls

    def get_published_reviews(self):
        published_reviews = getattr(self.context, "publishedReviews", [])
        if published_reviews:
            if published_reviews != ({"details": ""},):
                published_reviews = [
                    review
                    for review in published_reviews
                    if review["details"].strip() != ""
                ]
        return published_reviews

    def cover_picture_url(self):
        """Return cover picture or first page."""
        coverPicture = getattr(self.context, "coverPicture", None)
        if coverPicture:
            return f"{self.context.absolute_url()}/coverPicture"
        return None

    @property
    def do_visit_canonical_uri(self):
        url = getattr(self.context, "canonical_uri", "") or ""
        return "www.perspectivia.net/content/publikationen/francia" in url

    def show_dara_update(self):
        sm = getSecurityManager()
        if not sm.checkPermission("Manage portal", self.context):
            return False
        try:
            return self.context.doiRegistrationActive
        except AttributeError:
            return False

    def get_citation_string(self):
        raise NotImplementedError("specific to subtypes; implement in specific views")

    def is_url_shown_in_citation_note(self):
        is_external_fulltext = getattr(
            self.context, "isUseExternalFulltext", lambda: False
        )()
        is_url_shown_via_review = getattr(
            self.context, "isURLShownInCitationNote", lambda: True
        )()
        return not is_external_fulltext and is_url_shown_via_review

    def isUseExternalFulltext(self):
        return IParentGetter(self.context).get_flag_with_override(
            "useExternalFulltext", True
        )

    def get_review_pdf(self):
        """Return the uploaded pdf if that doesn't exist return the
        generatedPdf Blob object otherwise return None.

        Also return the size since it is not easy to get this from the
        blob directly
        """
        review_pdf = None

        uploaded_pdf = getattr(self.context, "pdf", None)
        if uploaded_pdf and uploaded_pdf.size > 0:
            review_pdf = uploaded_pdf

        if not review_pdf:
            generated_pdf = getattr(self.context, "generatedPdf", None)
            if generated_pdf and generated_pdf.size > 0:
                review_pdf = generated_pdf

        return review_pdf

    def getLicense(self):
        # XXX It might need some tweaks if we port the presentations
        publication = IParentGetter(self.context).get_parent_object_of_type(
            "Publication"
        )
        publication_licence = ""
        current = self.context
        if publication is not None:
            while current != publication.aq_parent:
                licence_obj = getattr(current, "licence_ref", None)
                if licence_obj:
                    licence_obj = licence_obj.to_object
                if licence_obj:
                    licence_translated = licence_obj
                    # TODO
                    # licence_translated = licence_obj.getTranslation()
                    publication_licence = licence_translated.text or ""
                    if publication_licence:
                        publication_licence = publication_licence.output_relative_to(
                            licence_translated
                        )
                else:
                    publication_licence = getattr(current.aq_base, "licence", "")
                if publication_licence:
                    break
                current = current.aq_parent
        return True and publication_licence or _("license-note-review")

    def getUUIDUrl(self):
        base_url = api.portal.get().absolute_url()
        if base_url.startswith("http://www."):
            base_url = base_url.replace("http://www.", "http://")
        base_url += "/r/"
        base_url += self.context.UID()
        return f'<a href="{base_url}">{base_url}</a>'

    def isDoiRegistrationActive(self):
        # TODO
        return False

    def get_citation_location(self):
        location = []
        doi_active = self.isDoiRegistrationActive()
        # If DOI registration is not active and the object has only the
        # auto-generated DOI, i.e. the user has not supplied their own,
        # then we don't want to show the DOI. See #12126-86
        has_doi = doi_active or self.context.doi != generateDoi(self.context)
        has_canonical_uri = getattr(self.context, "canonical_uri", False)
        if has_doi:
            doi = self.context.doi
            location.append(f'DOI: <a href="http://dx.doi.org/{doi}">{doi}</a>')
        if has_canonical_uri and not self.isUseExternalFulltext():  # 3102 #REC-984
            location.append(
                api.portal.translate(
                    _(
                        "label_downloaded_via_recensio",
                        mapping={"portal": api.portal.get().Title()},
                    )
                )
            )
        if not has_canonical_uri and not has_doi:
            location.append(self.getUUIDUrl())

        return ", ".join(location)

    @property
    def page_start_end_in_print(self):
        """See #2630 PAJ/PAEV/RJ/RM have page start and end fields."""

        page_start = getattr(
            self.context,
            "pageStartOfPresentedTextInPrint",
            getattr(self.context, "pageStartOfReviewInJournal", ""),
        )

        page_end = getattr(
            self.context,
            "pageEndOfPresentedTextInPrint",
            getattr(self.context, "pageEndOfReviewInJournal", ""),
        )
        return self.format_page_start_end(page_start, page_end)

    @property
    def page_start_end_in_print_article(self):
        page_start = getattr(self.context, "pageStartOfArticle", "")
        page_end = getattr(self.context, "pageEndOfArticle", "")
        return self.format_page_start_end(page_start, page_end)

    def format_page_start_end(self, page_start, page_end):
        # page_start is set to 0 when it is left empty in the bulk
        # import spreadsheet #4054
        if page_start in (None, 0):
            page_start = ""
        page_start = str(page_start).strip()

        # page_end is set to 0 when it is left empty in the bulk
        # import spreadsheet #4054
        if page_end in (None, 0):
            page_end = ""
        page_end = str(page_end).strip()

        if page_start == page_end:
            # both the same/empty
            page_start_end = page_start
        elif page_start and page_end:
            page_start_end = f"{page_start}-{page_end}"
        else:
            # one is not empty
            page_start_end = page_start or page_end
        return page_start_end

    def __call__(self):
        canonical_url = self.get_canonical_url()
        if (
            not self.request["HTTP_HOST"].startswith("admin.")
            and canonical_url != self.request["ACTUAL_URL"]
        ):
            return self.request.response.redirect(canonical_url, status=301)
        return super().__call__()


class ReviewArticleCollectionView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "get_journal_title",
        "metadata_start_end_pages",
        "metadata_review_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "title",
        "subtitle",
        "translatedTitle",
        "metadata_start_end_pages_article",
        "editorial",
        "titleEditedVolume",
        "subtitleEditedVolume",
        "translatedTitleEditedVolume",
        "yearOfPublication",
        "placeOfPublication",
        "publisher",
        "yearOfPublicationOnline",
        "placeOfPublicationOnline",
        "publisherOnline",
        "series",
        "seriesVol",
        "pages",
        "isbn",
        "isbn_online",
        "url_monograph",
        "urn_monograph",
        "doi_monograph",
        "url_article",
        "urn_article",
        "doi_article",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "canonical_uri",
        "urn",
        "effective_date",
        "metadata_recensioID",
        "idBvb",
        "doi",
    ]

    def formatted_authors(self):
        # TODO This is here as a hint for the one implementing citations.
        # Please remove this method and use IAuthors instead.
        authors_str = IAuthors(self.context).get_formatted_authors()
        return authors_str

    def getDecoratedTitle(self):
        args = {
            "(Hg.)": api.portal.translate(_("label_abbrev_editor", default="(Hg.)")),
            "in": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }

        authors_string = self.formatted_authors()

        reviewer_string = IBase(self.context).get_formatted_review_authors()
        editors_string = get_formatted_names(
            [rel.to_object for rel in self.context.editorial]
        )

        edited_volume = getFormatter(
            f" {args['(Hg.)']}{args[':']} ", ". ", " ", f", {args['page']} "
        )
        translated_title = self.context.translatedTitleEditedVolume
        if translated_title:
            translated_title = f"[{translated_title}]"
        edited_volume_string = edited_volume(
            editors_string,
            self.context.titleEditedVolume,
            self.context.subtitleEditedVolume,
            translated_title,
            self.page_start_end_in_print_article,
        )

        full_citation = getFormatter(": ", ", in: ", " ")
        return full_citation(
            authors_string,
            punctuated_title_and_subtitle(self.context),
            edited_volume_string,
            reviewer_string,
        )

    def get_citation_string(self):
        if self.context.customCitation:
            return scrubHTML(self.context.customCitation)

        args = {
            "(Hg.)": api.portal.translate(_("label_abbrev_editor", default="(Hg.)")),
            "review_of": api.portal.translate(
                _("text_review_of", default="review of:")
            ),
            "review_in": api.portal.translate(
                _("text_review_in", default="review published in:")
            ),
            "in": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }
        rev_details_formatter = getFormatter(
            ", ", ", %(in)s " % args, ", %(page)s " % args
        )
        reviewer_string = get_formatted_names(
            [rel.to_object for rel in self.context.reviewAuthors], lastname_first=True
        )
        authors_string = self.formatted_authors()
        editors_string = get_formatted_names(
            [rel.to_object for rel in self.context.editorial]
        )
        edited_volume = getFormatter(
            f" {args['(Hg.)']}{args[':']} ", ". ", ", ", f"{args[':']} ", ", "
        )
        edited_volume_string = edited_volume(
            editors_string,
            self.context.titleEditedVolume,
            self.context.subtitleEditedVolume,
            self.context.placeOfPublication,
            self.context.publisher,
            self.context.yearOfPublication,
        )
        title_subtitle_string = punctuated_title_and_subtitle(self.context)
        item_string = rev_details_formatter(
            authors_string,
            title_subtitle_string,
            edited_volume_string,
            self.page_start_end_in_print_article,
        )

        mag_number_formatter = getFormatter(", ", ", ")
        mag_number_string = mag_number_formatter(
            IParentGetter(self.context).get_title_from_parent_of_type("Publication"),
            IParentGetter(self.context).get_title_from_parent_of_type("Volume"),
            IParentGetter(self.context).get_title_from_parent_of_type("Issue"),
        )

        location = self.get_citation_location()

        citation_formatter = getFormatter(
            "%(:)s %(review_of)s " % args,
            ", %(review_in)s " % args,
            ", %(page)s " % args,
            ", ",
        )

        citation_string = citation_formatter(
            escape(reviewer_string),
            escape(item_string),
            escape(mag_number_string),
            self.page_start_end_in_print,
            location,
        )

        return citation_string


class ReviewArticleJournalView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "get_journal_title",
        "metadata_start_end_pages",
        "metadata_review_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "title",
        "subtitle",
        "translatedTitle",
        "metadata_start_end_pages_article",
        "editor",
        "titleJournal",
        "translatedTitleJournal",
        "shortnameJournal",
        "yearOfPublication",
        "officialYearOfPublication",
        "volumeNumber",
        "issueNumber",
        "placeOfPublication",
        "yearOfPublicationOnline",
        "placeOfPublicationOnline",
        "publisherOnline",
        "publisher",
        "issn",
        "issn_online",
        "url_journal",
        "urn_journal",
        "doi_journal",
        "url_article",
        "urn_article",
        "doi_article",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "canonical_uri",
        "urn",
        "effective_date",
        "metadata_recensioID",
        "idBvb",
        "doi",
    ]

    def formatted_authors_editorial(self):
        authors_str = IAuthors(self.context).get_formatted_authors()
        editorial_apadter = IEditorial(self.context, None)
        if editorial_apadter:
            editors_str = IEditorial(self.context, None).get_formatted_editorial()
        else:
            editors_str = ""
        return getFormatter(": ")(editors_str, authors_str)

    def getDecoratedTitle(self):
        args = {
            "in:": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }

        item = getFormatter(" ", ", ", " ", ", ", f", {args['page']} ")
        mag_year = getFormatter("/")(
            self.context.officialYearOfPublication, self.context.yearOfPublication
        )
        mag_year = f"({mag_year})" if mag_year else None
        translated_title_journal = self.context.translatedTitleJournal
        if translated_title_journal:
            translated_title_journal = f"[{translated_title_journal}]"
        item_string = item(
            self.context.titleJournal,
            translated_title_journal,
            self.context.volumeNumber,
            mag_year,
            self.context.issueNumber,
            self.page_start_end_in_print_article,
        )

        authors_string = self.formatted_authors_editorial()
        reviewer_string = IBase(self.context).get_formatted_review_authors()

        full_citation = getFormatter(": ", f", {args['in:']} ", " ")
        return full_citation(
            authors_string,
            punctuated_title_and_subtitle(self.context),
            item_string,
            reviewer_string,
        )

    def get_citation_string(self):
        if self.context.customCitation:
            return scrubHTML(self.context.customCitation)

        args = {
            "review_of": api.portal.translate(
                _("text_review_of", default="review of:")
            ),
            "review_in": api.portal.translate(
                _("text_review_in", default="Review published in:")
            ),
            "in:": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }
        rev_details_formatter = getFormatter(
            "%(:)s " % args,
            ", %(in:)s " % args,
            ", ",
            " ",
            ", ",
            ", %(page)s " % args,
        )
        mag_year = getFormatter("/")(
            self.context.officialYearOfPublication, self.context.yearOfPublication
        )
        mag_year = "(" + mag_year + ")" if mag_year else None
        item_string = rev_details_formatter(
            IAuthors(self.context).get_formatted_authors(),
            punctuated_title_and_subtitle(self.context),
            self.context.titleJournal,
            self.context.volumeNumber,
            mag_year,
            self.context.issueNumber,
            self.page_start_end_in_print_article,
        )

        reference_mag = getFormatter(", ", ", ")
        reference_mag_string = reference_mag(
            IParentGetter(self.context).get_title_from_parent_of_type("Publication"),
            IParentGetter(self.context).get_title_from_parent_of_type("Volume"),
            IParentGetter(self.context).get_title_from_parent_of_type("Issue"),
        )

        location = self.get_citation_location()

        rezensent_string = get_formatted_names(
            [rel.to_object for rel in self.context.reviewAuthors], lastname_first=True
        )
        citation_formatter = getFormatter(
            "%(:)s %(review_of)s " % args,
            ", %(review_in)s " % args,
            ", %(page)s " % args,
            ", ",
        )
        citation_string = citation_formatter(
            escape(rezensent_string),
            escape(item_string),
            escape(reference_mag_string),
            self.page_start_end_in_print,
            location,
        )
        return citation_string


class ReviewExhibitionView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "get_journal_title",
        "metadata_start_end_pages",
        "metadata_review_author",
        "languageReview",
        "languageReviewedText",
        "exhibiting_institution",
        "exhibiting_organisation",
        "curators",
        "titleProxy",
        "subtitle",
        "dates",
        "url_exhibition",
        "doi_exhibition",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "canonical_uri",
        "urn",
        "effective_date",
        "metadata_recensioID",
        "doi",
    ]

    @property
    def exhibitor(self):
        exhibitor = " / ".join(
            [
                institution["name"].strip()
                for institution in self.context.exhibiting_institution
                if institution["name"]
            ]
        )
        if exhibitor:
            return exhibitor
        exhibitor = " / ".join(
            [
                organisation["name"].strip()
                for organisation in self.context.exhibiting_organisation
                if organisation["name"]
            ]
        )
        if exhibitor:
            return exhibitor
        exhibitor = get_formatted_names(
            [
                person.to_object
                for person in self.context.curators
                if person.firstname or person.lastname
            ],
        )
        return exhibitor

    def getDecoratedTitle(self):
        dates_formatter = getFormatter(", ")
        dates_string = " / ".join(
            [
                dates_formatter(date["place"], date["runtime"])
                for date in self.context.dates
            ]
        )

        permanent_exhib_string = api.portal.translate(
            _("Dauerausstellung", default="Permanent Exhibition")
        )
        title_string = getFormatter(". ")(
            punctuated_title_and_subtitle(self.context),
            permanent_exhib_string if self.context.isPermanentExhibition else "",
        )

        full_title = getFormatter(": ", ", ", " ")

        def message_callback(reviewers_formatted):
            return _(
                "exhibition_reviewed_by",
                default="Exhibition reviewed by ${review_authors}",
                mapping={"review_authors": reviewers_formatted},
            )

        reviewer_string = IBase(self.context).get_formatted_review_authors(
            message_callback=message_callback
        )
        return full_title(
            self.exhibitor,
            title_string,
            dates_string,
            reviewer_string,
        )

    def get_citation_string(self):
        if self.context.customCitation:
            return scrubHTML(self.context.customCitation)

        args = {
            "review_of": api.portal.translate(
                _("text_review_of", default="review of:")
            ),
            "in": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }
        rev_details_formatter = getFormatter("%(:)s " % args, ", ", " ")
        rezensent_string = get_formatted_names(
            [rel.to_object for rel in self.context.reviewAuthors], lastname_first=True
        )

        dates_formatter = getFormatter(", ")
        dates_string = " / ".join(
            [
                dates_formatter(
                    date["place"],
                    date["runtime"],
                )
                for date in self.context.dates
            ]
        )
        permanent_exhib_string = api.portal.translate(
            _("Dauerausstellung", default="Dauerausstellung")
        )
        title_string = getFormatter(". ")(
            punctuated_title_and_subtitle(self.context),
            permanent_exhib_string if self.context.isPermanentExhibition else "",
        )
        item_string = rev_details_formatter(
            self.exhibitor,
            title_string,
            dates_string,
        )

        mag_number_formatter = getFormatter(", ", ", ")
        mag_number_string = mag_number_formatter(
            IParentGetter(self.context).get_title_from_parent_of_type("Publication"),
            IParentGetter(self.context).get_title_from_parent_of_type("Volume"),
            IParentGetter(self.context).get_title_from_parent_of_type("Issue"),
        )

        location = self.get_citation_location()

        citation_formatter = getFormatter(
            "%(:)s %(review_of)s " % args,
            ", %(in)s " % args,
            ", %(page)s " % args,
            ", ",
        )

        citation_string = citation_formatter(
            escape(rezensent_string),
            escape(item_string),
            escape(mag_number_string),
            self.page_start_end_in_print,
            location,
        )

        return citation_string


class ReviewJournalView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "get_journal_title",
        "metadata_start_end_pages",
        "metadata_review_author",
        "languageReview",
        "languageReviewedText",
        "editor",
        "title",
        "translatedTitleJournal",
        "shortnameJournal",
        "yearOfPublication",
        "officialYearOfPublication",
        "volumeNumber",
        "issueNumber",
        "placeOfPublication",
        "publisher",
        "yearOfPublicationOnline",
        "placeOfPublicationOnline",
        "publisherOnline",
        "issn",
        "issn_online",
        "url_journal",
        "urn_journal",
        "doi_journal",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "canonical_uri",
        "urn",
        "effective_date",
        "metadata_recensioID",
        "idBvb",
        "doi",
    ]

    def getDecoratedTitle(self):
        item = getFormatter(" ", ", ", " ", ", ")
        mag_year = getFormatter("/")(
            self.context.officialYearOfPublication, self.context.yearOfPublication
        )
        mag_year = f"({mag_year})" if mag_year else None
        translated_title = self.context.translatedTitleJournal
        if translated_title:
            translated_title = f"[{translated_title}]"
        item_string = item(
            self.context.title,
            translated_title,
            self.context.volumeNumber,
            mag_year,
            self.context.issueNumber,
        )

        reviewer_string = IBase(self.context).get_formatted_review_authors()

        return " ".join((item_string, reviewer_string))

    def get_citation_string(self):
        if self.context.customCitation:
            return scrubHTML(self.context.customCitation)

        rev_details_formatter = getFormatter(", ", ", ", " ")
        mag_year = getFormatter("/")(
            self.context.officialYearOfPublication, self.context.yearOfPublication
        )
        mag_year = f"({mag_year})" if mag_year else None
        item_string = rev_details_formatter(
            self.context.title,
            self.context.volumeNumber,
            self.context.issueNumber,
            mag_year,
        )

        reference_mag = getFormatter(", ", ", ")
        reference_mag_string = reference_mag(
            IParentGetter(self.context).get_title_from_parent_of_type("Publication"),
            IParentGetter(self.context).get_title_from_parent_of_type("Volume"),
            IParentGetter(self.context).get_title_from_parent_of_type("Issue"),
        )

        location = self.get_citation_location()

        reviewer_string = get_formatted_names(
            [rel.to_object for rel in self.context.reviewAuthors], lastname_first=True
        )
        args = {
            "review_of": api.portal.translate(
                _("text_review_of", default="review of:")
            ),
            "in": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }
        citation_formatter = getFormatter(
            "%(:)s %(review_of)s " % args,
            ", %(in)s " % args,
            ", %(page)s " % args,
            ", ",
        )
        citation_string = citation_formatter(
            escape(reviewer_string),
            escape(item_string),
            escape(reference_mag_string),
            self.page_start_end_in_print,
            location,
        )
        return citation_string


class ReviewMonographView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "get_journal_title",
        "metadata_start_end_pages",
        "metadata_review_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "editorial",
        "title",
        "subtitle",
        "translatedTitle",
        "yearOfPublication",
        "placeOfPublication",
        "publisher",
        "yearOfPublicationOnline",
        "placeOfPublicationOnline",
        "publisherOnline",
        "series",
        "seriesVol",
        "pages",
        "isbn",
        "isbn_online",
        "url_monograph",
        "urn_monograph",
        "doi_monograph",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "canonical_uri",
        "urn",
        "effective_date",
        "metadata_recensioID",
        "idBvb",
        "doi",
    ]

    def formatted_authors_editorial(self):
        authors_str = IAuthors(self.context).get_formatted_authors()
        editors_str = IEditorial(self.context).get_formatted_editorial()
        return getFormatter(": ")(editors_str, authors_str)

    def getDecoratedTitle(self):
        """Original Spec:

            [Werkautor Vorname] [Werkautor Nachname]: [Werktitel]. [Werk-Untertitel]
            (reviewed by [Rezensent Vorname] [Rezensent Nachname])

        Analog, Werkautoren kann es mehrere geben (Siehe Citation)

        Hans Meier: Geschichte des Abendlandes. Ein Abriss (reviewed by Klaus Müller)
        """
        authors_string = self.formatted_authors_editorial()

        reviewer_string = IBase(self.context).get_formatted_review_authors()

        full_citation = getFormatter(": ", " ")
        return full_citation(
            authors_string, punctuated_title_and_subtitle(self.context), reviewer_string
        )

    def get_citation_string(self):
        if self.context.customCitation:
            return scrubHTML(self.context.customCitation)

        args = {
            "review_of": api.portal.translate(
                _("text_review_of", default="review of:")
            ),
            "in": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }
        rev_details_formatter = getFormatter(", ", ", ", "%(:)s " % args, ", ")
        reviewer_string = get_formatted_names(
            [rel.to_object for rel in self.context.reviewAuthors], lastname_first=True
        )
        authors_string = self.formatted_authors_editorial()
        title_subtitle_string = punctuated_title_and_subtitle(self.context)
        item_string = rev_details_formatter(
            authors_string,
            title_subtitle_string,
            self.context.placeOfPublication,
            self.context.publisher,
            self.context.yearOfPublication,
        )

        mag_number_formatter = getFormatter(", ", ", ")
        mag_number_string = mag_number_formatter(
            IParentGetter(self.context).get_title_from_parent_of_type("Publication"),
            IParentGetter(self.context).get_title_from_parent_of_type("Volume"),
            IParentGetter(self.context).get_title_from_parent_of_type("Issue"),
        )

        location = self.get_citation_location()

        citation_formatter = getFormatter(
            "%(:)s %(review_of)s " % args,
            ", %(in)s " % args,
            ", %(page)s " % args,
            ", ",
        )

        citation_string = citation_formatter(
            escape(reviewer_string),
            escape(item_string),
            escape(mag_number_string),
            self.page_start_end_in_print,
            location,
        )

        return citation_string


class PresentationArticleReviewView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "title",
        "subtitle",
        "titleJournal",
        "shortnameJournal",
        "yearOfPublication",
        "officialYearOfPublication",
        "volumeNumber",
        "issueNumber",
        "metadata_start_end_pages",
        "placeOfPublication",
        "publisher",
        "issn",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "uri",
        "urn",
        "metadata_recensioID",
        "idBvb",
    ]


class PresentationCollectionView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReviewedText",
        "languageReview",
        "authors",
        "title",
        "subtitle",
        "metadata_start_end_pages",
        "editorsCollectedEdition",
        "titleCollectedEdition",
        "yearOfPublication",
        "placeOfPublication",
        "publisher",
        "series",
        "seriesVol",
        "pages",
        "isbn",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "uri",
        "urn",
        "metadata_recensioID",
        "idBvb",
    ]


class PresentationMonographView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "editorial",
        "title",
        "subtitle",
        "yearOfPublication",
        "placeOfPublication",
        "publisher",
        "series",
        "seriesVol",
        "pages",
        "isbn",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "urn",
        "metadata_recensioID",
        "idBvb",
    ]


class PresentationOnlineResourceView(View):
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReview",
        "title",
        "uri",
        "urn",
        "institution",
        "languageReviewedText",
        "documenttypes_institution",
        "documenttypes_cooperation",
        "documenttypes_referenceworks",
        "documenttypes_bibliographical",
        "documenttypes_fulltexts",
        "documenttypes_periodicals",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subjects",
        "metadata_recensioID",
    ]
