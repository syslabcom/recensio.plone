# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IReviewArticleJournal(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewArticleJournal"""


@implementer(IReviewArticleJournal)
class ReviewArticleJournal(Item):
    """Content-type class for IReviewArticleJournal"""
