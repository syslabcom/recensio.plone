from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.base import IBase
from recensio.plone.utils import getFormatter
from recensio.plone.utils import punctuated_title_and_subtitle
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewMonograph(model.Schema):
    """Marker interface and Dexterity Python Schema for ReviewMonograph."""

    translatedTitle = schema.TextLine(
        title=_("Translated Title"),
        required=False,
    )

    model.fieldset(
        "reviewed_text",
        label=_("label_schema_reviewed_text", default="Reviewed Text"),
        fields=[
            "translatedTitle",
        ],
    )


@implementer(IReviewMonograph)
class ReviewMonograph(Item):
    """Content-type class for IReviewMonograph."""

    def formatted_authors_editorial(self):
        # TODO
        return ""

    def getDecoratedTitle(self):
        """Original Spec:

            [Werkautor Vorname] [Werkautor Nachname]: [Werktitel]. [Werk-Untertitel]
            (reviewed by [Rezensent Vorname] [Rezensent Nachname])

        Analog, Werkautoren kann es mehrere geben (Siehe Citation)

        Hans Meier: Geschichte des Abendlandes. Ein Abriss (reviewed by Klaus Müller)
        """
        authors_string = self.formatted_authors_editorial()

        reviewer_string = IBase(self).get_formatted_review_authors()

        full_citation = getFormatter(": ", " ")
        return full_citation(
            authors_string, punctuated_title_and_subtitle(self), reviewer_string
        )
