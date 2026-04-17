from plone import api
from plone.app.testing.interfaces import SITE_OWNER_NAME
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING
from recensio.plone.viewlets.viewlets import Publicationlisting
from unittest.mock import Mock

import unittest


class TestPublicationListing(unittest.TestCase):
    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.request.form.clear()

        with api.env.adopt_user(SITE_OWNER_NAME):
            container = api.content.create(
                type="Folder",
                id="sample-reviews-publicationlisting",
                title="Sample Reviews",
                container=self.portal,
            )

            self.publication = api.content.create(
                type="Publication",
                id="publication-a",
                title="Publication A",
                container=container,
            )
            self.document = api.content.create(
                type="Document",
                id="index",
                title="Publication overview",
                container=self.publication,
            )
            self.volume = api.content.create(
                type="Volume",
                id="volume-2025",
                title="Volume 2025",
                container=self.publication,
            )
            self.issue = api.content.create(
                type="Issue",
                id="issue-01",
                title="Issue 01",
                container=self.volume,
            )
            self.review_in_issue = api.content.create(
                type="Review Monograph",
                id="review-in-issue",
                title="Review in issue",
                container=self.issue,
            )
            self.review_in_volume = api.content.create(
                type="Review Journal",
                id="review-in-volume",
                title="Review in volume",
                container=self.volume,
            )

            for obj in [
                self.publication,
                self.document,
                self.volume,
                self.issue,
                self.review_in_issue,
                self.review_in_volume,
            ]:
                api.content.transition(obj=obj, transition="publish")

    def test_viewlet_volume_summary_contains_counts_and_lazy_load_url(self):
        viewlet = Publicationlisting(self.document, self.request, Mock())

        volumes = viewlet.volumes()

        self.assertTrue(viewlet.visible())
        self.assertEqual(1, len(volumes))
        self.assertEqual("Volume 2025", volumes[0]["title"])
        self.assertEqual(1, volumes[0]["issue_count"])
        self.assertEqual(2, volumes[0]["review_count"])
        self.assertTrue(volumes[0]["has_children"])
        self.assertIn("@@publicationlisting-children", volumes[0]["load_url"])

    def test_lazy_children_view_renders_volume_contents(self):
        self.request.form["container_uid"] = self.volume.UID()

        view = api.content.get_view(
            "publicationlisting-children",
            self.publication,
            self.request,
        )
        html = view()

        self.assertIn("pat-inject", html)
        self.assertIn("trigger: autoload-visible", html)
        self.assertIn("Issue 01", html)
        self.assertIn("Review in volume", html)

    def test_lazy_children_view_renders_issue_reviews(self):
        self.request.form["container_uid"] = self.issue.UID()

        view = api.content.get_view(
            "publicationlisting-children",
            self.publication,
            self.request,
        )
        html = view()

        self.assertIn("Review in issue", html)
