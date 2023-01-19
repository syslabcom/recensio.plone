from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IPresentationArticleReview(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationArticleReview."""


@implementer(IPresentationArticleReview)
class PresentationArticleReview(Item):
    """Content-type class for IPresentationArticleReview."""
