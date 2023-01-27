from Products.CMFPlone.Portal import PloneSite
from zope.interface import implementer
from zope.interface import Interface

import Acquisition


class IParentGetter(Interface):
    """Get parent of a certain content type."""

    def get_parent_object_of_type(portal_type):
        """Return the object of a particular type which is the parent of the
        current object."""

    def get_title_from_parent_of_type(portal_type):
        """Return the title of the first object of a particular type which is a
        parent of the current object."""

    def get_flag_with_override(field_name, override_value):
        """Retrieves a boolean field value, allowing for overrides from a
        parent.

        If any object in the acquisition chain has the override_value
        set for the field specified by field_name, then this value is
        used. Only if no object in the chain has it set is the inverse
        value used.
        """


@implementer(IParentGetter)
class ParentGetter:
    """Get parent of a certain content type."""

    def __init__(self, context):
        self.context = context

    def get_title_from_parent_of_type(self, portal_type):
        """Return the title of the first object of a particular type which is a
        parent of the current object."""
        obj = self.get_parent_object_of_type(portal_type)
        if obj:
            return obj.Title()
        return ""

    def get_parent_object_of_type(self, portal_type):
        """Return the object of a particular type which is the parent of the
        current object."""
        if (
            hasattr(self.context, "portal_type")
            and self.context.portal_type == portal_type
        ):
            return self.context
        obj = Acquisition.aq_inner(self.context)
        while not isinstance(obj, PloneSite):
            obj = Acquisition.aq_parent(obj)
            if hasattr(obj, "portal_type") and obj.portal_type == portal_type:
                return obj
        return None

    def get_flag_with_override(self, field_name, override_value):
        """Retrieves a boolean field value, allowing for overrides from a
        parent.

        If any object in the acquisition chain has the override_value
        set for the field specified by field_name, then this value is
        used. Only if no object in the chain has it set is the inverse
        value used.
        """
        publication = self.get_parent_object_of_type("Publication")
        current = self.context
        value = not override_value
        if publication is not None:
            while current != publication.aq_parent:
                schema = current.Schema()
                if field_name in schema:
                    field = schema.get(field_name)
                    value = field.get(current)
                    if value is override_value:
                        break
                current = current.aq_parent
        return value
