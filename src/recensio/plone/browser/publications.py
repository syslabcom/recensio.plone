import string
import unicodedata
from collections import OrderedDict

from DateTime import DateTime
from Products.CMFPlone.browser.defaultpage import DefaultPage
from Products.Five.browser import BrowserView
from recensio.plone.adapter.parentgetter import ParentGetter
from recensio.plone.browser.canonical import CanonicalURLHelper
from recensio.plone.config import REVIEW_TYPES

from plone import api
from plone.memoize import ram
from plone.memoize.view import memoize

PUBLICATION_DESCENDANT_TYPES = ("Volume", "Issue") + tuple(REVIEW_TYPES)
PUBLICATION_JUMP_LETTERS = tuple(string.ascii_uppercase)


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
        return "%s-%02d-%02d" % (date.year(), date.month(), date.day())

    def _publication_stats(self, publication_path):
        descendants = self.context.portal_catalog(
            path={"query": publication_path, "depth": 3},
            portal_type=PUBLICATION_DESCENDANT_TYPES,
            review_state="published",
            sort_on="effective",
            sort_order="reverse",
        )
        stats = dict(
            volume_count=0,
            issue_count=0,
            review_count=0,
            latest_review_date="",
        )
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


class PublicationDocumentView(PublicationSummaryMixin, BrowserView):
    """Compact document view for publication profile pages."""

    @property
    @memoize
    def publication(self):
        return ParentGetter(self.context).get_parent_object_of_type("Publication")

    @property
    @memoize
    def publication_stats(self):
        publication = self.publication
        if publication is None:
            return dict(
                volume_count=0,
                issue_count=0,
                review_count=0,
                latest_review_date="",
            )
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
        publication = self.publication
        if publication is None or "logo" not in publication.objectIds():
            return None
        return f"{publication.absolute_url()}/logo/@@images/image/thumb"

    @property
    def publication_initial(self):
        title = self.publication and self.publication.Title() or self.context.Title()
        for character in (title or "").strip():
            if character.isalnum():
                normalized = unicodedata.normalize("NFKD", character)
                normalized = normalized.encode("ascii", "ignore").decode("ascii")
                if normalized:
                    return normalized[0].upper()
        return "P"


class PublicationsView(PublicationSummaryMixin, BrowserView, CanonicalURLHelper):
    """Overview page of publications."""

    def format_effective_date(self, date_string):
        """Format the publication date for compact display."""
        if not date_string or date_string == "None":
            return ""
        date = DateTime(date_string)
        return "%s-%02d-%02d" % (date.year(), date.month(), date.day())

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

    def _section_anchor(self, label):
        suffix = "other" if label == "#" else label.lower()
        return f"publication-section-{suffix}"

    def _publication_stats(self, publication_path):
        descendants = self.context.portal_catalog(
            path={"query": publication_path, "depth": 3},
            portal_type=PUBLICATION_DESCENDANT_TYPES,
            review_state="published",
            sort_on="effective",
            sort_order="reverse",
        )
        stats = dict(
            volume_count=0,
            issue_count=0,
            review_count=0,
            latest_review_date="",
        )
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

    @ram.cache(_render_cachekey)
    def brain_to_pub(self, brain, lang):
        pubob = brain.getObject()
        has_logo = "logo" in pubob.objectIds()
        if pubob.getDefaultPage():
            default_page = api.content.get_view(
                context=pubob,
                request=self.request,
                name="default_page",
            ).getDefaultPage()
            defob = getattr(pubob, default_page, None) or pubob
        else:
            defob = pubob
        title = defob and defob.Title() != "" and defob.Title() or pubob.Title()
        desc = (defob and defob.Description() or pubob.Description() or "").strip()
        path = defob and "/".join(defob.getPhysicalPath()) or ""
        info = dict(
            title=title,
            desc=desc,
            has_logo=has_logo,
            path=path,
            initial=self._publication_letter(title),
        )
        info.update(self._publication_stats(brain.getPath()))
        return info

    @memoize
    def publications(self):
        pc = self.context.portal_catalog
        publist = []
        currlang = api.portal.get_current_language()
        pubs = pc(
            portal_type="Publication",
            path="/".join(self.context.getPhysicalPath()),
            sort_on="sortable_title",
            review_state="published",
        )
        for pub in pubs:
            info = self.brain_to_pub(pub, currlang).copy()
            info["logo"] = (
                f"{pub.getURL()}/logo/@@images/image/thumb"
                if info["has_logo"]
                else None
            )
            info["link"] = self.request.physicalPathToURL(info["path"])
            publist.append(info)
        return publist

    @memoize
    def publication_sections(self):
        grouped = OrderedDict((label, []) for label in PUBLICATION_JUMP_LETTERS)
        grouped["#"] = []
        for publication in self.publications():
            grouped[publication["initial"]].append(publication)
        return [
            dict(
                label=label,
                anchor=self._section_anchor(label),
                publications=publications,
            )
            for label, publications in grouped.items()
            if publications
        ]

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
            dict(
                label=label,
                anchor=available_sections.get(label),
                enabled=label in available_sections,
            )
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
