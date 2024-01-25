from plone.supermodel import model
from plone.supermodel.interfaces import DEFAULT_ORDER
from recensio.plone import _


class fieldset(model.fieldset):
    id = None
    label = None
    description = None
    order = DEFAULT_ORDER

    def factory(self, fields=[], **kw):
        """Add fields to the fieldset."""
        return super().factory(
            self.id,
            label=self.label,
            description=self.description,
            fields=fields,
            order=self.order,
            **kw
        )


class fieldset_reviewed_text(fieldset):
    id = "reviewed_text"
    label = _("label_schema_reviewed_text", default="Reviewed Text")
    order = 20


class fieldset_review(fieldset):
    id = "review"
    label = _("label_schema_review", default="Review")
    order = 50


class fieldset_exhibition(fieldset):
    id = "exhibition"
    label = _("label_schema_exhibition", default="Ausstellung")
    order = 30


class fieldset_article(fieldset):
    id = "article"
    label = _("label_schema_article", default="Aufsatz")
    order = 30


class fieldset_edited_volume(fieldset):
    id = "edited_volume"
    label = _("label_schema_collection", default="Sammelband / Zeitschrift")
    order = 10
