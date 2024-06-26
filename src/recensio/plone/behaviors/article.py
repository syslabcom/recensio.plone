from plone.app.dexterity import textindexer
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IArticle(model.Schema):
    url_article = schema.TextLine(
        title=_("URL (Aufsatz)"),
        required=False,
    )

    urn_article = schema.TextLine(
        title=_("URN (Aufsatz)"),
        required=False,
    )

    doi_article = schema.TextLine(
        title=_("DOI (Aufsatz)"),
        required=False,
    )

    directives.order_after(subtitle="ITextReview.title")
    textindexer.searchable("subtitle")
    subtitle = schema.TextLine(
        title=_("Subtitle"),
        required=False,
    )
    directives.order_after(translatedTitle="IArticle.subtitle")
    textindexer.searchable("translatedTitle")
    translatedTitle = schema.TextLine(
        title=_("Translated Title"),
        required=False,
    )

    heading__page_number_of_article_in_journal_or_edited_volume = schema.TextLine(
        title=_(
            "description_page_number_of_article_in_journal_or_edited_volume",
            default=("Page numbers of the article"),
        ),
        required=False,
    )
    # This is just use to show a label in the form
    # XXX It is probably better to use a custom widget with a schema.Field,
    # but I have to think more about it
    directives.mode(
        heading__page_number_of_article_in_journal_or_edited_volume="display"
    )

    pageStartOfArticle = schema.Int(
        title=_("label_page_start_of_article_in_journal_or_edited_volume"),
        required=False,
    )

    pageEndOfArticle = schema.Int(
        title=_("label_page_end_of_article_in_journal_or_edited_volume"),
        required=False,
    )

    fieldset_reviewed_text(
        [
            "url_article",
            "urn_article",
            "doi_article",
            "subtitle",
            "translatedTitle",
            "heading__page_number_of_article_in_journal_or_edited_volume",
            "pageStartOfArticle",
            "pageEndOfArticle",
        ]
    )


@adapter(IDexterityContent)
class Article:
    """Adapter for IArticle."""

    def __init__(self, context):
        self.context = context

    @property
    def url_article(self):
        return self.context.url_article

    @url_article.setter
    def url_article(self, value):
        self.context.url_article = value

    @property
    def urn_article(self):
        return self.context.urn_article

    @urn_article.setter
    def urn_article(self, value):
        self.context.urn_article = value

    @property
    def doi_article(self):
        return self.context.doi_article

    @doi_article.setter
    def doi_article(self, value):
        self.context.doi_article = value

    @property
    def translatedTitle(self):
        return self.context.translatedTitle

    @translatedTitle.setter
    def translatedTitle(self, value):
        self.context.translatedTitle = value

    @property
    def subtitle(self):
        return self.context.subtitle

    @subtitle.setter
    def subtitle(self, value):
        self.context.subtitle = value

    @property
    def heading__page_number_of_article_in_journal_or_edited_volume(self):
        return ""

    @heading__page_number_of_article_in_journal_or_edited_volume.setter
    def heading__page_number_of_article_in_journal_or_edited_volume(self, value):
        pass

    @property
    def pageStartOfArticle(self):
        return self.context.pageStartOfArticle

    @pageStartOfArticle.setter
    def pageStartOfArticle(self, value):
        self.context.pageStartOfArticle = value

    @property
    def pageEndOfArticle(self):
        return self.context.pageEndOfArticle

    @pageEndOfArticle.setter
    def pageEndOfArticle(self, value):
        self.context.pageEndOfArticle = value
