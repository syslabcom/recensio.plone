from plone import api
from plone.app.testing.interfaces import SITE_OWNER_NAME
from plone.app.textfield.value import RichTextValue
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING

import unittest


class TestPublicationDocumentView(unittest.TestCase):
    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

    def test_document_fti_includes_publication_document_view(self):
        document_fti = api.portal.get_tool("portal_types").Document

        self.assertIn("publication_document_view", document_fti.view_methods)

    def test_publication_document_view_renders_publication_context(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            container = api.content.create(
                type="Folder",
                id="sample-reviews-publication-profile",
                title="Sample Reviews",
                container=self.portal,
            )

            publication = api.content.create(
                type="Publication",
                id="publication-profile-a",
                title="Publication A",
                container=container,
            )
            document = api.content.create(
                type="Document",
                id="profile",
                title="About this publication",
                container=publication,
            )
            document.text = RichTextValue(
                "<p>This publication focuses on new historical research.</p>"
            )

            volume = api.content.create(
                type="Volume",
                id="volume-2025",
                title="Volume 2025",
                container=publication,
            )
            issue = api.content.create(
                type="Issue",
                id="issue-01",
                title="Issue 01",
                container=volume,
            )
            review = api.content.create(
                type="Review Monograph",
                id="review-01",
                title="Review title",
                container=issue,
            )

            for obj in [publication, document, volume, issue, review]:
                api.content.transition(obj=obj, transition="publish")

        view = api.content.get_view(
            "publication_document_view",
            document,
            self.request,
        )

        html = view()

        self.assertIn("publication-profile-header", html)
        self.assertIn("About this publication", html)
        self.assertIn("Publication A", html)
        self.assertIn("#publicationslisting", html)
        self.assertIn("This publication focuses on new historical research.", html)
        self.assertIn("publication-profile-badge", html)
