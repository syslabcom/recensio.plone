from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_edited_volume
from recensio.plone.behaviors.directives import fieldset_reviewed_text
from zope import schema
from zope.component import adapter
from zope.interface import provider


@provider(IFormFieldProvider)
class ISerial(model.Schema):
    directives.order_after(series="IPrintedReview.publisherOnline")
    series = schema.TextLine(
        title=_("Series"),
        required=False,
    )

    directives.order_after(seriesVol="ISerial.series")
    seriesVol = schema.TextLine(
        title=_("Series (vol.)"),
        required=False,
    )

    directives.order_after(pages="ISerial.seriesVol")
    pages = schema.TextLine(
        title=_("Pages"),
        required=False,
    )
    # customizations
    fieldset_reviewed_text(["series", "seriesVol", "pages"])


@provider(IFormFieldProvider)
class ISerialEditedVolume(model.Schema):
    directives.order_after(series="IPrintedReview.publisherOnline")
    series = schema.TextLine(
        title=_("Series"),
        required=False,
    )

    directives.order_after(seriesVol="ISerial.series")
    seriesVol = schema.TextLine(
        title=_("Series (vol.)"),
        required=False,
    )

    directives.order_after(pages="ISerial.seriesVol")
    pages = schema.TextLine(
        title=_("Pages"),
        required=False,
    )
    # customizations
    fieldset_edited_volume(["series", "seriesVol", "pages"])


@adapter(IDexterityContent)
class Serial:
    """Adapter for ISeries."""

    def __init__(self, context):
        self.context = context

    @property
    def series(self):
        return self.context.series

    @series.setter
    def series(self, value):
        self.context.series = value

    @property
    def seriesVol(self):
        return self.context.seriesVol

    @seriesVol.setter
    def seriesVol(self, value):
        self.context.seriesVol = value

    @property
    def pages(self):
        return self.context.pages

    @pages.setter
    def pages(self, value):
        self.context.pages = value
