from contextlib import contextmanager
from plone import api
from plone.app.testing.helpers import login
from plone.app.testing.interfaces import SITE_OWNER_NAME
from plone.app.textfield.value import RichTextValue
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING

import unittest


@contextmanager
def change_language(request, language):
    language_tool = api.portal.get_tool("portal_languages")
    language_tool.use_request_negotiation = True
    language_tool.use_cookie_negotiation = True
    request.other["set_language"] = language
    yield request
    del request.other["set_language"]


class TestPublication(unittest.TestCase):
    """"""

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        with api.env.adopt_user(SITE_OWNER_NAME):
            container = api.content.create(
                type="Folder",
                id="sample-reviews",
                title="Sample Reviews",
                container=self.portal,
            )

            self.publication = api.content.create(
                type="Publication",
                id="newspapera",
                title="Newspaper A",
                container=container,
            )

            self.custom_licence_doc_de = api.content.create(
                container=self.publication,
                id="fake_license_de",
                title="Fake Lizenz",
                type="Document",
            )
            self.custom_licence_doc_de.setLanguage("de")
            self.custom_licence_doc_de.text = RichTextValue(
                "Dies ist eine übersetzte Lizenz"
            )
            self.custom_licence_doc_en = api.content.create(
                container=self.publication,
                id="fake_license_en",
                title="Fake License",
                type="Document",
            )
            self.custom_licence_doc_en.setLanguage("en")
            self.custom_licence_doc_en.text = RichTextValue(
                "This is a translated license"
            )

            # XXX understand how to add a translation reference
            # self.custom_licence_doc_de.addTranslationReference(self.custom_licence_doc_en)

            self.volume = api.content.create(
                type="Volume",
                id="volume",
                title="Volume",
                container=self.publication,
            )
            self.issue = api.content.create(
                type="Issue",
                id="issue",
                title="Issue",
                container=self.volume,
            )
            self.review = api.content.create(
                type="Review Monograph",
                id="review-monograph",
                title="Review Monograph",
                container=self.issue,
            )

    def test_review_licence(self):
        """Ensure that when a custom licence is set on the Publication this is
        visibile on its child review."""
        language_tool = api.portal.get_tool("portal_languages")
        language_tool.use_cookie_negotiation = True
        default_review_licence = "license-note-review"
        review_view = api.content.get_view("review_view", self.review, self.request)

        with change_language(self.request, "de"):
            self.assertEqual(default_review_licence, review_view.getLicense())
        with change_language(self.request, "en"):
            self.assertEqual(default_review_licence, review_view.getLicense())

        custom_licence = "Custom Licence"
        self.publication.licence = custom_licence
        with change_language(self.request, "de"):
            self.assertEqual(custom_licence, review_view.getLicense())
        with change_language(self.request, "en"):
            self.assertEqual(custom_licence, review_view.getLicense())

        api.relation.create(
            source=self.publication,
            target=self.custom_licence_doc_de,
            relationship="licence_ref",
        )
        with change_language(self.request, "de"):
            self.assertEqual(
                "Dies ist eine übersetzte Lizenz",
                review_view.getLicense(),
            )

        # XXX: This test fails because the translation reference is not set
        # with change_language(self.request, "en"):
        #     self.assertEqual(
        #         "This is a translated license",
        #         review_view.getLicense(),
        #     )

        volume_licence = "Custom Volume Licence"
        self.volume.licence = volume_licence

        review_view.getLicense()
        self.assertEqual(volume_licence, review_view.getLicense())

        api.relation.create(
            source=self.volume,
            target=self.custom_licence_doc_de,
            relationship="licence_ref",
        )
        with change_language(self.request, "de"):
            self.assertEqual(
                "Dies ist eine übersetzte Lizenz",
                review_view.getLicense(),
            )

        # XXX: This test fails because the translation reference is not set
        # with change_language(self.request, "en"):
        #     self.assertEqual(
        #         "This is a translated license",
        #         review_view.getLicense(),
        #     )

        issue_licence = "Custom Issue Licence"
        self.issue.licence = issue_licence
        self.assertEqual(issue_licence, review_view.getLicense())

        api.relation.create(
            source=self.issue,
            target=self.custom_licence_doc_de,
            relationship="licence_ref",
        )
        with change_language(self.request, "de"):
            self.assertEqual(
                "Dies ist eine übersetzte Lizenz",
                review_view.getLicense(),
            )

        # XXX: This test fails because the translation reference is not set
        # with change_language(self.request, "en"):
        #     self.assertEqual(
        #         "This is a translated license",
        #         review_view.getLicense(),
        #     )

        review_licence = "Custom Review Licence"
        self.review.licence = review_licence
        self.assertEqual(review_licence, review_view.getLicense())


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
