from DateTime import DateTime
from plone import api
from plone.app.layout.viewlets import ViewletBase
from plone.memoize import ram
from Products.CMFCore.utils import getToolByName
from recensio.plone.adapter.indexer import listAuthorsAndEditors
from zope.interface import implementer
from zope.viewlet.interfaces import IViewlet
from ZTUtils import make_query

import logging


log = logging.getLogger(__name__)


def _render_cachekey(method, self, volume, issue=None):
    portal_membership = getToolByName(self.context, "portal_membership")
    member = portal_membership.getAuthenticatedMember()
    roles = member.getRolesInContext(self.context)
    today = DateTime().strftime("%Y-%m-%d")
    context_url = self.context.absolute_url()
    return (context_url, roles, today, volume, issue)


def _volume_cachekey(method, self):
    portal_membership = getToolByName(self.context, "portal_membership")
    member = portal_membership.getAuthenticatedMember()
    roles = member.getRolesInContext(self.context)
    today = DateTime().strftime("%Y-%m-%d")
    parent_url = self.parent.absolute_url()
    return (parent_url, roles, today)


def _obj_cachekey(method, self, obj):
    portal_membership = getToolByName(self.context, "portal_membership")
    member = portal_membership.getAuthenticatedMember()
    roles = member.getRolesInContext(self.context)
    today = DateTime().strftime("%Y-%m-%d")
    obj_uid = obj.UID()
    return (obj_uid, roles, today)


def _issues_cachekey(method, self, volume):
    portal_membership = getToolByName(self.context, "portal_membership")
    member = portal_membership.getAuthenticatedMember()
    roles = member.getRolesInContext(self.context)
    today = DateTime().strftime("%Y-%m-%d")
    return (volume, roles, today, volume)


@implementer(IViewlet)
class Publicationlisting(ViewletBase):
    """Lists Volumes/Issues/Reviews in the current Publication"""

    def __init__(self, context, request, view, manager=None):
        super().__init__(context, request, view, manager)
        try:
            parents = self.request.PARENTS
        except AttributeError:
            return False
        if len(parents) < 2:
            return False
        self.parent = self.request.PARENTS[1]

    def visible(self):
        """should we display at all?"""
        if (
            hasattr(self.context, "portal_type")
            and self.context.portal_type == "Document"
            and hasattr(self.parent, "portal_type")
            and self.parent.portal_type == "Publication"
        ):
            return True
        return False

    def is_expanded(self, uid):
        return uid in self.request.get("expand", [])

    def _make_dict(self, obj):
        "contains the relevant details for listing a Review"
        view = api.content.get_view(
            context=obj, request=self.request, name="review_view"
        )
        return {
            "absolute_url": obj.absolute_url(),
            "effective": obj.effective(),
            "getDecoratedTitle": view.getDecoratedTitle(),
            "listAuthorsAndEditors": listAuthorsAndEditors(obj)(),
            "Title": obj.Title(),
        }

    def _get_toggle_link(self, uid):
        expand = self.request.get("expand", [])[:]
        if uid in expand:
            expand.remove(uid)
        else:
            expand.append(uid)
        toggle_link = "{}?{}#{}".format(
            self.context.absolute_url(),
            make_query(expand=expand),
            uid,
        )
        return toggle_link

    @ram.cache(_obj_cachekey)
    def _get_css_classes(self, obj):
        css_classes = []
        reviews = api.content.find(
            context=obj, portal_type=["Review Monograph", "Review Journal"], depth=1
        )
        if len(reviews) > 0:
            css_classes.append("review_container")
            if self.is_expanded(obj.UID()):
                css_classes.append("expanded")
        return " ".join(css_classes) or None

    @ram.cache(_obj_cachekey)
    def _make_iss_or_vol_dict(self, obj):
        issue_dict = {
            "Title": obj.Title(),
            "id": obj.getId(),
            "UID": obj.UID(),
            "toggle_link": self._get_toggle_link(obj.UID()),
            "css_classes": self._get_css_classes(obj),
        }

        if "issue.pdf" in obj.objectIds():
            issue_dict["pdf"] = obj["issue.pdf"].absolute_url_path()
            issue_dict["pdfsize"] = self._formatsize(obj["issue.pdf"].file.size)
        return issue_dict

    @ram.cache(_volume_cachekey)
    def volumes(self):
        # This is nasty. #3678 Decarbonize
        volume_objs = [
            brain.getObject()
            for brain in api.content.find(
                self.parent,
                depth=1,
                portal_type="Volume",
                sort_on="effective",
                sort_order="descending",
            )
        ]
        volumes = [self._make_iss_or_vol_dict(v) for v in volume_objs]
        return volumes

    @ram.cache(_issues_cachekey)
    def issues(self, volume):
        if volume not in self.parent:
            return []
        # This is nasty. #3678 Decarbonize
        objects = [
            brain.getObject()
            for brain in api.content.find(
                self.parent[volume], depth=1, portal_type="Issue"
            )
        ]
        issue_objs = sorted(objects, key=lambda v: v.effective(), reverse=True)
        issues = [self._make_iss_or_vol_dict(i) for i in issue_objs]
        return issues

    @ram.cache(_render_cachekey)
    def reviews(self, volume, issue=None):
        if volume not in self.parent.objectIds():
            return []
        if issue is None:
            # This is nasty. #3678 Decarbonize
            review_objs = [
                brain.getObject()
                for brain in api.content.find(
                    self.parent[volume],
                    depth=1,
                    portal_type=["Review Monograph", "Review Journal"],
                )
            ]
        else:
            if issue not in self.parent[volume].objectIds():
                return []
            # This is nasty. #3678 Decarbonize
            review_objs = [
                brain.getObject()
                for brain in api.content.find(
                    self.parent[volume][issue],
                    depth=1,
                    portal_type=["Review Monograph", "Review Journal"],
                )
            ]
        reviews = [self._make_dict(rev) for rev in review_objs]
        reviews = sorted(
            reviews, key=lambda r: r["listAuthorsAndEditors"], reverse=True
        )
        return reviews

    def _formatsize(self, size):
        size_kb = size / 1024
        display_size_kb = f"{size_kb:n} kB" if size_kb > 0 else ""
        if display_size_kb:
            display_size_bytes = f" ({size:n} bytes)"
        else:
            display_size_bytes = f"{size:n} bytes"
        display_size = f"{display_size_kb}{display_size_bytes}"
        return display_size
