from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationMonograph(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for
    PresentationMonograph."""


@implementer(IPresentationMonograph)
class PresentationMonograph(Item):
    """Content-type class for IPresentationMonograph."""
