from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IPublication(model.Schema):
    """Marker interface and Dexterity Python Schema for Publication."""


@implementer(IPublication)
class Publication(Container):
    """Content-type class for IPublication."""
