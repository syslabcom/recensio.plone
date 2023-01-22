from plone.app.dexterity.behaviors.metadata import default_language
from plone.app.dexterity.textindexer import searchable
from plone.app.textfield import RichText as RichTextField
from plone.app.vocabularies.catalog import CatalogSource
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.app.z3cform.widget import RichTextFieldWidget
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile import field as namedfile
from plone.supermodel import model
from recensio.plone import _
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.component import adapter
from zope.interface import provider


# from plone.supermodel.directives import fieldset


# TODO, maybe:
# - Move `title` to fieldset "reviewed_text"
# - Move `subject` to fieldset "reviewed_text"
# - Set content type for `generatedPdf` to `application/pdf`
# - Set a character limit for `review`: 4000 characters
# - Set rows for `review` to 20

# TODO: REVIEW the following.
# Left out attributes from recensio.contenttype.content.schemata.BaseReviewSchema:
# - reviewAuthorLastname: For migration to reviewAuthors only
# - reviewAuthorFirstname: For migration to reviewAuthors only
# - uri: Partner URL is no longer used for reviews but was being kept to
#        avoid breakage
#        this is still used in presentations. #3103


@provider(IFormFieldProvider)
class IBase(model.Schema):
    directives.widget(
        "reviewAuthors",
        RelatedItemsFieldWidget,
        pattern_options={"mode": "auto", "favorites": []},
    )
    reviewAuthors = RelationList(
        title=_("label_review_authors"),
        defaultFactory=list,
        value_type=RelationChoice(source=CatalogSource(portal_type="Person")),
        required=True,
    )

    directives.widget("languageReview", SelectFieldWidget)
    languageReview = schema.Choice(
        title=_("Language(s) (review)"),
        vocabulary="plone.app.vocabularies.SupportedContentLanguages",
        required=False,
        missing_value="",
        defaultFactory=default_language,
    )

    directives.widget("languageReviewedText", SelectFieldWidget)
    languageReviewedText = schema.Choice(
        title=_("Language(s) (text)"),
        vocabulary="plone.app.vocabularies.SupportedContentLanguages",
        required=False,
        missing_value="",
        defaultFactory=default_language,
    )

    recensioID = schema.TextLine(
        required=False,
    )
    directives.omitted("recensioID")

    generatedPdf = namedfile.NamedBlobFile(
        title=_("Generated Pdf"),
        required=False,
    )
    directives.omitted("generatedPdf")
    directives.no_omit(IEditForm, "generatedPdf")
    directives.no_omit(IAddForm, "generatedPdf")

    directives.widget("review", RichTextFieldWidget)
    searchable("review")
    review = RichTextField(
        title=_("Core Statements"),
        required=False,
        allowed_mime_types=["text/html"],
    )

    urn = schema.TextLine(
        title=_("URN"),
        description=_("description_urn", default="Filled in by the editorial staff"),
        required=False,
    )

    bv = schema.TextLine(
        title=_("BV Number"),
        description=_(
            "description_bv_number", default="Filled in by the editorial staff"
        ),
        required=False,
    )

    ppn = schema.TextLine(
        title=_("PPN"),
        description=_(
            "description_bv_number", default="Filled in by the editorial staff"
        ),
        required=False,
    )

    canonical_uri = schema.URI(
        title=_("Original Source URL"),
        description=_(
            "description_uri",
            default="Please fill in only after consultation with the recensio.net team",
        ),
        required=False,
    )

    # fieldset(
    #    "reviewed_text",
    #    label=_("label_schema_reviewed_text", default="Reviewed Text"),
    #    fields=[
    #        "languageReviewedText",
    #    ],
    # )

    # fieldset(
    #    "review",
    #    label=_("Review"),
    #    fields=[
    #        "reviewAuthors",
    #        "languageReview",
    #        "review",
    #        "urn",
    #        "bv",
    #        "ppn",
    #        "canonical_uri",
    #    ],
    # )


@adapter(IDexterityContent)
class Base:
    """Adapter for IBase."""

    def __init__(self, context):
        self.context = context

    @property
    def reviewAuthors(self):
        return self.context.reviewAuthors

    @reviewAuthors.setter
    def reviewAuthors(self, value):
        self.context.reviewAuthors = value

    @property
    def languageReview(self):
        return self.context.languageReview

    @languageReview.setter
    def languageReview(self, value):
        self.context.languageReview = value

    @property
    def languageReviewedText(self):
        return self.context.languageReviewedText

    @languageReviewedText.setter
    def languageReviewedText(self, value):
        self.context.languageReviewedText = value

    @property
    def recensioID(self):
        return self.context.recensioID

    @recensioID.setter
    def recensioID(self, value):
        self.context.recensioID = value

    @property
    def generatedPdf(self):
        return self.context.generatedPdf

    @generatedPdf.setter
    def generatedPdf(self, value):
        self.context.generatedPdf = value

    @property
    def review(self):
        return self.context.review

    @review.setter
    def review(self, value):
        self.context.review = value

    @property
    def urn(self):
        return self.context.urn

    @urn.setter
    def urn(self, value):
        self.context.urn = value

    @property
    def bv(self):
        return self.context.bv

    @bv.setter
    def bv(self, value):
        self.context.bv = value

    @property
    def ppn(self):
        return self.context.ppn

    @ppn.setter
    def ppn(self, value):
        self.context.ppn = value

    @property
    def canonical_uri(self):
        return self.context.canonical_uri

    @canonical_uri.setter
    def canonical_uri(self, value):
        self.context.canonical_uri = value
