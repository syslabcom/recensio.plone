from plone.app.dexterity.behaviors.id import IShortName
from plone.autoform.interfaces import OMITTED_KEY
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
