from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationCollection(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationCollection."""


@implementer(IPresentationCollection, IReview)
class PresentationCollection(Item):
    """Content-type class for IPresentationCollection."""

    # A ordered list of fields used for the metadata area of the view.
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReviewedText",
        "languageReview",
        "authors",
        "title",
        "subtitle",
        "metadata_start_end_pages",
        "editorsCollectedEdition",
        "titleCollectedEdition",
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
        "uri",
        "urn",
        "metadata_recensioID",
        "idBvb",
    ]
