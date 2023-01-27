from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IPresentationOnlineResource(model.Schema):
    """Marker interface and Dexterity Python Schema for
    PresentationOnlineResource."""


@implementer(IPresentationOnlineResource, IReview)
class PresentationOnlineResource(Item):
    """Content-type class for IPresentationOnlineResource."""

    # A ordered list of fields used for the metadata area of the view.
    metadata_fields = [
        "metadata_review_type_code",
        "metadata_presentation_author",
        "languageReview",
        "title",
        "uri",
        "urn",
        "institution",
        "languageReviewedText",
        "documenttypes_institution",
        "documenttypes_cooperation",
        "documenttypes_referenceworks",
        "documenttypes_bibliographical",
        "documenttypes_fulltexts",
        "documenttypes_periodicals",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subject",
        "metadata_recensioID",
    ]
