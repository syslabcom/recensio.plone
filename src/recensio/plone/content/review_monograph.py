from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IReviewMonograph(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewMonograph"""


@implementer(IReviewMonograph)
class ReviewMonograph(Item):
    """Content-type class for IReviewMonograph"""
