from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone.app.vocabularies.catalog import CatalogSource
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform.directives import widget
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.directives import fieldset_exhibition
from recensio.plone.interfaces import IReview
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import interface
from zope import schema
from zope.interface import implementer
from zope.interface import provider


class IExhibitingInstitutionRowSchema(interface.Interface):
    name = schema.TextLine(
        title=_("Ausstellende Institution (z. B. Museum)"),
        required=False,
    )
    gnd = schema.TextLine(
        title=_("GND der Ausstellenden Institution"),
        required=False,
    )


class IYearsRowSchema(interface.Interface):
    years = schema.TextLine(
        title=_("Years"),
        required=False,
    )


class IExhibitingOrganisationRowSchema(interface.Interface):
    name = schema.TextLine(
        title=_("Ausstellende Organisation (z. B. Stiftung)"),
        required=False,
    )
    gnd = schema.TextLine(
        title=_("GND der Ausstellenden Organisation"),
        required=False,
    )


class IDatesRowSchema(interface.Interface):
    place = schema.TextLine(
        title=_("Ort"),
        required=False,
    )
    runtime = schema.TextLine(
        title=_("Laufzeit"),
        required=False,
    )


@provider(IFormFieldProvider)
class IReviewExhibition(model.Schema, IReview):
    """Marker interface and Dexterity Python Schema for ReviewExhibition."""

    subtitle = schema.TextLine(
        title=_("Subtitle"),
        required=False,
    )

    exhibiting_institution = schema.List(
        title=_("Ausstellende Institution"),
        value_type=DictRow(
            schema=IExhibitingInstitutionRowSchema,
        ),
        required=False,
    )
    widget(exhibiting_institution=DataGridFieldFactory)

    dates = schema.List(
        title=_("Ausstellung"),
        value_type=DictRow(
            schema=IDatesRowSchema,
        ),
        required=False,
    )
    widget(dates=DataGridFieldFactory)

    years = schema.List(
        title=_("Ausstellungsjahr"),
        value_type=DictRow(
            schema=IYearsRowSchema,
        ),
        required=False,
    )
    widget(years=DataGridFieldFactory)

    exhibiting_organisation = schema.List(
        title=_("Ausstellende Organisation"),
        value_type=DictRow(
            schema=IExhibitingOrganisationRowSchema,
        ),
        required=False,
    )
    widget(exhibiting_organisation=DataGridFieldFactory)

    # FIXME: This was using the custom GNDReferenceBrowserWidget
    # Use the standard RelatedItemsFieldWidget for now
    widget(
        "curators",
        RelatedItemsFieldWidget,
        pattern_options={"mode": "auto", "favorites": []},
    )
    curators = RelationList(
        title=_("Kurator / Mitwirkende"),
        defaultFactory=list,
        value_type=RelationChoice(source=CatalogSource(portal_type="Person")),
        required=False,
    )

    isPermanentExhibition = schema.Bool(
        title=_("Dauerausstellung"),
        required=False,
    )
    titleProxy = schema.TextLine(
        title=_("Title"),
        required=False,
    )
    url_exhibition = schema.TextLine(
        title=_("URL der Ausstellungswebsite"),
        required=False,
    )
    doi_exhibition = schema.TextLine(
        title=_("DOI der Ausstellungswebsite"),
        required=False,
    )

    fieldset_exhibition(
        [
            "exhibiting_institution",
            "dates",
            "years",
            "exhibiting_organisation",
            "curators",
            "isPermanentExhibition",
            "titleProxy",
            "url_exhibition",
            "doi_exhibition",
        ],
    )


@implementer(IReviewExhibition)
class ReviewExhibition(Item):
    """Content-type class for IReviewExhibition."""
