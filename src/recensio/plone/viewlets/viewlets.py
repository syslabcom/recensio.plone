from DateTime import DateTime
from functools import cached_property
from plone import api
from plone.app.layout.viewlets import ViewletBase
from plone.memoize import ram
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from recensio.plone.adapter.indexer import listAuthorsAndEditors
from recensio.plone.adapter.parentgetter import ParentGetter
from recensio.plone.config import REVIEW_TYPES
from zope.interface import implementer
from zope.viewlet.interfaces import IViewlet
from ZTUtils import make_query

import logging


log = logging.getLogger(__name__)


def _publication_cachekey(method, self):
    portal_membership = getToolByName(self.context, "portal_membership")
    member = portal_membership.getAuthenticatedMember()
    roles = member.getRolesInContext(self.context)
    today = DateTime().strftime("%Y-%m-%d")
    publication = self.publication
    publication_url = publication.absolute_url() if publication else ""
    return (publication_url, roles, today)


def _container_cachekey(method, self, container_uid):
    return _publication_cachekey(method, self) + (container_uid,)


class PublicationListingMixin:
    review_types = REVIEW_TYPES

    @cached_property
    def publication(self):
        return ParentGetter(self.context).get_parent_object_of_type("Publication")

    @property
    def publication_path(self):
        publication = self.publication
        if publication is None:
            return ""
        return "/".join(publication.getPhysicalPath())

    def _container_load_url(self, uid):
        if not self.publication:
            return ""
        return f"{self.publication.absolute_url()}/@@publicationlisting-children?{make_query(container_uid=uid)}"

    def inject_options(self, panel_id):
        return (
            "trigger: autoload-visible; "
            "target: #{panel}; "
            "source: #{panel}; "
            "delay: 0; "
            "loading-class: publicationlisting-card__panel--loading"
        ).format(panel=panel_id)

    def _container_by_uid(self, container_uid, expected_portal_type=None):
        if not container_uid or not self.publication_path:
            return None
        portal_type = expected_portal_type or ["Volume", "Issue"]
        brains = api.content.find(
            UID=container_uid,
            path=self.publication_path,
            portal_type=portal_type,
        )
        if not brains:
            return None
        try:
            return brains[0].getObject()
        except AttributeError:
            log.exception(
                "Could not resolve publication listing container for UID %s",
                container_uid,
            )
            return None

    def _format_effective_date(self, date_string):
        if not date_string or date_string == "None":
            return ""
        date = DateTime(date_string)
        return f"{date.year()}-{date.month():02d}-{date.day():02d}"

    def _pdf_data(self, obj):
        if "issue.pdf" not in obj.objectIds():
            return {}
        return {
            "pdf": obj["issue.pdf"].absolute_url_path(),
            "pdfsize": self._formatsize(obj["issue.pdf"].file.size),
        }

    def _make_container_summary(self, obj, review_count=0, issue_count=0):
        has_children = bool(review_count or issue_count)
        summary = {
            "id": obj.getId(),
            "issue_count": issue_count,
            "load_url": has_children and self._container_load_url(obj.UID()) or "",
            "panel_id": f"publicationlisting-panel-{obj.UID()}",
            "portal_type": obj.portal_type,
            "review_count": review_count,
            "title": obj.Title(),
            "uid": obj.UID(),
            "has_children": has_children,
        }
        summary.update(self._pdf_data(obj))
        return summary

    @ram.cache(_publication_cachekey)
    def _volume_issue_counts(self):
        counts = {}
        if not self.publication:
            return counts
        issue_brains = api.content.find(
            context=self.publication,
            depth=2,
            portal_type="Issue",
        )
        for brain in issue_brains:
            volume_path = "/".join(brain.getPath().split("/")[:-1])
            counts[volume_path] = counts.get(volume_path, 0) + 1
        return counts

    @ram.cache(_publication_cachekey)
    def _volume_review_counts(self):
        counts = {}
        publication_path = self.publication_path
        if not publication_path:
            return counts
        review_brains = api.content.find(
            context=self.publication,
            depth=3,
            portal_type=self.review_types,
        )
        for brain in review_brains:
            relative_path = brain.getPath()[len(publication_path) + 1 :]
            if not relative_path:
                continue
            volume_id = relative_path.split("/", 1)[0]
            volume_path = f"{publication_path}/{volume_id}"
            counts[volume_path] = counts.get(volume_path, 0) + 1
        return counts

    @ram.cache(_publication_cachekey)
    def volumes(self):
        if not self.publication:
            return []
        issue_counts = self._volume_issue_counts()
        review_counts = self._volume_review_counts()
        volume_brains = api.content.find(
            context=self.publication,
            depth=1,
            portal_type="Volume",
            sort_on="effective",
            sort_order="descending",
        )
        return [
            self._make_container_summary(
                brain.getObject(),
                issue_count=issue_counts.get(brain.getPath(), 0),
                review_count=review_counts.get(brain.getPath(), 0),
            )
            for brain in volume_brains
        ]

    @ram.cache(_container_cachekey)
    def _issue_summaries(self, container_uid):
        volume = self._container_by_uid(container_uid, expected_portal_type="Volume")
        if volume is None:
            return []
        volume_path = "/".join(volume.getPhysicalPath())
        review_counts = {}
        review_brains = api.content.find(
            context=volume,
            depth=2,
            portal_type=self.review_types,
        )
        for brain in review_brains:
            parent_path = "/".join(brain.getPath().split("/")[:-1])
            if parent_path == volume_path:
                continue
            review_counts[parent_path] = review_counts.get(parent_path, 0) + 1

        issue_brains = api.content.find(
            context=volume,
            depth=1,
            portal_type="Issue",
            sort_on="effective",
            sort_order="descending",
        )
        return [
            self._make_container_summary(
                brain.getObject(),
                review_count=review_counts.get(brain.getPath(), 0),
            )
            for brain in issue_brains
        ]

    @ram.cache(_container_cachekey)
    def _review_items(self, container_uid):
        container = self._container_by_uid(container_uid)
        if container is None:
            return []
        review_brains = api.content.find(
            context=container,
            depth=1,
            portal_type=self.review_types,
            sort_on="effective",
            sort_order="descending",
        )
        items = []
        for brain in review_brains:
            try:
                obj = brain.getObject()
            except AttributeError:
                log.exception(
                    "Could not resolve publication listing review for path %s",
                    brain.getPath(),
                )
                continue
            review_view = api.content.get_view(
                context=obj,
                request=self.request,
                name="review_view",
            )
            items.append(
                {
                    "authors": " / ".join(listAuthorsAndEditors(obj)()),
                    "effective_date": self._format_effective_date(brain.EffectiveDate),
                    "title": review_view.getDecoratedTitle(),
                    "url": brain.getURL(),
                }
            )
        return items

    def _formatsize(self, size):
        size_kb = size / 1024
        display_size_kb = f"{size_kb:n} kB" if size_kb > 0 else ""
        if display_size_kb:
            display_size_bytes = f" ({size:n} bytes)"
        else:
            display_size_bytes = f"{size:n} bytes"
        display_size = f"{display_size_kb}{display_size_bytes}"
        return display_size


@implementer(IViewlet)
class Publicationlisting(PublicationListingMixin, ViewletBase):
    """Lists Volumes/Issues/Reviews in the current Publication."""

    def visible(self):
        return (
            getattr(self.context, "portal_type", None) == "Document"
            and self.publication is not None
        )


class PublicationListingChildren(PublicationListingMixin, BrowserView):
    """Lazy loads volume and issue contents for the publication listing."""

    @property
    def container_uid(self):
        return self.request.form.get("container_uid", "")

    @property
    def panel_id(self):
        if not self.container_uid:
            return ""
        return f"publicationlisting-panel-{self.container_uid}"

    @cached_property
    def listing_container(self):
        return self._container_by_uid(self.container_uid)

    @property
    def issues(self):
        container = self.listing_container
        if container is None or container.portal_type != "Volume":
            return []
        return self._issue_summaries(self.container_uid)

    @property
    def reviews(self):
        if self.listing_container is None:
            return []
        return self._review_items(self.container_uid)

    def __call__(self):
        if self.listing_container is None:
            self.request.response.setStatus(404)
            return ""
        return super().__call__()
