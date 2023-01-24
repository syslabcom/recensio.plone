from plone.app.dexterity import textindexer
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class IPrintedReview(model.Schema):
    heading_presented_work = schema.TextLine(
        title=_("heading_presented_work", default=("Information on presented work")),
        required=False,
    )
    directives.mode(heading_presented_work="display")

    subtitle = schema.TextLine(
        title=_("Subtitle"),
        required=False,
    )

    yearOfPublication = schema.TextLine(
        title=_("Year of publication"),
        required=False,
    )

    placeOfPublication = schema.TextLine(
        title=_("Place of publication"),
        required=False,
    )

    publisher = schema.TextLine(
        title=_("Publisher"),
        required=False,
    )
    textindexer.searchable("publisher")

    yearOfPublicationOnline = schema.TextLine(
        title=_("Year of publication (Online)"),
        required=False,
    )

    placeOfPublicationOnline = schema.TextLine(
        title=_("Place of publication (Online)"),
        required=False,
    )

    publisherOnline = schema.TextLine(
        title=_("Publisher (Online)"),
        required=False,
    )
    textindexer.searchable("publisherOnline")

    idBvb = schema.TextLine(
        title="idBvb",
        required=False,
    )
    directives.omitted("idBvb")

    model.fieldset(
        "reviewed_text",
        label=_("label_schema_reviewed_text", default="Reviewed Text"),
        fields=[
            "heading_presented_work",
            "subtitle",
            "yearOfPublication",
            "placeOfPublication",
            "publisher",
            "yearOfPublicationOnline",
            "placeOfPublicationOnline",
            "publisherOnline",
            "idBvb",
        ],
    )


@adapter(IDexterityContent)
class PrintedReview:
    """Adapter for IPrintedReview."""

    def __init__(self, context):
        self.context = context

    @property
    def heading_presented_work(self):
        return ""

    @heading_presented_work.setter
    def heading_presented_work(self, value):
        pass

    @property
    def subtitle(self):
        return self.context.subtitle

    @subtitle.setter
    def subtitle(self, value):
        self.context.subtitle = value

    @property
    def yearOfPublication(self):
        return self.context.yearOfPublication

    @yearOfPublication.setter
    def yearOfPublication(self, value):
        self.context.yearOfPublication = value

    @property
    def placeOfPublication(self):
        return self.context.placeOfPublication

    @placeOfPublication.setter
    def placeOfPublication(self, value):
        self.context.placeOfPublication = value

    @property
    def publisher(self):
        return self.context.publisher

    @publisher.setter
    def publisher(self, value):
        self.context.publisher = value

    @property
    def yearOfPublicationOnline(self):
        return self.context.yearOfPublicationOnline

    @yearOfPublicationOnline.setter
    def yearOfPublicationOnline(self, value):
        self.context.yearOfPublicationOnline = value

    @property
    def placeOfPublicationOnline(self):
        return self.context.placeOfPublicationOnline

    @placeOfPublicationOnline.setter
    def placeOfPublicationOnline(self, value):
        self.context.placeOfPublicationOnline = value

    @property
    def publisherOnline(self):
        return self.context.publisherOnline

    @publisherOnline.setter
    def publisherOnline(self, value):
        self.context.publisherOnline = value

    @property
    def idBvb(self):
        return self.context.idBvb

    @idBvb.setter
    def idBvb(self, value):
        self.context.idBvb = value
