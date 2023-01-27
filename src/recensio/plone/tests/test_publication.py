from plone import api
from plone.app.testing.helpers import login
from plone.app.testing.interfaces import SITE_OWNER_NAME
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING

import unittest


class TestParentGetter(unittest.TestCase):
    """"""

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        login(self.layer["app"], SITE_OWNER_NAME)
        api.content.create(
            container=self.portal,
            type="Folder",
            title="Zeitschriften",
            id="zeitschriften",
        )
        self.publication = api.content.create(
            container=self.portal.zeitschriften,
            type="Publication",
            title="Magazine A",
            id="magazine-a",
        )
        api.content.create(
            container=self.portal.zeitschriften["magazine-a"],
            type="Volume",
            title="2023",
            id="2023",
        )
        api.content.create(
            container=self.portal.zeitschriften["magazine-a"]["2023"],
            type="Issue",
            title="01",
            id="01",
        )

        self.review = api.content.create(
            container=self.portal.zeitschriften["magazine-a"]["2023"]["01"],
            type="Review Monograph",
            title="A Review",
            id="a-review",
        )

    def test_get_parent_of_review_monograph(self):
        result = IParentGetter(self.review).get_parent_object_of_type("Publication")
        self.assertEqual(result, self.publication)

    def test_get_parent_of_publication(self):
        result = IParentGetter(self.publication).get_parent_object_of_type(
            "Publication"
        )
        self.assertEqual(result, self.publication)
