from recensio.plone.browser.topical import BrowseTopicsView
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

import unittest


class DummyVdex:
    def __init__(self):
        self.calls = []

    def getVocabularyDict(self, lang=None):
        self.calls.append(lang)
        return {"language": lang}


class TestBrowseTopicsView(unittest.TestCase):
    def _helper(self):
        ddc_place = DummyVdex()
        ddc_time = DummyVdex()
        ddc_subject = DummyVdex()
        helper = SimpleNamespace(
            ddcPlace=SimpleNamespace(vdex=ddc_place),
            ddcTime=SimpleNamespace(vdex=ddc_time),
            ddcSubject=SimpleNamespace(vdex=ddc_subject),
        )
        return helper, ddc_place, ddc_time, ddc_subject

    @patch("plone.api.portal.get_current_language", return_value="fr")
    @patch("plone.api.content.get_view")
    def test_vocabulary_dict_uses_current_language(self, get_view, _get_language):
        helper, ddc_place, ddc_time, ddc_subject = self._helper()
        get_view.return_value = helper

        view = BrowseTopicsView(Mock(), Mock())

        self.assertEqual(["fr"], ddc_place.calls)
        self.assertEqual(["fr"], ddc_time.calls)
        self.assertEqual(["fr"], ddc_subject.calls)
        self.assertEqual({"language": "fr"}, view.vocDict["ddcPlace"])

    @patch("plone.api.portal.get_current_language", return_value="de-at")
    @patch("plone.api.content.get_view")
    def test_vocabulary_dict_normalizes_language_code(self, get_view, _get_language):
        helper, ddc_place, ddc_time, ddc_subject = self._helper()
        get_view.return_value = helper

        BrowseTopicsView(Mock(), Mock())

        self.assertEqual(["de"], ddc_place.calls)
        self.assertEqual(["de"], ddc_time.calls)
        self.assertEqual(["de"], ddc_subject.calls)
