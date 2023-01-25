from plone import api
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.authors import IAuthors
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from recensio.plone.behaviors.editorial import IEditorial
from recensio.plone.interfaces import IReview
from recensio.plone.utils import getFormatter
from recensio.plone.utils import punctuated_title_and_subtitle
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewArticleJournal(model.Schema):
    """Marker interface and Dexterity Python Schema for
    ReviewArticleJournal."""

    editor = schema.TextLine(
        title=_("Editor (name or institution)"),
        required=False,
    )

    titleJournal = schema.TextLine(
        title=_("title_journal", default="Title (Journal)"),
        required=True,
    )

    translatedTitleJournal = schema.TextLine(
        title=_(
            "label_translated_title_journal",
            default="Translated title (Journal)",
        ),
        required=False,
    )

    fieldset_reviewed_text(["editor", "translatedTitleJournal"])


# TODO
# * field `heading__page_number_of_presented_review_in_journal` from Base Review
#   is hidden
# * field `doc` from Base Review is hidden
# * field `heading_presented_work` from Printed Review is hidden
# * ReviewArticleJournalSchema["languageReviewedText"].label = _(u"Sprache (Aufsatz)")


@implementer(IReviewArticleJournal, IReview)
class ReviewArticleJournal(Item):
    """Content-type class for IReviewArticleJournal."""

    def formatted_authors_editorial(self):
        authors_str = IAuthors(self).get_formatted_authors()
        editors_str = IEditorial(self).get_formatted_editorial()
        return getFormatter(": ")(editors_str, authors_str)

    def getDecoratedTitle(self):
        args = {
            "in:": api.portal.translate(_("text_in", default="in:")),
            "page": api.portal.translate(_("text_pages", default="p.")),
            ":": api.portal.translate(_("text_colon", default=":")),
        }

        item = getFormatter(" ", ", ", " ", ", ", f", {args['page']} ")
        mag_year = getFormatter("/")(
            self.officialYearOfPublication, self.yearOfPublication
        )
        mag_year = f"({mag_year})" if mag_year else None
        translated_title_journal = self.translatedTitleJournal
        if translated_title_journal:
            translated_title_journal = f"[{translated_title_journal}]"
        item_string = item(
            self.titleJournal,
            translated_title_journal,
            self.volumeNumber,
            mag_year,
            self.issueNumber,
            self.page_start_end_in_print_article,
        )

        authors_string = self.formatted_authors_editorial()
        reviewer_string = IBase(self).get_formatted_review_authors()

        full_citation = getFormatter(": ", f", {args['in:']} ", " ")
        return full_citation(
            authors_string,
            punctuated_title_and_subtitle(self),
            item_string,
            reviewer_string,
        )
