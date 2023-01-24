from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ISettingsFulltext(model.Schema):
    useExternalFulltext = schema.Bool(
        title=_("Use external full text"),
        description=_(
            "description_use_external_full_text",
            default=(
                "Don't show the full text of contained reviews "
                "directly but link to the external source instead."
            ),
        ),
        default=False,
        required=False,
    )


@adapter(IDexterityContent)
class SettingsFulltext:
    """Adapter for ISettingsFulltext."""

    def __init__(self, context):
        self.context = context

    @property
    def useExternalFulltext(self):
        return self.context.useExternalFulltext

    @useExternalFulltext.setter
    def useExternalFulltext(self, value):
        self.context.useExternalFulltext = value
