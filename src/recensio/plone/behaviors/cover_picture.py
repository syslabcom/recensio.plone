from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_edited_volume
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ICoverPicture(model.Schema):
    coverPicture = NamedBlobImage(
        title=_("Cover picture"),
        required=False,
    )
    fieldset_reviewed_text(["coverPicture"])


@provider(IFormFieldProvider)
class ICoverPictureEditedVolume(model.Schema):
    coverPicture = NamedBlobImage(
        title=_("Cover picture"),
        required=False,
    )
    fieldset_edited_volume(["coverPicture"])


@adapter(IDexterityContent)
class CoverPicture:
    """Adapter for ICoverPicture."""

    def __init__(self, context):
        self.context = context

    @property
    def coverPicture(self):
        return self.context.coverPicture

    @coverPicture.setter
    def coverPicture(self, value):
        self.context.coverPicture = value
