from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IPresentationCollection(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationCollection."""


@implementer(IPresentationCollection)
class PresentationCollection(Item):
    """Content-type class for IPresentationCollection."""
