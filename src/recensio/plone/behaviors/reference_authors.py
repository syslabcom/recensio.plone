from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import Interface
from zope.interface import provider


class IReferenceAuthorRowSchema(Interface):
    """Schema for a row in the datagridfield."""

    lastname = schema.TextLine(title=_("Lastname"), required=False)
    firstname = schema.TextLine(title=_("Firstname"), required=False)
    email = schema.TextLine(title=_("Email address"), required=False)
    address = schema.TextLine(title=_("Institution"), required=False)
    phone = schema.TextLine(title=_("Phone"), required=False)
    preferred_language = schema.Choice(
        title=_("label_preferred_language", default="Preferred language"),
        vocabulary="plone.app.vocabularies.SupportedContentLanguages",
        required=False,
    )


@provider(IFormFieldProvider)
class IReferenceAuthors(model.Schema):
    directives.widget(referenceAuthors=DataGridFieldFactory)
    referenceAuthors = schema.List(
        title=_(
            "label_reference_authors",
            default=(
                "Reference Authors (email address, postal address and phone "
                "number are not publicly visible)"
            ),
        ),
        description=_("Enter data here. New rows will be added automatically."),
        value_type=DictRow(schema=IReferenceAuthorRowSchema, required=False),
        required=False,
    )

    fieldset(
        "review",
        label=_("label_schema_review", default="Review"),
        fields=[
            "referenceAuthors",
        ],
    )


@adapter(IDexterityContent)
class ReferenceAuthors:
    """Adapter for IReferenceAuthors."""

    def __init__(self, context):
        self.context = context

    @property
    def referenceAuthors(self):
        return self.context.referenceAuthors

    @referenceAuthors.setter
    def referenceAuthors(self, value):
        self.context.referenceAuthors = value
