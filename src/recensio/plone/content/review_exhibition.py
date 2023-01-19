from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IReviewExhibition(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewExhibition."""


@implementer(IReviewExhibition)
class ReviewExhibition(Item):
    """Content-type class for IReviewExhibition."""
