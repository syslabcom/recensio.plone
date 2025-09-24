from collective.solr import testing as solr_testing
from plone import api
from recensio.plone.interfaces import IRecensioPloneLayer
from recensio.plone.testing import RECENSIO_PLONE_SOLR_INTEGRATION_TESTING
from zope.interface import alsoProvides
from zope.interface import noLongerProvides

import unittest


class TestAuthorSearch(unittest.TestCase):
    """"""

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

        solr_testing.activateAndReindex(self.portal)

    def tearDown(self):
        noLongerProvides(self.request, IRecensioPloneLayer)

    def test_search(self):
        self.request.form = {"authors": "Eimer"}
        view = api.content.get_view(
            context=self.portal, request=self.request, name="authorsearch"
        )
        result = view.authors
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["Title"], "Eimer, Claudio")
        self.assertEqual(result[1]["Title"], "Eimer, Kathy")
