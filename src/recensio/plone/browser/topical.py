# from Products.Archetypes.utils import OrderedDict
from collections import OrderedDict
from collective.solr.browser.facets import param
from collective.solr.browser.facets import SearchFacetsView
from copy import deepcopy
from plone import api
from plone.memoize.view import memoize
from Products.CMFCore.utils import getToolByName
from recensio.plone import _
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.browser.facets import browsing_facets
from recensio.plone.browser.facets import convertFacets
from recensio.plone.browser.helper import CrossPlatformMixin
from recensio.plone.config import REVIEW_TYPES
from urllib.parse import urlencode
from ZTUtils import make_query

import logging

log = logging.getLogger(__name__)
PORTAL_TYPES = REVIEW_TYPES
SORT_RELEVANCE = "relevance"
SORT_CREATED = "created"
TOPICAL_SORTS = OrderedDict(
    (
        (
            SORT_RELEVANCE,
            {
                "title": _("label_sort_relevance", default="Relevance"),
            },
        ),
        (
            SORT_CREATED,
            {
                "title": _("label_sort_newest", default="Newest first"),
                "sort_on": "created",
                "sort_order": "reverse",
            },
        ),
    )
)


class BrowseTopicsView(SearchFacetsView, CrossPlatformMixin):
    """View for topical browsing (ddcPlace etc.)"""

    show_if_empty = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        helper = api.content.get_view(context=context, name="vocabulary-helper")
        language = self.vocabulary_language
        self.vocDict = dict(
            ddcPlace=helper.ddcPlace.vdex.getVocabularyDict(lang=language),
            ddcTime=helper.ddcTime.vdex.getVocabularyDict(lang=language),
            ddcSubject=helper.ddcSubject.vdex.getVocabularyDict(lang=language),
        )
        self.submenus = [
            dict(title="Epoch", id="ddcTime"),
            dict(title="Region", id="ddcPlace"),
            dict(title="Topic", id="ddcSubject"),
        ]
        self.queryparam = "fq"

    def __call__(self):
        return self.index()

    @property
    def vocabulary_language(self):
        language = api.portal.get_current_language() or "en"
        return language.split("-", 1)[0].split("_", 1)[0]

    @property
    def use_view_action_types(self):
        return api.portal.get_registry_record(
            "plone.types_use_view_action_in_listings", default=[]
        )

    @property
    def default_query(self):
        return {
            "portal_type": PORTAL_TYPES,
            "facet": "true",
            "facet.field": self.facet_fields,
            "b_size": 10,
            "b_start": 0,
        }

    @property
    def facet_fields(self):
        return browsing_facets

    @property
    @memoize
    def form(self):
        form = self.request.form.copy()
        if self.queryparam in form:
            # filter out everything but our ddc attributes
            if self.queryparam == "fq":
                if not isinstance(form[self.queryparam], list):
                    form[self.queryparam] = [form[self.queryparam]]
                form[self.queryparam] = [
                    x
                    for x in form[self.queryparam]
                    if x.split(":")[0].strip("+") in self.facet_fields
                ]
        form_facet_fields = form.get("facet.field", [])
        if not isinstance(form_facet_fields, list):
            form_facet_fields = [form_facet_fields]
        form["facet.field"] = list(set(form_facet_fields + self.facet_fields))
        return form

    @property
    def current_sort(self):
        sort_on = self.request.form.get("sort_on")
        sort_order = (self.request.form.get("sort_order") or "").lower()
        if (
            sort_on == TOPICAL_SORTS[SORT_CREATED]["sort_on"]
            and sort_order == TOPICAL_SORTS[SORT_CREATED]["sort_order"]
        ):
            return SORT_CREATED
        return SORT_RELEVANCE

    @property
    def current_sort_on(self):
        return TOPICAL_SORTS[self.current_sort].get("sort_on")

    @property
    def current_sort_order(self):
        return TOPICAL_SORTS[self.current_sort].get("sort_order")

    @property
    def show_relevance_scores(self):
        return self.current_sort == SORT_RELEVANCE

    @property
    def sort_options(self):
        options = []
        for key, config in TOPICAL_SORTS.items():
            options.append(
                {
                    "title": config["title"],
                    "url": self._sort_url(
                        sort_on=config.get("sort_on"),
                        sort_order=config.get("sort_order"),
                    ),
                    "selected": self.current_sort == key and "selected" or None,
                }
            )
        return options

    def _sort_url(self, sort_on=None, sort_order=None):
        params = self.request.form.copy()
        params.pop("b_start", None)
        params.pop("sort_on", None)
        params.pop("sort_order", None)
        params.pop("facet.field", None)
        if sort_on:
            params["sort_on"] = sort_on
        if sort_order:
            params["sort_order"] = sort_order
        query_string = urlencode(params, doseq=True)
        if not query_string:
            return self.request.URL
        return f"{self.request.URL}?{query_string}"

    @property
    @memoize
    def results(self):
        query = self.default_query.copy()
        query.update(self.form)
        log.debug("Querying Solr with query: %r", query)
        if "set_language" in query:
            del query["set_language"]
        stripped_query = deepcopy(query)
        for key in query:
            if query[key] in ["", []]:
                del stripped_query[key]
        if self.form.get("use_navigation_root", True) and "path" not in query:
            stripped_query["path_parents"] = "/".join(
                api.portal.get().getPhysicalPath()
            )
        stripped_query["use_solr"] = True
        catalog = getToolByName(self.context, "portal_catalog")
        results = catalog(stripped_query)
        return results

    @property
    def max_score(self):
        """Calculate the score based on the maxScore attribute of the SolrResponse, if available."""
        if self.results is not None and hasattr(self.results, "results"):
            solr_results = self.results.results()
            if hasattr(solr_results, "maxScore"):
                return float(solr_results.maxScore)
        return None

    def reset_facets_href(self):
        qs = {}
        if self.request.get("SearchableText"):
            qs["SearchableText"] = self.request.get("SearchableText")
        if self.current_sort_on:
            qs["sort_on"] = self.current_sort_on
        if self.current_sort_order:
            qs["sort_order"] = self.current_sort_order
        if "use_navigation_root" in self.request.form:
            qs["use_navigation_root"] = self.request.form["use_navigation_root"]
        if qs:
            return "./browse-topics?%s" % urlencode(qs, doseq=True)
        return "./browse-topics"

    def facets(self):
        """prepare and return facetting info for the given SolrResponse"""
        fcs = getattr(self.results, "facet_counts", None)
        if self.results is not None and fcs is not None:
            filt = None  # lambda name, count: name and count > 0
            if self.queryparam in self.form:
                # if self.queryparam == "fq":
                #     container = self.form[self.queryparam]
                # else:
                #     container = self.form
                # filter out everything but our ddc attributes
                if self.queryparam == "fq":
                    if not isinstance(self.form[self.queryparam], list):
                        self.form[self.queryparam] = [self.form[self.queryparam]]
                    self.form[self.queryparam] = [
                        x
                        for x in self.form[self.queryparam]
                        if x.split(":")[0].strip("+") in self.facet_fields
                    ]
            return convertFacets(
                fcs.get("facet_fields", {}),
                self.context,
                self.form,
                filt,
                facet_fields=self.facet_fields,
                queryparam=self.queryparam,
            )
        else:
            return None
        # # Below code commented out because it's logically unreachable
        # if self.results is not None:
        #     # we have no facet information, solr probably not running
        #     filt = None
        #     catalog = getToolByName(self.context, "portal_catalog")
        #     indexes = filter(
        #         lambda i: i.id in self.facet_fields, catalog.getIndexObjects()
        #     )
        #     # I know this is sick, but it shouldn't get used anyway
        #     ffdict = dict(
        #         map(
        #             lambda ind: (
        #                 ind.id,
        #                 dict(
        #                     map(
        #                         lambda x: (x, 1),
        #                         [
        #                             item
        #                             for sublist in ind.uniqueValues()
        #                             for item in sublist
        #                         ],
        #                     )
        #                 ),
        #             ),
        #             indexes,
        #         )
        #     )
        #     return convertFacets(
        #         ffdict,
        #         self.context,
        #         self.form,
        #         filt,
        #         facet_fields=self.facet_fields,
        #         queryparam=self.queryparam,
        #     )

    def selected(self):
        """determine selected facets and prepare links to clear them;
        this assumes that facets are selected using filter queries"""
        info = []
        facets = param(self, "facet.field")
        fq = param(self, self.queryparam)
        fq = [x for x in fq]
        if self.queryparam == "fq":
            fq = [x for x in fq if x.split(":")[0].strip("+") in self.facet_fields]
        for idx, query in enumerate(fq):
            params = self.form.copy()
            if self.queryparam == "fq":
                field, value = query.split(":", 1)
            else:
                field = self.queryparam
                value = '"%s"' % query
            params[self.queryparam] = fq[:idx] + fq[idx + 1 :]
            if field not in facets:
                params["facet.field"] = facets + [field]
            if value.startswith('"') and value.endswith('"'):
                info.append(
                    dict(
                        title=field,
                        value=value[1:-1],
                        query=make_query(params, doseq=True),
                    )
                )
        return info

    def sort(self, submenu):
        return sorted(submenu, key=lambda x: x["count"], reverse=True)

    @memoize
    def getMenu(self):
        facets = self.facets()
        selected = self.selected()

        def getSubmenu(vocab, facet, selected):
            submenu = []
            for item in vocab.items():
                name = item[0]
                # extract vocabulary term for item
                itemvoc = item[0]
                if isinstance(item[1], str):
                    itemvoc = item[1]
                elif isinstance(item[1], tuple):
                    itemvoc = item[1][0]

                iteminfo = dict(name=name, voc=itemvoc, count=0, query="", submenu=[])
                # look if we have info from facets()
                if facet:
                    facetinfo = [x for x in facet["counts"] if x["name"] == name]
                    if facetinfo:  # and facetinfo[0]['count'] > 0:
                        iteminfo.update(facetinfo[0])
                # look if we have info from selected()
                if selected:
                    selectedinfo = [x for x in selected if x["value"] == name]
                    if selectedinfo:
                        iteminfo["clearquery"] = selectedinfo[0]["query"]
                        log.debug("selected %(value)s for %(title)s" % selectedinfo[0])

                # recurse if we have subordinate vocabulary items
                subitem = item[1][1]
                if isinstance(subitem, dict) or isinstance(subitem, OrderedDict):
                    subsubmenu = getSubmenu(subitem, facet, selected)
                    iteminfo["submenu"] = subsubmenu
                    # iteminfo['count'] += sum(map(
                    #         lambda x: x['count'], subsubmenu))
                submenu.append(iteminfo)

            return self.sort(submenu)

        menu = dict()

        for attrib in self.facet_fields:
            submenu = []
            if facets:
                facets_sub = [x for x in facets if x["title"] == attrib]
            else:
                facets_sub = []
            if selected:
                selected_sub = [x for x in selected if x["title"] == attrib]
            else:
                selected_sub = []

            if facets_sub:
                facets_sub = facets_sub[0]
            if facets_sub or selected_sub or self.show_if_empty:
                submenu = getSubmenu(self.vocDict[attrib], facets_sub, selected_sub)
            menu[attrib] = submenu
        return menu

    def getSubmenus(self):
        menu = self.getMenu()
        # this would work if ATVocabularyManager.utils were consistent:
        # submenus = [dict(title=voc.getVocabularyByName('region_values').
        #                  Title(),id='ddcPlace'),
        submenus = self.submenus
        for submenu in submenus:
            mid = submenu["id"]
            cq = [item for item in menu[mid] if "clearquery" in item]
            for item in menu[mid]:
                cq = cq + [
                    subitem for subitem in item["submenu"] if "clearquery" in subitem
                ]
            submenu["selected"] = cq

        return submenus

    def showSubmenu(self, submenu):
        """Returns True if submenu has an entry with query or clearquery set,
        i.e. should be displayed
        """
        return bool([x for x in submenu if "clearquery" in x or x["count"] > 0])

    def expandSubmenu(self, submenu):
        """Returns True if submenu has an entry with clearquery set, i.e.
        should be displayed expanded
        """
        return bool(
            [
                x
                for x in submenu
                if "clearquery" in x or self.expandSubmenu(x["submenu"])
            ]
        )

    def get_tfpot(self, obj, _t):
        """Get the title of the publication for a parent of type _t
        Sorry for the cryptic name but for the sake of brevity in the template…
        And no, this is not final code, cleanup is scheduled.
        """
        value = IParentGetter(obj).get_title_from_parent_of_type(_t)
        return value
