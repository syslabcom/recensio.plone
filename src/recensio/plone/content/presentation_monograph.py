from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IPresentationMonograph(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationMonograph."""


@implementer(IPresentationMonograph)
class PresentationMonograph(Item):
    """Content-type class for IPresentationMonograph."""
