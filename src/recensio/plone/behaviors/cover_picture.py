from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from recensio.plone import _
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ICoverPicture(model.Schema):

    coverPicture = NamedBlobImage(
        title=_("Cover picture"),
        required=False,
    )


@adapter(IDexterityContent)
class CoverPicture:
    """Adapter for ICoverPicture"""

    def __init__(self, context):
        self.context = context

    @property
    def coverPicture(self):
        return self.context.coverPicture

    @coverPicture.setter
    def coverPicture(self, value):
        self.context.coverPicture = value
