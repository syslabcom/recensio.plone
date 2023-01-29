from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from recensio.plone.content.base_review import BaseReview
from recensio.plone.interfaces import IReview
from recensio.plone.utils import getFormatter
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewJournal(model.Schema, IReview):
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


@implementer(IReviewJournal)
class ReviewJournal(Item, BaseReview):
    """Content-type class for IReviewJournal."""

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
