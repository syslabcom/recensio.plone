from plone.app.dexterity import textindexer
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from recensio.plone.interfaces import IReview
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewJournal(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for ReviewJournal."""

    directives.order_after(editor="IJournalReview.doi_journal")
    textindexer.searchable("editor")
    editor = schema.TextLine(
        title=_("Editor (name or institution)"),
        required=False,
    )

    directives.order_after(translatedTitleJournal="ITextReview.title")
    textindexer.searchable("translatedTitleJournal")
    translatedTitleJournal = schema.TextLine(
        title=_(
            "label_translated_title_journal",
            default="Translated title (Journal)",
        ),
        required=False,
    )

    fieldset_reviewed_text(["editor", "translatedTitleJournal"])


# TODO
# * ReviewJournalSchema["title"].widget.label = _(u"Title (journal)")
# * field `subtitle` from Printed Review is hidden


@implementer(IReviewJournal)
class ReviewJournal(Item):
    """Content-type class for IReviewJournal."""
