from AccessControl import Unauthorized
from Acquisition import aq_inner
from DateTime import DateTime
from plone import api
from plone.i18n.locales.languages import _languagelist
from plone.memoize import ram
from plone.memoize.instance import memoize
from Products.Five.browser import BrowserView
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.config import REVIEW_TYPES
from recensio.plone.utils import getTranslations
from recensio.plone.utils import punctuated_title_and_subtitle
from zope.component import getMultiAdapter
from ZTUtils import make_query

import logging


log = logging.getLogger("recensio.theme")


class HomepageView(BrowserView):
    """Dynamic elements on the homepage."""

    review_languages = ["en", "de", ""]

    def _render_cachekey(method, self, lang=""):
        preflang = api.portal.get_current_language()
        portal_membership = api.portal.get_tool("portal_membership")
        member = portal_membership.getAuthenticatedMember()
        roles = member.getRolesInContext(self.context)

        today = DateTime().strftime("%Y-%m-%d")
        root = api.portal.get_navigation_root(context=self.context)
        path = "/".join(root.getPhysicalPath())
        return (path, preflang, lang, self.review_languages, roles, today)

    def format_effective_date(self, date_string):
        """Format the publication date as specified in #2627."""
        if date_string == "None":
            return ""
        date = DateTime(date_string)
        return "%s-%02d-%02d" % (date.year(), date.month(), date.day())

    def format_authors(self, brain):
        ob = brain.getObject()
        authors = getattr(ob, "authors", "")
        if len(authors) == 0:
            authors = getattr(ob, "editorial", "")
        if len(authors) == 0:
            return ""
        first_author = authors[0].to_object
        if not first_author:
            return ""
        firstname = first_author.firstname.strip()
        initial = firstname[0] + ". " if len(firstname) > 0 else ""
        lastname = first_author.lastname
        et_al = " et al." if len(authors) > 1 else ""
        if len(lastname) > 0:
            return f"{initial}{lastname}{et_al}:"
        return ""

    @property
    @memoize
    def review_base_query(self):
        root = api.portal.get_navigation_root(context=self.context)
        query = dict(
            portal_type=REVIEW_TYPES,
            path="/".join(root.getPhysicalPath()),
            review_state="published",
            sort_on="effective",
            sort_order="reverse",
            b_size=30,
        )
        return query

    @ram.cache(_render_cachekey)
    def _getRmByLanguage(self, lang):
        pc = api.portal.get_tool("portal_catalog")
        langinfo = _languagelist.copy()
        langinfo[""] = {"name": "International", "native": "int"}
        resultset = list()
        query = self.review_base_query
        q = query.copy()
        if lang:
            q["languageReview"] = [lang]
        else:
            q["languageReview"] = list(
                set(langinfo.keys()).difference(set(self.review_languages))
            )
        res = pc(q)
        for part in range(int(6 / len(self.review_languages))):
            resultset.append(
                dict(
                    language=lang or "int",
                    part=part,
                    langname=langinfo[lang]["native"],
                    results=[
                        dict(
                            authors=self.format_authors(x),
                            path=x.getPath(),
                            title=punctuated_title_and_subtitle(x.getObject()),
                            date=self.format_effective_date(x["EffectiveDate"]),
                            meta_type=x.portal_type,
                        )
                        for x in res[part * 5 : part * 5 + 4]
                    ],
                    query_str=make_query(q),
                )
            )
        # print "getReviewMonographs", lang, len(res)
        return resultset

    def getReviewMonographs(self):
        resultset = list()
        for lang in self.review_languages:
            resultset.extend(self._getRmByLanguage(lang))
        return resultset

    @ram.cache(_render_cachekey)
    def getReviewJournals(self):
        pc = api.portal.get_tool("portal_catalog")
        root = api.portal.get_navigation_root(context=self.context)
        query = dict(
            portal_type=["Issue", "Volume"],
            path="/".join(root.getPhysicalPath()),
            review_state="published",
            sort_on="effective",
            sort_order="reverse",
            b_size=12,
        )
        res = pc(query)[:12]
        resultset = list()
        objects = {}
        for r in res:
            objects[r.getObject()] = r
        for obj, brain in objects.items():
            if obj.portal_type == "Issue" and obj.__parent__.portal_type == "Volume":
                if obj.__parent__ in objects.keys() and objects[obj.__parent__] in res:
                    res.remove(objects[obj.__parent__])
        for r in res:
            if not r:
                continue
            try:
                o = r.getObject()
            except AttributeError:
                log.exception(
                    "Could not get object. Probably this means "
                    "there is a mismatch with solr"
                )
                continue
            if o not in objects:
                continue
            pg = IParentGetter(o)
            publication = pg.get_parent_object_of_type("Publication")
            publication_title = publication and publication.Title() or ""
            if o.portal_type == "Volume":
                volume = o
            else:
                volume = pg.get_parent_object_of_type("Volume")
            volume_title = volume and volume.Title() or ""

            # The title of the result shall only be shown if the result
            # is a volume. Because we already show the volume title.
            result_title = r.Title if o != volume else ""
            resultset.append(
                dict(
                    Title=result_title,
                    effective_date=self.format_effective_date(r.EffectiveDate),
                    publication_title=publication_title,
                    review_path=r.getPath(),
                    volume_title=volume_title,
                )
            )
        return resultset[:6]

    @ram.cache(_render_cachekey)
    def getPublications(self):
        portal = self.context.portal_url.getPortalObject()
        rezensionen = getattr(portal, "rezensionen", None)
        zeitschriften = getattr(rezensionen, "zeitschriften", None)
        pc = api.portal.get_tool("portal_catalog")
        if zeitschriften:
            query = dict(
                portal_type=["Publication"],
                review_state="published",
                path="/".join(zeitschriften.getPhysicalPath()),
                sort_on="id",
                b_size=1000,
            )

            context = aq_inner(self.context)
            portal_state = getMultiAdapter(
                (context, self.request), name="plone_portal_state"
            )

            lang = portal_state.language()
            pubs = []
            for brain in pc(query):
                try:
                    obj = brain.getObject()
                    default_page = obj.restrictedTraverse(obj.getDefaultPage())
                    translations = getTranslations(default_page)
                    if lang in translations:
                        translated_ob = translations[lang][0]
                        pubs.append(translated_ob)
                except Unauthorized:
                    continue
            items = [
                dict(title=x.Title(), path="/".join(x.getPhysicalPath())) for x in pubs
            ]
            return items
        else:
            # This can only happen, when there is no initial content yet
            return []

    def get_portal_type_query(self):
        return "&".join(
            [
                "portal_type:list={}".format(portal_type.replace(" ", "+"))
                for portal_type in REVIEW_TYPES
            ]
        )
