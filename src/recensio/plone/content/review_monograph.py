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
class IReviewMonograph(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for ReviewMonograph."""

    directives.order_after(translatedTitle="IBookReview.additionalTitles")
    textindexer.searchable("translatedTitle")
    translatedTitle = schema.TextLine(
        title=_("Translated Title"),
        required=False,
    )

    fieldset_reviewed_text(["translatedTitle"])


@implementer(IReviewMonograph)
class ReviewMonograph(Item):
    """Content-type class for IReviewMonograph."""
