#!/usr/bin/python
from datetime import datetime
from plone.memoize import instance
from plone.memoize import ram
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

    @ram.cache(_render_cachekey)
    def get_b_start(self):
        b_start = int(self.request.get("b_start", 0))
        if b_start:
            return b_start
        else:
            letter = self.request.get("letter")
            if not letter:
                return 0
            # XXX this is way too clever
            letter = letter.lower()
            catalog = getToolByName(self.context, "portal_catalog")
            query = {
                "portal_type": "Person",
                "b_start": 0,
                "b_size": int(self.request.get("b_size", 30)),
                "sort_on": "sortable_title",
                "fl": "Title",
            }
            navigation_root = getNavigationRoot(self.context)
            if self.request.get("use_navigation_root", True):
                query["path"] = navigation_root
            num_authors = len(catalog(query))
            if num_authors == 0:
                return 0
            b_size = 30
            query["b_size"] = b_size + 1
            partition = [0, num_authors]
            sample_idx = 0
            while True:
                sample_start = max(
                    partition[0] + (partition[1] - partition[0]) / 2,
                    0,
                )
                sample_start = int(sample_start / b_size) * b_size
                query["b_start"] = max(sample_start - 1, 0)
                sample = catalog(query)
                sample_end = min(sample_start + b_size - 1, num_authors - 1)
                if sample[sample_end]["Title"][0].lower() < letter:
                    # last item in sample is before letter - move further towards end
                    partition[0] = min(sample_end + 1, num_authors)
                elif (
                    sample_start == 0
                    or sample[sample_start - 1]["Title"][0].lower() < letter
                ):
                    break
                else:
                    # first item in sample is our letter or after - move further towards beginning
                    partition[1] = max(sample_start - 1, 0)

                sample_idx += 1
                if sample_idx >= 9:
                    logger.warning("Bailing out to avoid infinite loop")
                    break

            b_start = sample_start
            for idx in range(sample_start, sample_end):
                if sample[idx]["Title"].lower().startswith(letter):
                    b_start = idx
                    break
            b_start = int(b_start / b_size) * b_size
        return b_start

    @property
    @instance.memoize
    def authors(self):
        catalog = getToolByName(self.context, "portal_catalog")
        author_string = safe_unicode(self.request.get("authors"))
        b_start = self.get_b_start()
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
