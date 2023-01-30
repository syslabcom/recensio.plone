from DateTime import DateTime
from plone import api
from plone.memoize import ram
from Products.Five.browser import BrowserView
from recensio.plone.browser.canonical import CanonicalURLHelper


def _render_cachekey(method, self, brain, lang):
    return (brain.getPath(), lang, DateTime().dayOfYear())


class PublicationsView(BrowserView, CanonicalURLHelper):
    """Overview page of publications."""

    @ram.cache(_render_cachekey)
    def brain_to_pub(self, brain, lang):
        pubob = brain.getObject()
        if "logo" in pubob.objectIds():
            logourl = brain.getPath() + "/logo/image_thumb"
        else:
            logourl = self.context.portal_url.getPortalPath() + "/empty_publication.jpg"
        if pubob.getDefaultPage():
            defob = getattr(pubob, pubob.getDefaultPage())
            # XXX restore this line when we have an alternative to getTranslation
            # defob = defob.getTranslation(lang) or defob
        else:
            defob = pubob
        title = defob and defob.Title() != "" and defob.Title() or pubob.Title()
        desc = defob and defob.Description() or pubob.Description()
        morelink = defob and "/".join(defob.getPhysicalPath()) or ""
        return dict(title=title, desc=desc, logo=logourl, link=morelink)

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
            info = self.brain_to_pub(pub, currlang)
            info["logo"] = self.request.physicalPathToURL(info["logo"])
            info["link"] = self.request.physicalPathToURL(info["link"])
            publist.append(info)
        return publist

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
