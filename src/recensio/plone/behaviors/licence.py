from plone.app.vocabularies.catalog import CatalogSource
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from z3c.relationfield.schema import RelationChoice
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ILicence(model.Schema):
    # TODO
    # rows=3,
    licence = schema.Text(
        title=_("label_publication_licence", default="Publication Licence"),
        description=_(
            "description_publication_licence",
            default=(
                "Please specify the licence terms under which reviews "
                "may be used. This text will be displayed on the front "
                "page of the PDF version and to the side of the web "
                "version of each review for this publication."
            ),
        ),
        required=False,
    )

    directives.widget(
        "licence_ref",
        RelatedItemsFieldWidget,
        pattern_options={"mode": "auto", "favorites": []},
    )
    licence_ref = RelationChoice(
        title=_(
            "label_publication_licence_ref",
            default="Publication Licence (Translated)",
        ),
        description=_(
            "description_publication_licence_ref",
            default=(
                "To specify a licence text that will be "
                "displayed in the current UI language, select a "
                "page that has been translated with the platform's "
                "translation mechanism."
            ),
        ),
        source=CatalogSource(portal_type="Document"),
        required=False,
    )


@adapter(IDexterityContent)
class Licence:
    """Adapter for ILicence."""

    def __init__(self, context):
        self.context = context

    @property
    def licence(self):
        return self.context.licence

    @licence.setter
    def licence(self, value):
        self.context.licence = value

    @property
    def licence_ref(self):
        return self.context.licence_ref

    @licence_ref.setter
    def licence_ref(self, value):
        self.context.licence_ref = value
