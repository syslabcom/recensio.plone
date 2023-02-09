from plone import api
from plone.app.testing.interfaces import SITE_OWNER_NAME
from recensio.plone.adapter.indexer import ddcPlace
from recensio.plone.adapter.indexer import ddcTime
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING

import unittest


class TestIndexer(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"].clone()

        with api.env.adopt_user(SITE_OWNER_NAME):
            container = api.content.create(
                type="Folder",
                id="sample-reviews",
                title="Sample Reviews",
                container=self.portal,
            )

            publication = api.content.create(
                type="Publication",
                id="newspapera",
                title="Newspaper A",
                container=container,
            )
            volume = api.content.create(
                type="Volume",
                id="volume",
                title="Volume",
                container=publication,
            )
            self.review = api.content.create(
                type="Review Monograph",
                id="review-monograph",
                title="Review Monograph",
                container=volume,
            )

    def test_ddcPlace(self):
        self.review.ddcPlace = ["42.5", "43.4"]
        self.assertSetEqual(
            set(ddcPlace(self.review)()), {"4", "42", "42.5", "43", "437", "43.4"}
        )

    def test_ddcTime(self):
        self.review.ddcTime = ["09032", "09033"]
        self.assertSetEqual(set(ddcTime(self.review)()), {"0903", "09032", "09033"})
