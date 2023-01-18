# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


# from recensio.plone import _


class IIssue(model.Schema):
    """Marker interface and Dexterity Python Schema for Issue"""


@implementer(IIssue)
class Issue(Container):
    """Content-type class for IIssue"""
