from plone.app.dexterity import _ as _DX
from plone.app.dexterity import textindexer
from plone.app.z3cform.widget import SelectFieldWidget
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
class ITextReview(model.Schema):
    directives.widget("languageReviewedText", SelectFieldWidget)
    languageReviewedText = schema.List(
        title=_("Language(s) (text)"),
        value_type=schema.Choice(
            vocabulary="recensio.plone.vocabularies.available_content_languages"
        ),
        required=False,
        defaultFactory=list,
    )

    textindexer.searchable("title")
    title = schema.TextLine(title=_DX("label_title", default="Title"), required=True)

    fieldset_reviewed_text(
        [
            "languageReviewedText",
            "title",
        ],
    )


@adapter(IDexterityContent)
class TextReview:
    """Adapter for ITextReview."""

    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        return self.context.title

    @title.setter
    def title(self, value):
        self.context.title = value

    @property
    def languageReviewedText(self):
        return self.context.languageReviewedText

    @languageReviewedText.setter
    def languageReviewedText(self, value):
        self.context.languageReviewedText = value
