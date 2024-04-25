from Acquisition import aq_parent
from plone.memoize import instance
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from recensio.plone.controlpanel.settings import IRecensioSettings
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.component.hooks import setSite
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from ZTUtils import make_query

import logging
import re


log = logging.getLogger(__name__)


class IRecensioHelperView(Interface):
    """Interface for the RecensioHelperView."""

    def normalize_isbns_in_text(text):
        """Enables flexible full text search for ISBNs."""

    def punctuated_title(self, title, subtitle):
        """"""

    def contains_one_of(self, items, values):
        """"""

    def get_subtree(self, value):
        """"""


class SwitchPortal:
    def __init__(self, portal):
        self.portal = portal

    def __enter__(self):
        self.original_portal = getSite()
        setSite(self.portal)

    def __exit__(self, type, value, traceback):
        setSite(self.original_portal)
        if value:
            log.warn(
                "Could not get portal url of " + self.portal.id,
                exc_info=(type, value, traceback),
            )
            return True


class CrossPlatformMixin:
    def get_toggle_cross_portal_url(self):
        new_form = self.request.form.copy()
        new_form["use_navigation_root"] = not new_form.get("use_navigation_root", True)
        return "?".join((self.request["ACTUAL_URL"], make_query(new_form)))

    @instance.memoize
    def get_foreign_portal_url(self, portal_id):
        other_portal = self.context.unrestrictedTraverse("/" + portal_id)
        external_url = None
        with SwitchPortal(other_portal):
            registry = getUtility(IRegistry)
            settings = registry.forInterface(
                IRecensioSettings, prefix="recensio.plone.settings"
            )
            external_url = settings.external_portal_url
        return external_url

    def get_foreign_url(self, result):
        portal_id = result.getPath().split("/")[1]
        other_portal = self.context.unrestrictedTraverse("/" + portal_id)
        external_url = self.get_foreign_portal_url(portal_id)
        if not external_url:
            return result.getURL()
        return result.getURL().replace(other_portal.absolute_url(), external_url)

    @instance.memoize
    def get_all_portal_ids(self):
        this_portal = getSite()
        app = aq_parent(this_portal)
        return app.objectIds("Plone Site")

    def get_portal_link_snippet(self):
        portal_ids = self.get_all_portal_ids()
        link_tpl = '<a href="{1}">{0}</a>'
        portal_infos = []
        for portal_id in portal_ids:
            portal_title = self.context.restrictedTraverse("/" + portal_id).Title()
            portal_infos.append((portal_title, self.get_foreign_portal_url(portal_id)))
        link_snippet = ", ".join(
            [
                link_tpl.format(*portal_info)
                for portal_info in portal_infos
                if portal_info[1]
            ]
        )
        return link_snippet


@implementer(IRecensioHelperView)
class RecensioHelperView(BrowserView, CrossPlatformMixin):
    """General purpose view methods for Recensio."""

    @property
    def heading_add_item_title(self):
        """For French Presentations the add form should display:

        Ajouter une ...
        """
        portal = getSite()

        fti = portal.portal_types.getTypeInfo(self.context)  #
        itemtype = fti.Title()

        lang = portal.portal_languages.getPreferredLanguage()
        if fti.content_meta_type.startswith("Presentation") and lang == "fr":
            itemtype = "heading_add_%s_title" % fti.content_meta_type

        return itemtype

    def listRecensioSupportedLanguages(self):
        # XXX return listRecensioSupportedLanguages()
        return None

    def listAvailableContentLanguages(self):
        # XXX return listAvailableContentLanguages()
        return None

    def punctuated_title(self, title, subtitle):
        """#4040

        if the string already ends in an punctuation mark don't add
        another
        """
        last_char = title[-1]

        p_title = title
        if last_char not in ["!", "?", ":", ";", ".", ","] and subtitle:
            p_title = p_title + "."

        if subtitle:
            p_title = p_title + " "

        return p_title

    def normalize_isbns_in_text(self, text):
        expr = re.compile(r"[0-9]+[ \-0-9]*[0-9]+")
        for match in expr.findall(text):
            isbn = match
            isbn = "".join(isbn.split("-"))
            isbn = "".join(isbn.split(" "))
            text = text.replace(match, isbn)
        return text

    def contains_one_of(self, items, values):
        """Check whether one of the values is contained in items.

        items must be a list of tuples as acquired by calling items() on
        a vocabulary dict.
        """
        return sum(
            [
                item[0] in values
                or self.contains_one_of(dict(item[1][1] or {}).items(), values)
                for item in items
            ]
        )

    def get_subtree(self, value):
        """Retrieve the next level of a recursive vocabulary dict. Value is
        expected to be a tuple like this: ('4', ('Europa', OrderedDict([])))
        The items of the OrderedDict are returned.

        This method was added for search_form. We cannot access the
        items() method of an OrderedDict there.
        """
        subtree = value[1][1] or {}
        return subtree.items()


class VocabularyHelper(BrowserView):
    def get_named_vocabulary(self, name):
        factory = getUtility(IVocabularyFactory, name)
        return factory(self.context)

    @property
    def ddcSubject(self):
        return self.get_named_vocabulary("recensio.plone.vocabularies.topic_values")

    @property
    def ddcTime(self):
        return self.get_named_vocabulary("recensio.plone.vocabularies.epoch_values")

    @property
    def ddcPlace(self):
        return self.get_named_vocabulary("recensio.plone.vocabularies.region_values")
