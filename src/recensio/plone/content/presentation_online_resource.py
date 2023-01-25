from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationOnlineResource(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationOnlineResource."""


@implementer(IPresentationOnlineResource, IReview)
class PresentationOnlineResource(Item):
    """Content-type class for IPresentationOnlineResource."""
