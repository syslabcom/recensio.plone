from plone.app.content.interfaces import INameFromTitle
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from Products.CMFPlone import PloneMessageFactory as _PMF
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IPerson(model.Schema):
    """Marker interface and Dexterity Python Schema for Person."""

    firstname = schema.TextLine(
        title=_("First name"),
        required=False,
    )
    lastname = schema.TextLine(
        title=_("Last name"),
        required=True,
    )
    gndId = schema.TextLine(
        title=_("GND"),
        description=_("help_gndId", default=""),
        required=False,
    )

    # Define the necessary basic metadata fields `title` and `description` but
    # do not show them in edit and add forms.
    # Instead, the title is generated from the firstname and lastname.
    title = schema.TextLine(
        title=_PMF("label_title", default="Title"),
        required=False,
        missing_value="",
    )
    description = schema.Text(
        title=_PMF("label_description", default="Summary"),
        required=False,
        missing_value="",
    )
    form.omitted("title", "description")


@implementer(IPerson)
class Person(Item):
    """Content-type class for IPerson."""


@implementer(INameFromTitle)
@adapter(IPerson)
class NameFromPerson:
    def __new__(cls, context):
        # Similar to:
        # plone.app.dexterity.behaviors.filename.NameFromFileName
        title = ", ".join([it for it in [context.lastname, context.firstname] if it])
        instance = super().__new__(cls)
        instance.title = title
        context.title = title
        return instance

    def __init__(self, context):
        pass
