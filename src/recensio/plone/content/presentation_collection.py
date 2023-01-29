from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationCollection(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for
    PresentationCollection."""


@implementer(IPresentationCollection)
class PresentationCollection(Item):
    """Content-type class for IPresentationCollection."""
