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
class IReviewArticleJournal(model.Schema, IReview):
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


@implementer(IReviewArticleJournal)
class ReviewArticleJournal(Item):
    """Content-type class for IReviewArticleJournal."""
