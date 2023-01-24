from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from recensio.plone import _
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ICoverPicture(model.Schema):
    coverPicture = NamedBlobImage(
        title=_("Cover picture"),
        required=False,
    )

    fieldset(
        "reviewed_text",
        label=_("label_schema_reviewed_text", default="Reviewed Text"),
        fields=["coverPicture"],
    )


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
