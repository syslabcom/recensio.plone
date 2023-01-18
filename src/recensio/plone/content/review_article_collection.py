# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IReviewArticleCollection(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewArticleCollection"""


@implementer(IReviewArticleCollection)
class ReviewArticleCollection(Item):
    """Content-type class for IReviewArticleCollection"""
