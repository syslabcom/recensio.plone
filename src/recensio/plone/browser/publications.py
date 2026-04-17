from collections import OrderedDict
from DateTime import DateTime
from plone import api
from plone.memoize.view import memoize
from Products.CMFPlone.browser.defaultpage import DefaultPage
from Products.Five.browser import BrowserView
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.browser.canonical import CanonicalURLHelper
from recensio.plone.config import REVIEW_TYPES

import datetime
import string
import unicodedata

PUBLICATION_DESCENDANT_TYPES = ("Volume", "Issue") + tuple(REVIEW_TYPES)
PUBLICATION_JUMP_LETTERS = tuple(string.ascii_uppercase)
ARCHIVE_SECTION_ID = "archive"


def _render_cachekey(method, self, brain, lang):
    return (brain.getPath(), lang, DateTime().dayOfYear())


class PublicationDefaultPage(DefaultPage):
    """Translated default page"""

    def getDefaultPage(self):
        """Get the default page, if possible in the correct language.
        We expect the default page to have no language suffix (e.g. 'index').
        Translations should have a language suffix (e.g. 'index-en').
        If this fails we check the language attribute of all contained documents.
        If there is only one document with the right language we return that.
        """
        default_page = super().getDefaultPage()
        language = api.portal.get_current_language()
        defob = self.context.get(default_page)
        if not defob or defob.Language() == language:
            return default_page
        documents = self.context.listFolderContents(dict(portal_type="Document"))
        id_match = [
            item for item in documents if item.getId() == f"{default_page}-{language}"
        ]
        if len(id_match) == 1:
            return id_match[0].getId()

        language_match = [item for item in documents if item.Language() == language]
        if len(language_match) == 1:
            return language_match[0].getId()
        return default_page


class PublicationSummaryMixin:
    def format_effective_date(self, date_string):
        """Format the publication date for compact display."""
        if not date_string or date_string == "None":
            return ""
        date = DateTime(date_string)
        return f"{date.year()}-{date.month():02d}-{date.day():02d}"

    def _publication_stats(self, publication_path):
        descendants = api.content.find(
            path={"query": publication_path, "depth": 3},
            portal_type=PUBLICATION_DESCENDANT_TYPES,
            review_state="published",
            sort_on="effective",
            sort_order="reverse",
        )
        stats = {
            "volume_count": 0,
            "issue_count": 0,
            "review_count": 0,
            "latest_review_date": "",
        }
        for descendant in descendants:
            if descendant.portal_type == "Volume":
                stats["volume_count"] += 1
            elif descendant.portal_type == "Issue":
                stats["issue_count"] += 1
            elif descendant.portal_type in REVIEW_TYPES:
                stats["review_count"] += 1
                if not stats["latest_review_date"]:
                    stats["latest_review_date"] = self.format_effective_date(
                        descendant.EffectiveDate
                    )
        return stats

    def _publication_logo_url(self, publication):
        if not publication:
            publication = self.context
        if "logo" not in publication.objectIds():
            return None
        return f"{publication.absolute_url()}/logo/@@images/image/thumb"

    def _publication_letter(self, title):
        """Return the A-Z jump target for a publication title."""
        for character in (title or "").strip():
            if character.isdigit():
                return "#"
            normalized = unicodedata.normalize("NFKD", character)
            normalized = normalized.encode("ascii", "ignore").decode("ascii")
            if normalized and normalized[0].isalpha():
                return normalized[0].upper()
        return "#"


