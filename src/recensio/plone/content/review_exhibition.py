from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow
from plone import api
from plone.app.vocabularies.catalog import CatalogSource
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform.directives import widget
from plone.dexterity.content import Item
from plone.supermodel import model
from recensio.plone import _
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.directives import fieldset_exhibition
from recensio.plone.interfaces import IReview
from recensio.plone.utils import get_formatted_names
from recensio.plone.utils import getFormatter
from recensio.plone.utils import punctuated_title_and_subtitle
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import interface
from zope import schema
from zope.interface import implementer


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


class IReviewExhibition(model.Schema):
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


@implementer(IReviewExhibition, IReview)
class ReviewExhibition(Item):
    """Content-type class for IReviewExhibition."""

    # A ordered list of fields used for the metadata area of the view.
    metadata_fields = [
        "metadata_review_type_code",
        "get_journal_title",
        "metadata_start_end_pages",
        "metadata_review_author",
        "languageReview",
        "languageReviewedText",
        "exhibiting_institution",
        "exhibiting_organisation",
        "curators",
        "titleProxy",
        "subtitle",
        "dates",
        "url_exhibition",
        "doi_exhibition",
        "ddcSubject",
        "ddcTime",
        "ddcPlace",
        "subject",
        "canonical_uri",
        "urn",
        "effectiveDate",
        "metadata_recensioID",
        "doi",
    ]

    @property
    def exhibitor(self):
        exhibitor = " / ".join(
            [
                institution["name"].strip()
                for institution in self.exhibiting_institution
                if institution["name"]
            ]
        )
        if exhibitor:
            return exhibitor
        exhibitor = " / ".join(
            [
                organisation["name"].strip()
                for organisation in self.exhibiting_organisation
                if organisation["name"]
            ]
        )
        if exhibitor:
            return exhibitor
        exhibitor = get_formatted_names(
            [
                person.to_object
                for person in self.curators
                if person.firstname or person.lastname
            ],
        )
        return exhibitor

    def getDecoratedTitle(self):
        dates_formatter = getFormatter(", ")
        dates_string = " / ".join(
            [dates_formatter(date["place"], date["runtime"]) for date in self.dates]
        )

        permanent_exhib_string = api.portal.translate(
            _("Dauerausstellung", default="Permanent Exhibition")
        )
        title_string = getFormatter(". ")(
            punctuated_title_and_subtitle(self),
            permanent_exhib_string if self.isPermanentExhibition else "",
        )

        full_title = getFormatter(": ", ", ", " ")

        def message_callback(reviewers_formatted):
            return _(
                "exhibition_reviewed_by",
                default="Exhibition reviewed by ${review_authors}",
                mapping={"review_authors": reviewers_formatted},
            )

        reviewer_string = IBase(self).get_formatted_review_authors(
            message_callback=message_callback
        )
        return full_title(
            self.exhibitor,
            title_string,
            dates_string,
            reviewer_string,
        )
