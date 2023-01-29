from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationArticleReview(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for
    PresentationArticleReview."""


@implementer(IPresentationArticleReview)
class PresentationArticleReview(Item):
    """Content-type class for IPresentationArticleReview."""
