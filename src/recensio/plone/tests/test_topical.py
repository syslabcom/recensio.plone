from recensio.plone.browser.topical import BrowseTopicsView
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch
from urllib.parse import parse_qs
from urllib.parse import urlparse

import unittest


class DummyVdex:
    def __init__(self):
        self.calls = []

    def getVocabularyDict(self, lang=None):
        self.calls.append(lang)
        return {"language": lang}


class DummyRequest:
    def __init__(self, form=None, url="http://nohost/plone/browse-topics"):
        self.form = form or {}
        self.URL = url

    def get(self, name, default=None):
        return self.form.get(name, default)


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

    def _view(self, form=None, language="en"):
        helper, ddc_place, ddc_time, ddc_subject = self._helper()
        request = DummyRequest(form=form)
        with patch("plone.api.portal.get_current_language", return_value=language):
            with patch("plone.api.content.get_view", return_value=helper):
                view = BrowseTopicsView(Mock(), request)
        return view, ddc_place, ddc_time, ddc_subject

    @patch("plone.api.portal.get_current_language", return_value="fr")
    @patch("plone.api.content.get_view")
    def test_vocabulary_dict_uses_current_language(self, get_view, _get_language):
        helper, ddc_place, ddc_time, ddc_subject = self._helper()
        get_view.return_value = helper

        view = BrowseTopicsView(Mock(), DummyRequest())

        self.assertEqual(["fr"], ddc_place.calls)
        self.assertEqual(["fr"], ddc_time.calls)
        self.assertEqual(["fr"], ddc_subject.calls)
        self.assertEqual({"language": "fr"}, view.vocDict["ddcPlace"])

    @patch("plone.api.portal.get_current_language", return_value="de-at")
    @patch("plone.api.content.get_view")
    def test_vocabulary_dict_normalizes_language_code(self, get_view, _get_language):
        helper, ddc_place, ddc_time, ddc_subject = self._helper()
        get_view.return_value = helper

        BrowseTopicsView(Mock(), DummyRequest())

        self.assertEqual(["de"], ddc_place.calls)
        self.assertEqual(["de"], ddc_time.calls)
        self.assertEqual(["de"], ddc_subject.calls)

    def test_current_sort_defaults_to_relevance(self):
        view, _, _, _ = self._view()

        self.assertEqual("relevance", view.current_sort)
        self.assertIsNone(view.current_sort_on)
        self.assertIsNone(view.current_sort_order)
        self.assertTrue(view.show_relevance_scores)

    def test_current_sort_detects_creation_date_sort(self):
        view, _, _, _ = self._view(form={"sort_on": "created", "sort_order": "reverse"})

        self.assertEqual("created", view.current_sort)
        self.assertEqual("created", view.current_sort_on)
        self.assertEqual("reverse", view.current_sort_order)
        self.assertFalse(view.show_relevance_scores)

    def test_sort_options_preserve_current_filters_and_clear_batch(self):
        view, _, _, _ = self._view(
            form={
                "SearchableText": "rome",
                "fq": ['ddcSubject:"12"', 'ddcPlace:"4"'],
                "b_start": 20,
            }
        )

        created_option = view.sort_options[1]
        parsed = parse_qs(urlparse(created_option["url"]).query)

        self.assertEqual(["rome"], parsed["SearchableText"])
        self.assertEqual(["created"], parsed["sort_on"])
        self.assertEqual(["reverse"], parsed["sort_order"])
        self.assertEqual(
            {'ddcSubject:"12"', 'ddcPlace:"4"'},
            set(parsed["fq"]),
        )
        self.assertNotIn("b_start", parsed)

    def test_reset_facets_href_keeps_search_text_and_sort(self):
        view, _, _, _ = self._view(
            form={
                "SearchableText": "rome",
                "sort_on": "created",
                "sort_order": "reverse",
            }
        )

        parsed = parse_qs(urlparse(view.reset_facets_href()).query)

        self.assertEqual(["rome"], parsed["SearchableText"])
        self.assertEqual(["created"], parsed["sort_on"])
        self.assertEqual(["reverse"], parsed["sort_order"])
