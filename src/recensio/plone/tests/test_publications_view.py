from recensio.plone.browser.publications import PublicationsView

import unittest


class DummyBrain:
    def __init__(self, portal_type, effective_date="None"):
        self.portal_type = portal_type
        self.EffectiveDate = effective_date


class TestPublicationsView(unittest.TestCase):
    def _view(self, catalog_results=None):
        context = type("DummyContext", (), {})()
        context.portal_catalog = lambda **kwargs: catalog_results or []
        request = type("DummyRequest", (), {})()
        return PublicationsView(context, request)

    def test_publication_letter_normalizes_titles_for_jump_links(self):
        view = self._view()

        self.assertEqual("A", view._publication_letter("Ägyptische Rundschau"))
        self.assertEqual("#", view._publication_letter("123 Journal"))

    def test_publication_stats_count_descendants_and_latest_review(self):
        view = self._view(
            [
                DummyBrain("Issue", "2026-03-29"),
                DummyBrain("Review Journal", "2026-03-28"),
                DummyBrain("Volume", "2026-03-20"),
                DummyBrain("Review Monograph", "2026-03-10"),
            ]
        )

        stats = view._publication_stats("/plone/reviews/publication-a")

        self.assertEqual(1, stats["volume_count"])
        self.assertEqual(1, stats["issue_count"])
        self.assertEqual(2, stats["review_count"])
        self.assertEqual("2026-03-28", stats["latest_review_date"])

    def test_publication_sections_and_jump_links_follow_available_letters(self):
        view = self._view()
        view.publications = lambda: [
            {"initial": "A", "title": "A Journal"},
            {"initial": "N", "title": "New Journal"},
            {"initial": "N", "title": "Next Journal"},
        ]

        sections = view.publication_sections()
        jump_links = view.publication_jump_links()

        self.assertEqual(["A", "N"], [section["label"] for section in sections])
        self.assertEqual(2, len(sections[1]["publications"]))
        self.assertTrue(
            next(item for item in jump_links if item["label"] == "A")["enabled"]
        )
        self.assertTrue(
            next(item for item in jump_links if item["label"] == "N")["enabled"]
        )
        self.assertFalse(
            next(item for item in jump_links if item["label"] == "B")["enabled"]
        )
