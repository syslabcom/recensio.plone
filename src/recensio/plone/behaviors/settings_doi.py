from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ISettingsDoi(model.Schema):
    doiRegistrationActive = schema.Bool(
        title=_("Activate DOI registration"),
        description=_(
            "description_activate_doi_registration",
            default=("Activates the registration of DOIs at da|ra"),
        ),
        default=True,
        required=False,
    )


@adapter(IDexterityContent)
class SettingsDoi:
    """Adapter for ISettingsDoi."""

    def __init__(self, context):
        self.context = context

    @property
    def doiRegistrationActive(self):
        return self.context.doiRegistrationActive

    @doiRegistrationActive.setter
    def doiRegistrationActive(self, value):
        self.context.doiRegistrationActive = value
