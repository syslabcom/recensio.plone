from plone.app.dexterity import textindexer
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_edited_volume
from recensio.plone.interfaces import IReview
from zope import schema
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IReviewArticleCollection(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for
    ReviewArticleCollection."""

    directives.order_after(titleEditedVolume="IEditorialEditedVolume.editorial")
    textindexer.searchable("titleEditedVolume")
    titleEditedVolume = schema.TextLine(
        title=_("title_edited_volume", default="Title (Edited Volume)"),
        required=True,
    )

    directives.order_after(subtitleEditedVolume="titleEditedVolume")
    textindexer.searchable("subtitleEditedVolume")
    subtitleEditedVolume = schema.TextLine(
        title=_("subtitle_edited_volume", default="Subtitle (Edited Volume)"),
        required=False,
    )

    directives.order_after(translatedTitleEditedVolume="subtitleEditedVolume")
    textindexer.searchable("translatedTitleEditedVolume")
    # TODO
    # size=60
    translatedTitleEditedVolume = schema.TextLine(
        required=False,
        title=_("Translated title (Edited Volume)"),
    )

    fieldset_edited_volume(
        ["titleEditedVolume", "subtitleEditedVolume", "translatedTitleEditedVolume"]
    )


# TODO
# * field `doc` from Base Review is hidden
# * field `help_authors_or_editors` from Editorial is hidden
# * field `additionalTitles` from Book Review is hidden
# * field `heading_presented_work` from Printed Review is hidden


@implementer(IReviewArticleCollection)
class ReviewArticleCollection(Item):
    """Content-type class for IReviewArticleCollection."""
