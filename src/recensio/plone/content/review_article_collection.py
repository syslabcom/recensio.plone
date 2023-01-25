from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.authors import IAuthors
from recensio.plone.behaviors.base import IBase
from recensio.plone.interfaces import IReview
from recensio.plone.utils import get_formatted_names
from recensio.plone.utils import getFormatter
from recensio.plone.utils import punctuated_title_and_subtitle
from zope import schema
from zope.i18n import translate
from zope.i18nmessageid import Message
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


@implementer(IReviewArticleCollection, IReview)
class ReviewArticleCollection(Item):
    """Content-type class for IReviewArticleCollection."""

    def formatted_authors(self):
        authors_str = IAuthors(self).get_formatted_authors()
        return authors_str

    def getDecoratedTitle(self):
        args = {
            "(Hg.)": translate(
                Message("label_abbrev_editor", "recensio", default="(Hg.)")
            ),
            "in": translate(Message("text_in", "recensio", default="in:")),
            "page": translate(Message("text_pages", "recensio", default="p.")),
            ":": translate(Message("text_colon", "recensio", default=":")),
        }

        authors_string = self.formatted_authors()

        reviewer_string = IBase(self).get_formatted_review_authors()
        editors_string = get_formatted_names([rel.to_object for rel in self.editorial])

        edited_volume = getFormatter(
            f" {args['(Hg.)']}{args[':']} ", ". ", " ", f", {args['page']} "
        )
        translated_title = self.translatedTitleEditedVolume
        if translated_title:
            translated_title = f"[{translated_title}]"
        edited_volume_string = edited_volume(
            editors_string,
            self.titleEditedVolume,
            self.subtitleEditedVolume,
            translated_title,
            self.page_start_end_in_print_article,
        )

        full_citation = getFormatter(": ", ", in: ", " ")
        return full_citation(
            authors_string,
            punctuated_title_and_subtitle(self),
            edited_volume_string,
            reviewer_string,
        )
