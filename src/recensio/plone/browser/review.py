from AccessControl.SecurityManagement import getSecurityManager
from html import escape
from plone import api
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from recensio.plone import _
from recensio.plone.mails.legacy import get_formatted_names
from ZTUtils import make_query


class View(BrowserView):
    """Moderation View."""

    metadata_fields = []  # XXX
    ordered_fields = []  # XXX
    custom_metadata_field_labels = {
        "get_publication_title": _("Publication Title"),
        "get_journal_title": _("heading_metadata_journal"),
        "get_volume_title": _("Volume Title"),
        "get_issue_title": _("Issue Title"),
    }

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

    def get_canonical_url(self):
        """XXX.

        registry = getUtility(IRegistry)
        recensio_settings = registry.forInterface(IRecensioSettings, prefix="recensio.plone.settings")
        virtual_url = self.request.get("VIRTUAL_URL_PARTS", [])
        if virtual_url and virtual_url[0] != recensio_settings.external_portal_url:
            canonical_url = "/".join(
                (
                    recensio_settings.external_portal_url,
                    "/".join(self.context.getPhysicalPath()[2:]),
                )
            )
            return canonical_url
        else:
            return self.request["ACTUAL_URL"]
        """
        return self.context.absolute_url()  # XXX user the code above

    def get_metadata_review_author(self):
        return get_formatted_names(
            " <br/> ", ", ", self.context.reviewAuthors, lastname_first=True
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
        rows = [row for row in rows if any([row[key] for key in keys])]
        if rows:
            rows_ul = "<ul class='rows_list'>"
            for row in rows:
                inner = ", ".join(
                    [safe_unicode(escape(row[key])) for key in keys if row[key]]
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
                rows_ul += "<li>{}{}</li>".format(
                    inner,
                    self._get_gnd_link(row.getGndId())
                    if getattr(row, "gndId", None)
                    else "",
                )
            rows_ul += "</ul>"
            return rows_ul
        else:
            return ""

    def get_label(self, fields, field, meta_type):  # noqa: C901
        """Return the metadata label for a field of a particular
        portal_type."""

        if field == "officialYearOfPublication":
            return _(
                "label_metadata_official_year_of_publication",
                default="Official year of publication",
            )

        if meta_type.startswith("Review"):
            if field == "languageReview":
                return _("label_metadata_language_review", default="Language (review)")
        elif meta_type.startswith("Presentation"):
            if field == "languageReview":
                return _(
                    "label_metadata_language_presentation",
                    default="Language (presentation)",
                )
        if meta_type in ["ReviewMonograph", "PresentationMonograph"]:
            if field == "languageReviewedText":
                return _(
                    "label_metadata_language_monograph",
                    default="Language (monograph)",
                )
            if field == "authors":
                return _("Author (monograph)", default="Author (monograph)")
            if field == "editorial":
                return _("Editor (monograph)", default="Editor (monograph)")
        elif meta_type in ["PresentationArticleReview", "PresentationCollection"]:
            if field == "languageReviewedText":
                return _(
                    "label_metadata_language_article", default="Language (article)"
                )
            if field == "authors":
                return _("label_metadata_author_article", default="Author (article)")
            if field == "editorial":
                return _("label_metadata_editor_article", default="Editor (article)")
            if field == "title":
                return _("label_metadata_title_article", default="Title (article)")
            if field == "titleCollectedEdition":
                return _(
                    "label_metadata_title_edited_volume",
                    default="Title (edited volume)",
                )
        elif meta_type == "PresentationOnlineResource":
            if field == "title":
                return _(
                    "label_metadata_name_resource", default="Name (Internet resource)"
                )
            if field == "languageReviewedText":
                return _(
                    "label_metadata_language_internet_resource",
                    default="Language (Internet resource)",
                )
        elif meta_type == "ReviewJournal":
            if field == "languageReviewedText":
                return _(
                    "label_metadata_language_review_journal",
                    default="Language (Journal)",
                )
            if field == "editor":
                return _("label_metadata_editor", default="Editor")
        elif meta_type.startswith("ReviewArticle"):
            if field == "languageReviewedText":
                return _("label_metadata_language_article", default="Sprache (Aufsatz)")
            elif field == "authors":
                return _("label_metadata_authors_article", default="Autor (Aufsatz)")
            elif field in ["editor", "editorial"]:
                if meta_type == "ReviewArticleCollection":
                    return _(
                        "label_metadata_editor_edited_volume",
                        default="Editor (edited volume)",
                    )
                elif meta_type == "ReviewArticleJournal":
                    return _(
                        "label_metadata_editor_journal", default="Editor (journal)"
                    )
            elif field == "title":
                return _("label_metadata_title_article", default="Title (article)")
            elif field == "subtitle":
                return _(
                    "label_metadata_subtitle_article",
                    default="Subtitle (Article)",
                )
            elif field == "titleEditedVolume":
                return _(
                    "label_metadata_title_edited_volume",
                    default="Title (edited volume)",
                )
            elif field == "subtitleEditedVolume":
                return _(
                    "label_metadata_subtitle_edited_volume",
                    default="Subtitle (edited volume)",
                )
            elif field == "metadata_start_end_pages":
                return _("metadata_pages_review", default="Pages (review)")
            elif field == "translatedTitle":
                return _(
                    "label_metadata_translated_title_article",
                    default="Übersetzter Titel (Aufsatz)",
                )
            elif field == "url_monograph":
                return _(
                    "label_metadata_url_edited_volume",
                    default="URL (Sammelband)",
                )
            elif field == "urn_monograph":
                return _(
                    "label_metadata_urn_edited_volume",
                    default="URN (Sammelband)",
                )
            elif field == "doi_monograph":
                return _(
                    "label_metadata_doi_edited_volume",
                    default="DOI (Sammelband)",
                )

        return _(fields[field].widget.label)

    def get_doi_url_if_active(self):
        context = self.context
        try:
            doi_active = self.context.isDoiRegistrationActive()
        except AttributeError:
            doi_active = False
        # If DOI registration is not active and the object has only the
        # auto-generated DOI, i.e. the user has not supplied their own,
        # then we don't want to show the DOI. See #12126-86
        if not doi_active and context.getDoi() == context.generateDoi():
            return False
        else:
            return f"http://dx.doi.org/{context.getDoi()}"
        return False

    def get_metadata(self):  # noqa: C901
        context = self.context
        meta = {}
        fields = []  # XXX
        for field in self.metadata_fields:
            value = False  # A field is only displayed if it has a value
            is_macro = False
            if field.startswith("get_"):
                label = self.custom_metadata_field_labels[field]
                value = getattr(context, field)()
            elif field == "metadata_start_end_pages":
                if "metadata_start_end_pages_article" in self.metadata_fields:
                    label = _("metadata_pages_review")
                else:
                    label = _("metadata_pages")
                value = context.page_start_end_in_print
            elif field == "metadata_start_end_pages_article":
                label = _("metadata_pages_article")
                value = context.page_start_end_in_print_article
            elif field == "metadata_review_author":
                label = _("label_metadata_review_author")
                value = self.list_rows(context.reviewAuthors, "lastname", "firstname")
            elif field == "metadata_presentation_author":
                label = _("label_metadata_presentation_author")
                value = self.list_rows(context.reviewAuthors, "lastname", "firstname")
            elif field == "authors":
                label = self.get_label(fields, field, context.meta_type)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "editorial":
                label = self.get_label(fields, field, context.meta_type)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "editorsCollectedEdition":
                label = self.get_label(fields, field, context.meta_type)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field == "curators":
                label = self.get_label(fields, field, context.meta_type)
                value = self.list_rows(getattr(context, field), "lastname", "firstname")
            elif field in ["exhibiting_institution", "exhibiting_organisation"]:
                label = self.get_label(fields, field, context.meta_type)
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
                    label = self.get_label(fields, field, context.meta_type)
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
                    label = self.get_label(fields, field, context.meta_type)
                    value = f'<a href="{url}" title="{url}">{url}</a>'
            elif field == "doi":
                doi_url = self.get_doi_url_if_active()
                if doi_url:
                    value = '<a rel="doi" href="{}" title="{}">{}</a>'.format(
                        doi_url,
                        doi_url,
                        context.getDoi(),
                    )
                    label = self.get_label(fields, field, context.meta_type)
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
                    label = self.get_label(fields, field, context.meta_type)
                else:
                    label = None
            elif field == "title":
                label = self.get_label(fields, field, context.meta_type)
                titles = [context.title]
                if "additionalTitles" in context.schema:
                    titles.extend(
                        [
                            additional["title"]
                            for additional in context.getAdditionalTitles()
                        ]
                    )
                value = " / ".join(titles)
            elif field == "subtitle":
                label = self.get_label(fields, field, context.meta_type)
                subtitles = [context.subtitle]
                if "additionalTitles" in context.schema:
                    subtitles.extend(
                        [
                            additional["subtitle"]
                            for additional in context.getAdditionalTitles()
                            if additional["subtitle"]
                        ]
                    )
                value = " / ".join(subtitles)
            elif field == "dates":
                label = self.get_label(fields, field, context.meta_type)
                values = getattr(context, field)
                if context.isPermanentExhibition:
                    permanent_ex = _("Dauerausstellung").encode("utf-8")
                    values = [
                        {
                            "place": value["place"],
                            "runtime": " ".join([permanent_ex, value["runtime"]]),
                        }
                        for value in values
                    ]
                value = self.list_rows(values, "place", "runtime")
            elif field == "effectiveDate":
                label = _("label_metadata_recensio_date")
                ploneview = api.content.get_view(
                    context=context, request=self.request, name="plone"
                )
                value = ploneview.toLocalizedTime(context[field], long_format=False)
            else:
                if field == "ddcSubject":
                    label = _("Subject classification")
                elif field == "ddcTime":
                    label = _("Time classification")
                elif field == "ddcPlace":
                    label = _("Regional classification")
                else:
                    label = self.get_label(fields, field, context.meta_type)
                # The macro is used in the template, the value is
                # used to determine whether to display that row or not
                value = getattr(context, field) and True or False
                is_macro = True
            meta[field] = {"label": label, "value": value, "is_macro": is_macro}
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
                                "{} {}".format(au["firstname"], au["lastname"])
                                for au in context.reviewAuthors
                            ]
                        }
                    )
                elif field == "title":
                    authors = ", ".join(
                        [
                            "{} {}".format(au["firstname"], au["lastname"])
                            for au in getattr(context, "authors", [])
                        ]
                    )
                    terms.update({name: f"{authors}: {getattr(context, field)}"})
                elif field == "pages":
                    value = self.context.page_start_end_in_print
                    terms.update({name: value})
                else:
                    value = getattr(context, field)
                    if callable(value):
                        value = value()
                    terms.update({name: value})
        new_terms = {}
        for key, value in terms.items():
            if isinstance(value, unicode):
                new_terms[key] = value.encode("utf-8")
            elif isinstance(value, list):
                new_value = []
                for inner_value in value:
                    if isinstance(inner_value, unicode):
                        new_value.append(inner_value.encode("utf-8"))
                    else:
                        new_value.append(inner_value)
                new_terms[key] = new_value
            else:
                new_terms[key] = value
        return introstr + "&" + make_query(new_terms)

    def get_online_review_urls(self):
        existing_online_review_urls = []
        if "existingOnlineReviews" in self.ordered_fields:
            existingOnlineReviewUrls = self.context.getExistingOnlineReviews()
            if existingOnlineReviewUrls != () and existingOnlineReviewUrls != (
                {"name": "", "url": ""},
            ):
                existing_online_review_urls = [
                    url
                    for url in existingOnlineReviewUrls
                    if url["name"].strip() != "" and url["url"].strip() != ""
                ]
        return existing_online_review_urls

    def get_published_reviews(self):
        published_reviews = []
        if "publishedReviews" in self.ordered_fields:
            publishedReviews = self.context.getPublishedReviews()
            if publishedReviews != () and publishedReviews != ({"details": ""},):
                published_reviews = [
                    review
                    for review in publishedReviews
                    if review["details"].strip() != ""
                ]
        return published_reviews

    def get_preview_img_url(self):
        """Return cover picture or first page."""
        coverPicture = getattr(self.context, "coverPicture", None)
        if coverPicture:
            target = "coverPicture"
        else:
            target = "get_page_image?no:int=1"
        return f"{self.context.absolute_url()}/{target}"

    @property
    def do_visit_canonical_uri(self):
        url = getattr(self.context, "canonical_uri", "") or ""
        return "www.perspectivia.net/content/publikationen/francia" in url

    def show_dara_update(self):
        sm = getSecurityManager()
        if not sm.checkPermission("Manage portal", self.context):
            return False
        try:
            return self.context.isDoiRegistrationActive()
        except AttributeError:
            return False

    def is_url_shown_in_citation_note(self):
        is_external_fulltext = getattr(
            self.context, "isUseExternalFulltext", lambda: False
        )()
        is_url_shown_via_review = getattr(
            self.context, "isURLShownInCitationNote", lambda: True
        )()
        return not is_external_fulltext and is_url_shown_via_review

    def isUseExternalFulltext(self):
        """XXX: needs a migration and the IParentGetter to be ported."""
        return False

    def get_review_pdf(self):
        """XXX."""

    def __call__(self):
        canonical_url = self.get_canonical_url()
        if (
            not self.request["HTTP_HOST"].startswith("admin.")
            and canonical_url != self.request["ACTUAL_URL"]
        ):
            # XXX
            # return self.request.response.redirect(canonical_url, status=301)
            pass
        return super().__call__()
