from plone import api
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.utils import normalizeString
from Products.Five.browser import BrowserView
from recensio.plone import _
from recensio.plone.config import REVIEW_TYPES
from recensio.plone.utils import punctuated_title_and_subtitle
from zope.annotation.interfaces import IAnnotations
from ZTUtils import make_query


class ResultsListing(BrowserView):
    """Lists search results."""

    def normalizeString(self, text):
        return normalizeString(text)

    @property
    def portal_path(self):
        return api.portal.get().getPhysicalPath()


class ListingBase(BrowserView):
    """Base class for listing views."""

    def punctuated_title_and_subtitle(self, obj):
        return punctuated_title_and_subtitle(obj)

    @property
    def rss_url(self):
        portal_url = api.portal.get().absolute_url()
        return f"{portal_url}/search_rss?{make_query(self.query)}"

    @property
    def items(self):
        catalog = api.portal.get_tool("portal_catalog")
        results = catalog(self.query)
        IAnnotations(self.request)["recensio.query_results"] = results
        return results

    def translate(self, msgid):
        translation_service = api.portal.get_tool("translation_service")
        return translation_service.utranslate(
            msgid=msgid,
            context=self.request,
        )


class ReviewSectionsListing(ListingBase):
    @property
    def title(self):
        return self.translate(_("label_latest_review_journals"))

    @property
    def query(self):
        navigation_root = getNavigationRoot(self.context)
        query = dict(
            portal_type=["Volume", "Issue"],
            path=navigation_root,
            fq="-hide_from_listing:true",
            sort_on="effective",
            sort_order="reverse",
        )
        return query


class ReviewItemsListing(ListingBase):
    @property
    def title(self):
        return self.translate(_("label_nav_reviews"))

    @property
    def query(self):
        navigation_root = getNavigationRoot(self.context)
        query = dict(
            portal_type=REVIEW_TYPES,
            path=navigation_root,
            facet_field=["languageReview"],
            sort_on="effective",
            sort_order="reverse",
        )
        if "languageReview" in self.request:
            query["languageReview"] = self.request.get("languageReview")
        return query


class SortingMenuView(BrowserView):
    """"""

    @property
    def sort_options(self):
        return [
            {
                "title": _("Relevance"),
                "url": self._url(None),
                "current": self._current(None),
            },
            {
                "title": _("Year Of Publication Title (younger first)"),
                "url": self._url("sortable_year", reverse=True),
                "current": self._current("sortable_year", reverse=True),
            },
            {
                "title": _("Year Of Publication Title (older first)"),
                "url": self._url("sortable_year"),
                "current": self._current("sortable_year"),
            },
        ]

    def _url(self, sortkey, reverse=False):
        q = {}
        q.update(self.request.form)
        if "sort_on" in q:
            del q["sort_on"]
        if "sort_order" in q:
            del q["sort_order"]
        if sortkey:
            q["sort_on"] = sortkey
        if reverse:
            q["sort_order"] = "reverse"

        base_url = self.request.URL
        return base_url + "?" + make_query(q)

    def _current(self, sortkey, reverse=False):
        if not self.request.form.get("sort_on") and not sortkey:
            # Default case - relevance/score; ignore reverse
            return "current"
        elif self.request.form.get("sort_on") == sortkey:
            request_reverse = self.request.form.get("sort_order") == "reverse"
            if request_reverse is reverse:
                return "current"
        return ""
