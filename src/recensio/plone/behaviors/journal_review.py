from plone.app.dexterity import textindexer
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
class IJournalReview(model.Schema):
    textindexer.searchable("issn")
    issn = schema.TextLine(
        title=_("ISSN"),
        description=_(
            "description_issn",
            default=("With or without hyphens."),
        ),
        required=False,
    )

    textindexer.searchable("issn_online")
    issn_online = schema.TextLine(
        title=_("ISSN Online"),
        description=_(
            "description_issn_online",
            default=("With or without hyphens."),
        ),
        required=False,
    )

    url_journal = schema.TextLine(
        title=_("URL (Zeitschrift)"),
        required=False,
    )

    urn_journal = schema.TextLine(
        title=_("URN (Zeitschrift)"),
        required=False,
    )

    doi_journal = schema.TextLine(
        title=_("DOI (Zeitschrift)"),
        required=False,
    )

    directives.order_after(shortnameJournal="translatedTitleJournal")
    shortnameJournal = schema.TextLine(
        title=_("Shortname"),
        required=False,
    )

    officialYearOfPublication = schema.TextLine(
        title=_("Official year of publication (if different)"),
        required=False,
    )

    volumeNumber = schema.TextLine(
        title=_("Vol."),
        required=False,
    )

    issueNumber = schema.TextLine(
        title=_("Number"),
        required=False,
    )
    # customizations
    directives.order_after(issueNumber="IPrintedReview.yearOfPublication")
    directives.order_after(volumeNumber="IPrintedReview.yearOfPublication")
    directives.order_after(officialYearOfPublication="IPrintedReview.yearOfPublication")
    fieldset_reviewed_text(
        [
            "issn",
            "issn_online",
            "url_journal",
            "urn_journal",
            "doi_journal",
            "shortnameJournal",
            "volumeNumber",
            "issueNumber",
            "officialYearOfPublication",
        ],
    )


@provider(IFormFieldProvider)
class IJournalArticleReview(model.Schema):
    textindexer.searchable("issn")
    issn = schema.TextLine(
        title=_("ISSN"),
        description=_(
            "description_issn",
            default=("With or without hyphens."),
        ),
        required=False,
    )

    textindexer.searchable("issn_online")
    issn_online = schema.TextLine(
        title=_("ISSN Online"),
        description=_(
            "description_issn_online",
            default=("With or without hyphens."),
        ),
        required=False,
    )

    url_journal = schema.TextLine(
        title=_("URL (Zeitschrift)"),
        required=False,
    )

    urn_journal = schema.TextLine(
        title=_("URN (Zeitschrift)"),
        required=False,
    )

    doi_journal = schema.TextLine(
        title=_("DOI (Zeitschrift)"),
        required=False,
    )

    directives.order_after(shortnameJournal="translatedTitleJournal")
    shortnameJournal = schema.TextLine(
        title=_("Shortname"),
        required=False,
    )

    volumeNumber = schema.TextLine(
        title=_("Vol."),
        required=False,
    )

    issueNumber = schema.TextLine(
        title=_("Number"),
        required=False,
    )

    officialYearOfPublication = schema.TextLine(
        title=_("Official year of publication (if different)"),
        required=False,
    )
    # customizations
    directives.order_after(
        officialYearOfPublication="IPrintedReviewEditedVolume.yearOfPublication"
    )
    directives.order_after(
        volumeNumber="IJournalArticleReview.officialYearOfPublication"
    )
    directives.order_after(issueNumber="IJournalArticleReview.volumeNumber")
    fieldset_edited_volume(
        [
            "issn",
            "issn_online",
            "url_journal",
            "urn_journal",
            "doi_journal",
            "shortnameJournal",
            "volumeNumber",
            "issueNumber",
            "officialYearOfPublication",
        ],
    )


@adapter(IDexterityContent)
class JournalReview:
    """Adapter for IJournalReview."""

    def __init__(self, context):
        self.context = context

    @property
    def issn(self):
        return self.context.issn

    @issn.setter
    def issn(self, value):
        self.context.issn = value

    @property
    def issn_online(self):
        return self.context.issn_online

    @issn_online.setter
    def issn_online(self, value):
        self.context.issn_online = value

    @property
    def url_journal(self):
        return self.context.url_journal

    @url_journal.setter
    def url_journal(self, value):
        self.context.url_journal = value

    @property
    def urn_journal(self):
        return self.context.urn_journal

    @urn_journal.setter
    def urn_journal(self, value):
        self.context.urn_journal = value

    @property
    def doi_journal(self):
        return self.context.doi_journal

    @doi_journal.setter
    def doi_journal(self, value):
        self.context.doi_journal = value

    @property
    def shortnameJournal(self):
        return self.context.shortnameJournal

    @shortnameJournal.setter
    def shortnameJournal(self, value):
        self.context.shortnameJournal = value

    @property
    def volumeNumber(self):
        return self.context.volumeNumber

    @volumeNumber.setter
    def volumeNumber(self, value):
        self.context.volumeNumber = value

    @property
    def issueNumber(self):
        return self.context.issueNumber

    @issueNumber.setter
    def issueNumber(self, value):
        self.context.issueNumber = value

    @property
    def officialYearOfPublication(self):
        return self.context.officialYearOfPublication

    @officialYearOfPublication.setter
    def officialYearOfPublication(self, value):
        self.context.officialYearOfPublication = value
