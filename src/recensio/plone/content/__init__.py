from plone.app.dexterity.behaviors.id import IShortName
from plone.app.dexterity.behaviors.metadata import ICategorization
from plone.autoform.interfaces import OMITTED_KEY
from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.supermodel.model import Fieldset
from recensio.plone import _
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope.interface import Interface


IShortName.setTaggedValue(
    OMITTED_KEY,
    [
        (Interface, "id", "true"),
        (IAddForm, "id", "false"),
        (IEditForm, "id", "false"),
    ],
)

reviewed_text_categorization = Fieldset(
    "reviewed_text",
    label=_("label_schema_reviewed_text", default="Reviewed Text"),
    fields=["subjects"],
)
ICategorization.setTaggedValue(FIELDSETS_KEY, [reviewed_text_categorization])
ICategorization.setTaggedValue(OMITTED_KEY, [(Interface, "language", "true")])
