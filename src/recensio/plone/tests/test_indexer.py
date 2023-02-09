from plone import api
from plone.app.testing.interfaces import SITE_OWNER_NAME
from recensio.plone.adapter.indexer import ddcPlace
from recensio.plone.adapter.indexer import ddcTime
from recensio.plone.adapter.indexer import isbn
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING

import unittest


class ReviewStub:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


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

    def test_isbn_and_isbn_online(self):
        result = isbn(ReviewStub(isbn="12-34", isbn_online="5-678"))()
        self.assertEqual(result, ["1234", "5678"])

    def test_isbn_only(self):
        result = isbn(ReviewStub(isbn="12-34"))()
        self.assertEqual(result, ["1234"])

    def test_isbn_online_only(self):
        result = isbn(ReviewStub(isbn_online="834 5562 88"))()
        self.assertEqual(result, ["834556288"])

    def test_no_isbn_whatsoever(self):
        result = isbn(ReviewStub())()
        self.assertEqual(result, [])

    def test_issn_and_issn_online(self):
        result = isbn(ReviewStub(issn="12-34", issn_online="5-678"))()
        self.assertEqual(result, ["1234", "5678"])

    def test_issn_only(self):
        result = isbn(ReviewStub(issn="12-34"))()
        self.assertEqual(result, ["1234"])

    def test_issn_online_only(self):
        result = isbn(ReviewStub(issn_online="834 5562 88"))()
        self.assertEqual(result, ["834556288"])

    def test_no_issn_whatsoever(self):
        result = isbn(ReviewStub())()
        self.assertEqual(result, [])
