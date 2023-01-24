from plone.app.vocabularies.catalog import CatalogSource
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IEditorial(model.Schema):
    help_authors_or_editors = schema.TextLine(
        title=_(
            "help_authors_or_editors",
            default=(
                "Please fill in either authors OR editors "
                "(exception: Complete Works etc.)"
            ),
        ),
        required=False,
    )
    # This is just use to show a label in the form
    # XXX It is probably better to use a custom widget with a schema.Field,
    # but I have to think more about it
    directives.mode(help_authors_or_editors="display")

    editorial = RelationList(
        title=_("label_editorial", default="Editor(s) of the presented monograph"),
        defaultFactory=list,
        value_type=RelationChoice(source=CatalogSource(portal_type="Person")),
        required=False,
    )
    directives.widget(
        "editorial",
        RelatedItemsFieldWidget,
        pattern_options={"mode": "auto", "favorites": []},
    )


@adapter(IDexterityContent)
class Editorial:
    """Adapter for IEditorial."""

    def __init__(self, context):
        self.context = context

    @property
    def help_authors_or_editors(self):
        """This field is readonly."""
        return ""

    @help_authors_or_editors.setter
    def help_authors_or_editors(self, value):
        """This field is readonly."""
        pass

    @property
    def editorial(self):
        return self.context.editorial

    @editorial.setter
    def editorial(self, value):
        self.context.editorial = value
