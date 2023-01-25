from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IVolume(model.Schema):
    """Marker interface and Dexterity Python Schema for Volume."""


@implementer(IVolume)
class Volume(Container):
    """Content-type class for IVolume."""
