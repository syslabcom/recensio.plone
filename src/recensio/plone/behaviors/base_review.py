from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.app.dexterity.textindexer import searchable
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.field import NamedBlobFile
from plone.namedfile.field import NamedBlobImage
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_review
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IBaseReview(model.Schema):
    directives.order_after(pdf="IBase.languageReview")
    pdf = NamedBlobFile(
        title=_("PDF"),
        required=False,
    )
    searchable("pdf")
    directives.omitted("pdf")
    directives.no_omit(IAddForm, "pdf")
    directives.no_omit(IEditForm, "pdf")

    directives.order_after(pageStart="IBaseReview.pdf")
    pageStart = schema.Int(
        title=_("label_page_start_in_pdf", default="Page number (start)"),
        description=_(
            "description_page_number",
            default="Please fill in only if the review is part of a larger pdf-file",
        ),
        required=False,
    )
    directives.order_after(pageEnd="IBaseReview.pageStart")
    pageEnd = schema.Int(
        title=_("label_page_end_in_pdf", default="Page number (end)"),
        required=False,
    )

    directives.order_after(doc="IPagesOfReviewInJournal.pageEndOfReviewInJournal")
    doc = NamedBlobFile(
        title=_("Word Document"),
        required=False,
    )

    directives.order_after(customCitation="IBase.review")
    customCitation = schema.Text(
        title=_("Optional citation format"),
        description=_(
            "description_custom_citation",
            default=(
                "Please fill in only if you wish to use a citation format "
                "different from the platform's"
            ),
        ),
        required=False,
    )

    directives.order_after(doi="ILicence.licence")
    doi = schema.TextLine(
        title=_("label_doi", default=("DOI")),
        description=_(
            "description_doi",
            default=("Digital Object Identifier"),
        ),
        required=False,
    )

    directives.order_after(customCoverImage="IBaseReview.doi")
    customCoverImage = NamedBlobImage(
        title=_("Custom cover image"),
        description=_(
            "description_custom_cover_image",
            default="Image that will be shown as a link to the external "
            'full text. Only used if "Use external full text" is '
            "activated on the volume or issue.",
        ),
        required=False,
    )

    fieldset_review(
        [
            "pdf",
            "pageStart",
            "pageEnd",
            "doc",
            "customCitation",
            "doi",
            "customCoverImage",
        ],
    )


@adapter(IDexterityContent)
class BaseReview:
    """Adapter for IBaseReview."""

    def __init__(self, context):
        self.context = context

    @property
    def pdf(self):
        return self.context.pdf

    @pdf.setter
    def pdf(self, value):
        self.context.pdf = value

    @property
    def pageStart(self):
        return self.context.pageStart

    @pageStart.setter
    def pageStart(self, value):
        self.context.pageStart = value

    @property
    def pageEnd(self):
        return self.context.pageEnd

    @pageEnd.setter
    def pageEnd(self, value):
        self.context.pageEnd = value

    @property
    def doc(self):
        return self.context.doc

    @doc.setter
    def doc(self, value):
        self.context.doc = value

    @property
    def customCitation(self):
        return self.context.customCitation

    @customCitation.setter
    def customCitation(self, value):
        self.context.customCitation = value

    @property
    def doi(self):
        return self.context.doi

    @doi.setter
    def doi(self, value):
        self.context.doi = value

    @property
    def customCoverImage(self):
        return self.context.customCoverImage

    @customCoverImage.setter
    def customCoverImage(self, value):
        self.context.customCoverImage = value
