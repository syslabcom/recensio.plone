from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.authors import IAuthors
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from recensio.plone.behaviors.editorial import IEditorial
from recensio.plone.interfaces import IReview
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

    fieldset_reviewed_text(["translatedTitle"])


@implementer(IReviewMonograph, IReview)
class ReviewMonograph(Item):
    """Content-type class for IReviewMonograph."""

    def formatted_authors_editorial(self):
        authors_str = IAuthors(self).get_formatted_authors()
        editors_str = IEditorial(self).get_formatted_editorial()
        return getFormatter(": ")(editors_str, authors_str)

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