class PublicationDocumentView(PublicationSummaryMixin, BrowserView):
    """Compact document view for publication profile pages."""

    @property
    @memoize
    def publication(self):
        return IParentGetter(self.context).get_parent_object_of_type("Publication")

    @property
    @memoize
    def publication_stats(self):
        publication = self.publication
        if publication is None:
            return {
                "volume_count": 0,
                "issue_count": 0,
                "review_count": 0,
                "latest_review_date": "",
            }
        publication_path = "/".join(publication.getPhysicalPath())
        return self._publication_stats(publication_path)

    @property
    def show_jump_to_listing(self):
        publication = self.publication
        stats = self.publication_stats
        return publication is not None and any(
            stats[key] for key in ("volume_count", "issue_count", "review_count")
        )

    @property
    def publication_logo_url(self):
        return self._publication_logo_url(self.publication)

    def publication_initial(self):
        return self._publication_letter(self.publication.title)


class PublicationsView(PublicationSummaryMixin, BrowserView, CanonicalURLHelper):
    """Overview page of publications."""

    def publication_logo_url(self, publication):
        return self._publication_logo_url(publication)

    def get_publication_stats(self, publication_brain):
        publication_path = "/".join(publication_brain.getPhysicalPath())
        return self._publication_stats(publication_path)

    def _section_anchor(self, label):
        suffix = "other" if label == "#" else label.lower()
        return f"publication-section-{suffix}"

    @property
    def show_archive(self):
        return self.request.get("show") == ARCHIVE_SECTION_ID

    @memoize
    def archived_publications(self):
        pubs = api.content.find(
            path="/".join(self.context.getPhysicalPath()),
            portal_type="Publication",
            sort_on="sortable_title",
            review_state="published",
            expires={"query": datetime.datetime.now(), "range": "max"},
            show_inactive=True,
        )
        return pubs

    @memoize
    def publications(self):
        pubs = api.content.find(
            path="/".join(self.context.getPhysicalPath()),
            portal_type="Publication",
            sort_on="sortable_title",
            review_state="published",
            expires={"query": datetime.datetime.now(), "range": "min"},
        )
        return pubs

    def publication_sections(self):
        grouped = OrderedDict((label, []) for label in PUBLICATION_JUMP_LETTERS)
        grouped["#"] = []
        if self.show_archive:
            pubs = self.archived_publications()
        else:
            pubs = self.publications()

        for publication in pubs:
            grouped[self._publication_letter(publication.Title)].append(publication)
        return [
            {
                "label": label,
                "anchor": self._section_anchor(label),
                "publications": publications,
            }
            for label, publications in grouped.items()
            if publications
        ]

    @property
    def archive_url(self):
        base = self.request["ACTUAL_URL"]
        if self.show_archive:
            return base
        return f"{base}?show={ARCHIVE_SECTION_ID}"

    @property
    def active_url(self):
        return self.request["ACTUAL_URL"]

    @property
    def has_archived_publications(self):
        return bool(self.archived_publications())

    @memoize
    def publication_jump_links(self):
        available_sections = {
            section["label"]: section["anchor"]
            for section in self.publication_sections()
        }
        labels = list(PUBLICATION_JUMP_LETTERS)
        if "#" in available_sections:
            labels.append("#")
        return [
            {
                "label": label,
                "anchor": available_sections.get(label),
                "enabled": label in available_sections,
            }
            for label in labels
        ]

    def __call__(self):
        # XXX: Restore this commented code
        # canonical_url = self.get_canonical_url()
        # if (
        #     not self.request["HTTP_HOST"].startswith("admin.")
        #     and canonical_url != self.request["ACTUAL_URL"]
        # ):
        #     return self.request.response.redirect(canonical_url, status=301)
        return super().__call__()


class EnsureCanonical(BrowserView, CanonicalURLHelper):
    def __call__(self):
        canonical_url = self.get_canonical_url()
        if (
            not self.request["HTTP_HOST"].startswith("admin.")
            and canonical_url != self.request["ACTUAL_URL"]
        ):
            return self.request.response.redirect(canonical_url, status=301)
        # XXX The old code was doing this:
        # return self.context()
        # But on object that have this view set has default view, this
        # turns out to be an infinite recursion.
        # So we do this instead:
        return api.content.get_view("view", self.context, self.request)()
