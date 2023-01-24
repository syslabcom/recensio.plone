from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IPagesOfPresentedText(model.Schema):
    heading__page_number_of_presented_text_in_print = schema.TextLine(
        title=_(
            "description_page_number_of_presented_text_in_print",
            default=("Page numbers of the presented article"),
        ),
        required=False,
    )
    pageStartOfPresentedTextInPrint = schema.Int(
        title=_("label_page_start_of_presented_text_in_print", default="First page"),
        required=False,
    )
    pageEndOfPresentedTextInPrint = schema.Int(
        title=_("label_page_end_of_presented_text_in_print", default="Last page"),
        required=False,
    )
    # This is just use to show a label in the form
    # XXX It is probably better to use a custom widget with a schema.Field,
    # but I have to think more about it
    directives.mode(heading__page_number_of_presented_text_in_print="display")

    model.fieldset(
        "reviewed_text",
        label=_("label_schema_reviewed_text", default="Reviewed Text"),
        fields=[
            "heading__page_number_of_presented_text_in_print",
        ],
    )

    model.fieldset(
        "presented_text",
        label=_("label_schema_presented_text", default="Presented Text"),
        fields=[
            "pageStartOfPresentedTextInPrint",
            "pageEndOfPresentedTextInPrint",
        ],
    )


@adapter(IDexterityContent)
class PagesOfPresentedText:
    """Adapter for IPagesOfPresentedText."""

    def __init__(self, context):
        self.context = context

    @property
    def pageStartOfPresentedTextInPrint(self):
        return self.context.pageStartOfPresentedTextInPrint

    @pageStartOfPresentedTextInPrint.setter
    def pageStartOfPresentedTextInPrint(self, value):
        self.context.pageStartOfPresentedTextInPrint = value

    @property
    def pageEndOfPresentedTextInPrint(self):
        return self.context.pageEndOfPresentedTextInPrint

    @pageEndOfPresentedTextInPrint.setter
    def pageEndOfPresentedTextInPrint(self, value):
        self.context.pageEndOfPresentedTextInPrint = value

    @property
    def heading__page_number_of_presented_text_in_print(self):
        """This field is readonly."""
        return ""

    @heading__page_number_of_presented_text_in_print.setter
    def heading__page_number_of_presented_text_in_print(self, value):
        """This field is readonly."""
        pass
