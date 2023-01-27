from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationMonograph(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationMonograph."""


@implementer(IPresentationMonograph, IReview)
class PresentationMonograph(Item):
    """Content-type class for IPresentationMonograph."""

    # A ordered list of fields used for the metadata area of the view.
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "editorial",
        "title",
        "subtitle",
        "yearOfPublication",
        "placeOfPublication",
        "publisher",
        "series",
        "seriesVol",
        "pages",
        "isbn",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subject",
        "urn",
        "metadata_recensioID",
        "idBvb",
    ]
