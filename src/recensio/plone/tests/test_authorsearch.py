from collective.solr.testing import activateAndReindex
from plone import api
from recensio.plone.interfaces import IRecensioPloneLayer
from recensio.plone.testing import RECENSIO_PLONE_SOLR_INTEGRATION_TESTING
from zope.interface import alsoProvides
from zope.interface import noLongerProvides

import unittest


class TestAuthorSearch(unittest.TestCase):
    """Author search view tests."""

    layer = RECENSIO_PLONE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"].clone()
        alsoProvides(self.request, IRecensioPloneLayer)
        if "gnd" not in self.portal:
            with api.env.adopt_roles(["Manager"]):
                api.content.create(
                    type="Folder",
                    container=self.portal,
                    id="gnd",
                    title="GND",
                )

        gnd_view = api.content.get_view(
            name="gnd-view", context=self.portal, request=self.request
        )
        for data in [
            {"lastname": "Kot\u0142owski", "firstname": "Tadeusz"},
            {"lastname": "Benthin", "firstname": "Patrick"},
            {"lastname": "Eimer", "firstname": "Claudio"},
            {"lastname": "Eimer", "firstname": "Kathy"},
        ]:
            gnd_view.createPerson(**data)

        activateAndReindex(self.portal)

    def tearDown(self):
        noLongerProvides(self.request, IRecensioPloneLayer)

    def _gnd_view(self):
        return api.content.get_view(
            name="gnd-view", context=self.portal, request=self.request
        )

    def test_search(self):
        self.request.form = {"authors": "Eimer"}
        view = api.content.get_view(
            context=self.portal, request=self.request, name="authorsearch"
        )
        result = view.authors
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["Title"], "Eimer, Claudio")
        self.assertEqual(result[1]["Title"], "Eimer, Kathy")

    def test_selected_letter_defaults_to_first_available(self):
        view = api.content.get_view(
            context=self.portal, request=self.request, name="authorsearch"
        )

        self.assertEqual("B", view.selected_letter)

    def test_requested_letter_is_selected_and_preloaded(self):
        self.request.form = {"letter": "E"}
        view = api.content.get_view(
            context=self.portal, request=self.request, name="authorsearch"
        )

        panels = {panel["letter"]: panel for panel in view.panels}

        self.assertEqual("E", view.selected_letter)
        self.assertTrue(panels["E"]["loaded"])
        self.assertEqual(
            ["Eimer, Claudio", "Eimer, Kathy"],
            [author["title"] for author in panels["E"]["authors"]],
        )
        self.assertFalse(panels["B"]["loaded"])
        self.assertIn("@@authorsearch-batch", panels["B"]["initial_url"])

    def test_jump_links_mark_available_letters(self):
        view = api.content.get_view(
            context=self.portal, request=self.request, name="authorsearch"
        )

        links = {link["label"]: link for link in view.author_jump_links}

        self.assertFalse(links["A"]["enabled"])
        self.assertTrue(links["B"]["enabled"])
        self.assertTrue(links["B"]["current"])
        self.assertIn("letter=B", links["B"]["href"])
        self.assertIn("letter=E", links["E"]["href"])

    def test_batch_view_returns_cards_and_next_url(self):
        gnd_view = self._gnd_view()
        for idx in range(91):
            gnd_view.createPerson(lastname=f"Additional{idx:02d}", firstname="Author")

        activateAndReindex(self.portal)

        self.request.form = {"letter": "A", "b_start": 30}
        view = api.content.get_view(
            context=self.portal, request=self.request, name="authorsearch-batch"
        )
        html = view()

        self.assertIn("Additional30, Author", html)
        self.assertIn("data-next-url", html)
        self.assertIn("b_start%3Aint=60", view.batch_next_url)
