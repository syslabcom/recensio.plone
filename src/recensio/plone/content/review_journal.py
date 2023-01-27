from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from recensio.plone.interfaces import IReview
from recensio.plone.utils import getFormatter
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewJournal(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewJournal."""

    editor = schema.TextLine(
        title=_("Editor (name or institution)"),
    )

    translatedTitleJournal = schema.TextLine(
        title=_(
            "label_translated_title_journal",
            default="Translated title (Journal)",
        ),
    )

    fieldset_reviewed_text(["editor", "translatedTitleJournal"])


# TODO
# * ReviewJournalSchema["title"].widget.label = _(u"Title (journal)")
# * field `subtitle` from Printed Review is hidden


@implementer(IReviewJournal, IReview)
class ReviewJournal(Item):
    """Content-type class for IReviewJournal."""

    # A ordered list of fields used for the metadata area of the view.
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
        "subject",
        "canonical_uri",
        "urn",
        "effectiveDate",
        "metadata_recensioID",
        "idBvb",
        "doi",
    ]

    def getDecoratedTitle(self):
        item = getFormatter(" ", ", ", " ", ", ")
        mag_year = getFormatter("/")(
            self.officialYearOfPublication, self.yearOfPublication
        )
        mag_year = f"({mag_year})" if mag_year else None
        translated_title = self.translatedTitleJournal
        if translated_title:
            translated_title = f"[{translated_title}]"
        item_string = item(
            self.title, translated_title, self.volumeNumber, mag_year, self.issueNumber
        )

        reviewer_string = IBase(self).get_formatted_review_authors()

        return " ".join((item_string, reviewer_string))
