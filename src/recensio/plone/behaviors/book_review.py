from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone.app.dexterity import textindexer
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import Interface
from zope.interface import provider


class IAdditionalTitleRowSchema(Interface):
    """Schema for a row in the datagridfield"""

    title = schema.TextLine(title=_("Title"), required=False)
    subtitle = schema.TextLine(title=_("Subtitle"), required=False)


@provider(IFormFieldProvider)
class IBookReview(model.Schema):

    additionalTitles = schema.List(
        title=_("Paralleltitel (andere Sprachen)"),
        value_type=DictRow(schema=IAdditionalTitleRowSchema, required=False),
        required=False,
        defaultFactory=list,
    )
    directives.widget(additionalTitles=DataGridFieldFactory)
    textindexer.searchable("additionalTitles")

    isbn = schema.TextLine(
        title=_("ISBN"),
        description=_(
            "description_isbn",
            default=(
                "With or without hyphens. In case of several numbers please "
                "choose the hard cover edition."
            ),
        ),
        required=False,
    )

    isbn_online = schema.TextLine(
        title=_("ISBN (Online)"),
        description=_(
            "description_isbn_online",
            default=(
                "With or without hyphens. In case of several numbers please "
                "choose the hard cover edition."
            ),
        ),
        required=False,
    )

    url_monograph = schema.TextLine(
        title=_("URL (Monographie)"),
        required=False,
    )

    urn_monograph = schema.TextLine(
        title=_("URN (Monographie)"),
        required=False,
    )

    doi_monograph = schema.TextLine(
        title=_("DOI (Monographie)"),
        required=False,
    )


@adapter(IDexterityContent)
class BookReview:
    """Adapter for IBookReview"""

    def __init__(self, context):
        self.context = context

    @property
    def additionalTitles(self):
        return self.context.additionalTitles

    @additionalTitles.setter
    def additionalTitles(self, value):
        self.context.additionalTitles = value

    @property
    def isbn(self):
        return self.context.isbn

    @isbn.setter
    def isbn(self, value):
        self.context.isbn = value

    @property
    def isbn_online(self):
        return self.context.isbn_online

    @isbn_online.setter
    def isbn_online(self, value):
        self.context.isbn_online = value

    @property
    def url_monograph(self):
        return self.context.url_monograph

    @url_monograph.setter
    def url_monograph(self, value):
        self.context.url_monograph = value

    @property
    def urn_monograph(self):
        return self.context.urn_monograph

    @urn_monograph.setter
    def urn_monograph(self, value):
        self.context.urn_monograph = value

    @property
    def doi_monograph(self):
        return self.context.doi_monograph

    @doi_monograph.setter
    def doi_monograph(self, value):
        self.context.doi_monograph = value
