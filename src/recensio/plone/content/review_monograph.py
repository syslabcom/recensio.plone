from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewMonograph(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewMonograph."""

    # TODO
    # schemata="reviewed_text"
    translatedTitle = schema.TextLine(
        title=_("Translated Title"),
        required=False,
    )


@implementer(IReviewMonograph)
class ReviewMonograph(Item):
    """Content-type class for IReviewMonograph."""
