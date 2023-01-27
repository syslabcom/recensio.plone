from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationArticleReview(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationArticleReview."""


@implementer(IPresentationArticleReview, IReview)
class PresentationArticleReview(Item):
    """Content-type class for IPresentationArticleReview."""

    # A ordered list of fields used for the metadata area of the view.
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReview",
        "languageReviewedText",
        "authors",
        "title",
        "subtitle",
        "titleJournal",
        "shortnameJournal",
        "yearOfPublication",
        "officialYearOfPublication",
        "volumeNumber",
        "issueNumber",
        "metadata_start_end_pages",
        "placeOfPublication",
        "publisher",
        "issn",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subject",
        "uri",
        "urn",
        "metadata_recensioID",
        "idBvb",
    ]
