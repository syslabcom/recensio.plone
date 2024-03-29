from DateTime import DateTime
from plone import api
from plone.memoize import ram
from Products.CMFPlone.browser.defaultpage import DefaultPage
from Products.Five.browser import BrowserView
from recensio.plone.browser.canonical import CanonicalURLHelper


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


class PublicationsView(BrowserView, CanonicalURLHelper):
    """Overview page of publications."""

    @ram.cache(_render_cachekey)
    def brain_to_pub(self, brain, lang):
        pubob = brain.getObject()
        if "logo" in pubob.objectIds():
            logo_path = brain.getPath() + "/logo/@@images/image/thumb"
        else:
            logo_path = (
                self.context.portal_url.getPortalPath() + "/empty_publication.jpg"
            )
        if pubob.getDefaultPage():
            defob = getattr(pubob, pubob.getDefaultPage())
            # XXX restore this line when we have an alternative to getTranslation
            # defob = defob.getTranslation(lang) or defob
        else:
            defob = pubob
        title = defob and defob.Title() != "" and defob.Title() or pubob.Title()
        desc = defob and defob.Description() or pubob.Description()
        path = defob and "/".join(defob.getPhysicalPath()) or ""
        return dict(title=title, desc=desc, logo_path=logo_path, path=path)

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
            info["logo"] = self.request.physicalPathToURL(info["logo_path"])
            info["link"] = self.request.physicalPathToURL(info["path"])
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
