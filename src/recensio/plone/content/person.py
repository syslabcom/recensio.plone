# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.supermodel import model
from zope.interface import implementer


class IPerson(model.Schema):
    """Marker interface and Dexterity Python Schema for Person"""


@implementer(IPerson)
class Person(Item):
    """Content-type class for IPerson"""
