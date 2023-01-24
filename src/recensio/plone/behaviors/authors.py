from plone.app.vocabularies.catalog import CatalogSource
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IAuthors(model.Schema):
    directives.widget(
        "authors",
        RelatedItemsFieldWidget,
        pattern_options={"mode": "auto", "favorites": []},
    )
    authors = RelationList(
        title=_("Authors"),
        defaultFactory=list,
        value_type=RelationChoice(source=CatalogSource(portal_type="Person")),
        required=False,
    )

    model.fieldset(
        "reviewed_text",
        label=_("label_schema_reviewed_text", default="Reviewed Text"),
        fields=["authors"],
    )


@adapter(IDexterityContent)
class Authors:
    """Adapter for IAuthors."""

    def __init__(self, context):
        self.context = context

    @property
    def authors(self):
        return self.context.authors

    @authors.setter
    def authors(self, value):
        self.context.authors = value
