#!/usr/bin/python
from datetime import datetime
from plone.memoize import instance
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from recensio.plone.browser.helper import CrossPlatformMixin
from string import ascii_uppercase

import logging


logger = logging.getLogger(__name__)


def _render_cachekey(_, self):
    hour = datetime.now().strftime("%Y-%m-%d:%H")
    b_start = self.request.get("b_start", "0")
    letter = self.request.get("letter")
    use_navigation_root = self.request.get("use_navigation_root", True)
    navigation_root = getNavigationRoot(self.context)
    return (b_start, letter, hour, use_navigation_root, navigation_root)


class AuthorSearchView(BrowserView, CrossPlatformMixin):
    """Dynamic elements on the homepage."""

    template = ViewPageTemplateFile("templates/authorsearch.pt")
    ALPHABET = ascii_uppercase

    def __call__(self):
        self.request.set("disable_border", True)
        return self.template(self)

    @property
    @instance.memoize
    def authors(self):
        catalog = getToolByName(self.context, "portal_catalog")
        author_string = safe_unicode(self.request.get("authors"))
        b_start = int(self.request.get("b_start", 0))
        b_size = int(self.request.get("b_size", 30))
        query = {
            "portal_type": "Person",
            "b_start": b_start,
            "b_size": b_size,
            "sort_on": "sortable_title",
            "fl": "Title,UID,path_string",
        }
        navigation_root = getNavigationRoot(self.context)
        if self.request.get("use_navigation_root", True):
            query["path"] = navigation_root
        if author_string:
            query["SearchableText"] = author_string.strip("\"'")
        return catalog(query)

    @property
    def portal_title(self):
        return getToolByName(self.context, "portal_url").getPortalObject().Title()
