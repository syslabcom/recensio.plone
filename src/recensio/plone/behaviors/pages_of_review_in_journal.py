from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_review
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IPagesOfReviewInJournal(model.Schema):
    directives.order_after(pageStartOfReviewInJournal="IBaseReview.pageEnd")
    pageStartOfReviewInJournal = schema.Int(
        title=_("label_page_start_of_review_in_journal", default="First page"),
        required=False,
    )
    directives.order_after(
        pageEndOfReviewInJournal="IPagesOfReviewInJournal.pageStartOfReviewInJournal"
    )
    pageEndOfReviewInJournal = schema.Int(
        title=_("label_page_end_of_review_in_journal", default="Last page"),
        required=False,
    )

    fieldset_review(
        [
            "pageStartOfReviewInJournal",
            "pageEndOfReviewInJournal",
        ]
    )


@adapter(IDexterityContent)
class PagesOfReviewInJournal:
    """Adapter for IPagesOfReviewInJournal."""

    def __init__(self, context):
        self.context = context

    @property
    def pageStartOfReviewInJournal(self):
        return self.context.pageStartOfReviewInJournal

    @pageStartOfReviewInJournal.setter
    def pageStartOfReviewInJournal(self, value):
        self.context.pageStartOfReviewInJournal = value

    @property
    def pageEndOfReviewInJournal(self):
        return self.context.pageEndOfReviewInJournal

    @pageEndOfReviewInJournal.setter
    def pageEndOfReviewInJournal(self, value):
        self.context.pageEndOfReviewInJournal = value
