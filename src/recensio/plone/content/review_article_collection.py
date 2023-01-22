from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewArticleCollection(model.Schema):
    """Marker interface and Dexterity Python Schema for
    ReviewArticleCollection."""

    titleEditedVolume = schema.TextLine(
        title=_("title_edited_volume", default="Title (Edited Volume)"),
        required=True,
    )

    subtitleEditedVolume = schema.TextLine(
        title=_("subtitle_edited_volume", default="Subtitle (Edited Volume)"),
        required=False,
    )

    # TODO
    # size=60
    translatedTitleEditedVolume = schema.TextLine(
        required=False,
        title=_("Translated title (Edited Volume)"),
    )


# TODO
# * field `doc` from Base Review is hidden
# * field `help_authors_or_editors` from Editorial is hidden
# * field `additionalTitles` from Book Review is hidden
# * field `heading_presented_work` from Printed Review is hidden


@implementer(IReviewArticleCollection)
class ReviewArticleCollection(Item):
    """Content-type class for IReviewArticleCollection."""
