from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IReviewJournal(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewJournal"""


@implementer(IReviewJournal)
class ReviewJournal(Item):
    """Content-type class for IReviewJournal"""
