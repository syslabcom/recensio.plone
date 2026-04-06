from importlib import import_module
from plone import api
from plone.app.testing import IntegrationTesting
from plone.registry.interfaces import IRegistry
from recensio.plone.testing import RECENSIO_PLONE_FIXTURE
from recensio.plone.testing import RECENSIO_SOLR_FIXTURE
from textwrap import dedent
from zope.component import getUtility

import unittest


UPGRADE_MODULE = (
    "recensio.plone.upgrades.v2.20260328120000_update_solr_panel_settings.upgrade"
)
UPGRADE_PROFILE = "profile-recensio.plone.upgrades.v2:default-upgrade-20260328120000"
TARGET_VERSION = "20260328120000"

RECENSIO_PLONE_SOLR_FIRST_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RECENSIO_SOLR_FIXTURE, RECENSIO_PLONE_FIXTURE),
    name="RecensioPloneLayer:SolrFirstIntegrationTesting",
)


class TestSolrPanelSettingsUpgrade(unittest.TestCase):
    layer = RECENSIO_PLONE_SOLR_FIRST_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.portal_setup = api.portal.get_tool("portal_setup")
        self.registry = getUtility(IRegistry)

    def test_upgrade_updates_solr_registry_settings(self):
        self.registry["collective.solr.search_pattern"] = "Title:{value}"
        self.registry["collective.solr.required"] = ["SearchableText"]
        self.registry["collective.solr.max_results"] = 25
        self.registry["collective.solr.facets"] = ["portal_type", "Subject"]

        upgrade_module = import_module(UPGRADE_MODULE)
        upgrade_module.UpdateSolrPanelSettings(
            self.portal_setup,
            associated_profile=UPGRADE_PROFILE,
            base_profile="recensio.plone:default",
            target_version=TARGET_VERSION,
        )

        self.assertEqual(1000, self.registry["collective.solr.max_results"])
        self.assertEqual(
            dedent(
                """\
                +(Title:{value}^10 OR
                Description:{value}^5 OR
                SearchableText:{value} OR
                SearchableText:({base_value} OR
                Subject:{value}^5 OR
                isbn:{value}^1000 OR
                publisher:{value}^5
                ) OR
                searchwords:({base_value})^1000)
                -showinsearch:False
                """
            ).strip(),
            self.registry["collective.solr.search_pattern"].strip(),
        )
        self.assertEqual(["use_solr"], list(self.registry["collective.solr.required"]))
        self.assertEqual(
            ["portal_type", "Subject", "ddcPlace", "ddcTime"],
            list(self.registry["collective.solr.facets"]),
        )
