from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewJournal(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewJournal."""

    # TODO
    # schemata="reviewed_text",
    editor = schema.TextLine(
        title=_("Editor (name or institution)"),
    )

    # TODO
    # schemata="reviewed_text",
    translatedTitleJournal = schema.TextLine(
        title=_(
            "label_translated_title_journal",
            default="Translated title (Journal)",
        ),
    )


# TODO
# * ReviewJournalSchema["title"].widget.label = _(u"Title (journal)")
# * field `subtitle` from Printed Review is hidden


@implementer(IReviewJournal)
class ReviewJournal(Item):
    """Content-type class for IReviewJournal."""
