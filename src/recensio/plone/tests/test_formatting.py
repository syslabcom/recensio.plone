from recensio.plone.behaviors.authors import Authors
from recensio.plone.behaviors.authors import IAuthors
from recensio.plone.behaviors.base import Base
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.editorial import Editorial
from recensio.plone.behaviors.editorial import IEditorial
from recensio.plone.browser.review import ReviewArticleCollectionView
from recensio.plone.browser.review import ReviewArticleJournalView
from recensio.plone.browser.review import ReviewExhibitionView
from recensio.plone.browser.review import ReviewJournalView
from recensio.plone.browser.review import ReviewMonographView
from recensio.plone.content.review_article_collection import ReviewArticleCollection
from recensio.plone.content.review_article_journal import ReviewArticleJournal
from recensio.plone.content.review_exhibition import ReviewExhibition
from recensio.plone.content.review_journal import ReviewJournal
from recensio.plone.content.review_monograph import ReviewMonograph
from unittest.mock import Mock
from unittest.mock import patch
from zope.component import provideAdapter
from zope.i18n import translate

import unittest


class TestDecoratedTitle(unittest.TestCase):
    """Test the `getDecoratedTitle` method for different types."""

    maxDiff = 1024

    def test_decorated_title_review_monograph(self):
        """Test `ReviewMonographView.getDecoratedTitle()`"""
        review = ReviewMonograph()
        review_view = ReviewMonographView(review, None)
        review.title = "Plone 4.0"
        review.subtitle = "Das Benutzerhandbuch"
        review.additionalTitles = [{"title": "Plone 4", "subtitle": "Benutzerhandbuch"}]
        review_view.formatted_authors_editorial = (
            lambda: "Patrick Gerken / Alexander Pilz"
        )
        mock_author = Mock()
        mock_author.firstname = "Cillian"
        mock_author.lastname = "de Roiste"
        mock_relation = Mock()
        mock_relation.to_object = mock_author
        review.reviewAuthors = [mock_relation]
        provideAdapter(Base, provides=IBase)
        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Patrick Gerken / Alexander Pilz: Plone 4.0. Das Benutzerhandbuch / "
                    "Plone 4. Benutzerhandbuch "
                    "(reviewed by Cillian de Roiste)",
                )

    def test_decorated_title_review_journal(self):
        """Test `ReviewJournalView.getDecoratedTitle()`"""
        review = ReviewJournal()
        review_view = ReviewJournalView(review, None)
        review.title = "Plone Mag"
        review.subtitle = None
        review.translatedTitleJournal = "Plöne Mág"
        mock_author = Mock()
        mock_author.firstname = "Cillian"
        mock_author.lastname = "de Roiste"
        mock_relation = Mock()
        mock_relation.to_object = mock_author
        review.reviewAuthors = [mock_relation]
        review.yearOfPublication = "2009"
        review.officialYearOfPublication = "2010"
        review.volumeNumber = "1"
        review.issueNumber = "3"
        provideAdapter(Base, provides=IBase)
        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Plone Mag [Plöne Mág], 1 (2010/2009), 3 (reviewed by Cillian de Roiste)",
                )

    @patch.object(
        ReviewArticleJournalView,
        "formatted_authors_editorial",
        lambda x: "Patrick Gerken / Alexander Pilz",
    )
    @patch.object(ReviewArticleJournalView, "page_start_end_in_print_article", "42-48")
    def test_decorated_title_review_article_journal(self):
        """Test `ReviewArticleJournalView.getDecoratedTitle()`"""
        review = ReviewArticleJournal()
        review_view = ReviewArticleJournalView(review, None)
        review.title = "The Plone Story"
        review.subtitle = "A CMS through the ages"
        review.translatedTitle = "Die Plöne-Geschichte. Ein CMS im Wandel der Zeit"
        review.titleJournal = "Plone Mag"
        review.translatedTitleJournal = "Plöne Mág"
        mock_author = Mock()
        mock_author.firstname = "Cillian"
        mock_author.lastname = "de Roiste"
        mock_relation = Mock()
        mock_relation.to_object = mock_author
        review.reviewAuthors = [mock_relation]
        review.yearOfPublication = "2009"
        review.officialYearOfPublication = "2010"
        review.volumeNumber = "1"
        review.issueNumber = "3"
        provideAdapter(Base, provides=IBase)
        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Patrick Gerken / Alexander Pilz: "
                    "The Plone Story. A CMS through the ages "
                    "[Die Plöne-Geschichte. Ein CMS im Wandel der Zeit], "
                    "in: Plone Mag [Plöne Mág], "
                    "1 (2010/2009), 3, p. 42-48 (reviewed by Cillian de Roiste)",
                )

    @patch.object(
        ReviewArticleCollectionView,
        "formatted_authors",
        lambda x: "Patrick Gerken / Alexander Pilz",
    )
    @patch.object(
        ReviewArticleCollectionView, "page_start_end_in_print_article", "73-78"
    )
    def test_decorated_title_review_article_collection(self):
        """Test `ReviewArticleCollectionView.getDecoratedTitle()`"""
        review = ReviewArticleCollection()
        review_view = ReviewArticleCollectionView(review, None)
        review.title = "Plone 4.0"
        review.subtitle = "Das Benutzerhandbuch"
        review.translatedTitle = "Plone 4.0. The User Manual"
        review.titleEditedVolume = "Handbuch der Handbücher"
        review.subtitleEditedVolume = "Betriebsanleitungen, Bauanleitungen und mehr"
        review.translatedTitleEditedVolume = "Handbook of Handbooks"
        mock_author = Mock()
        mock_author.firstname = "Cillian"
        mock_author.lastname = "de Roiste"
        mock_relation = Mock()
        mock_relation.to_object = mock_author
        review.reviewAuthors = [mock_relation]
        mock_editor = Mock()
        mock_editor.firstname = "Karl"
        mock_editor.lastname = "Kornfeld"
        mock_relation2 = Mock()
        mock_relation2.to_object = mock_editor
        review.editorial = [mock_relation2]
        provideAdapter(Base, provides=IBase)
        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Patrick Gerken / Alexander Pilz: Plone 4.0. Das Benutzerhandbuch "
                    "[Plone 4.0. The User Manual], "
                    "in: Karl Kornfeld (Hg.): Handbuch der Handbücher. "
                    "Betriebsanleitungen, Bauanleitungen und mehr "
                    "[Handbook of Handbooks], "
                    "p. 73-78 (reviewed by Cillian de Roiste)",
                )

    def _make_review_exhibition(self):
        review = ReviewExhibition()
        mock_author = Mock()
        mock_author.firstname = "Cillian"
        mock_author.lastname = "de Roiste"
        mock_relation = Mock()
        mock_relation.to_object = mock_author
        review.reviewAuthors = [mock_relation]
        review.dates = [{"place": "München", "runtime": ""}]
        mock_curator = Mock()
        mock_curator.firstname = "Alexander"
        mock_curator.lastname = "Pilz"
        mock_relation2 = Mock()
        mock_relation2.to_object = mock_curator
        review.curators = [mock_relation2]
        provideAdapter(Base, provides=IBase)
        return review

    def test_decorated_title_review_exhibition_title(self):
        review = self._make_review_exhibition()
        review_view = ReviewExhibitionView(review, None)

        review.title = "Algol"
        review.subtitle = "Eine Retrospektive"
        review.isPermanentExhibition = False
        review.exhibiting_institution = [{"name": "Museum für Software", "gnd": ""}]
        review.exhibiting_organisation = [
            {"name": "Verein für Softwareerhaltung", "gnd": ""}
        ]

        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Museum für Software: Algol. Eine Retrospektive, München "
                    "(Exhibition reviewed by Cillian de Roiste)",
                )

    def test_decorated_title_review_exhibition_institution(self):
        review = self._make_review_exhibition()
        review_view = ReviewExhibitionView(review, None)
        review.title = None
        review.subtitle = None
        review.isPermanentExhibition = True
        review.exhibiting_institution = [{"name": "Museum für Software", "gnd": ""}]
        review.exhibiting_organisation = [
            {"name": "Verein für Softwareerhaltung", "gnd": ""}
        ]

        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Museum für Software: Permanent Exhibition, München "
                    "(Exhibition reviewed by Cillian de Roiste)",
                )

    def test_decorated_title_review_exhibition_organisation(self):
        review = self._make_review_exhibition()
        review_view = ReviewExhibitionView(review, None)
        review.title = None
        review.subtitle = None
        review.isPermanentExhibition = True
        review.exhibiting_institution = [{"name": "", "gnd": ""}]
        review.exhibiting_organisation = [
            {"name": "Verein für Softwareerhaltung", "gnd": ""}
        ]

        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Verein für Softwareerhaltung: Permanent Exhibition, München "
                    "(Exhibition reviewed by Cillian de Roiste)",
                )

    def test_decorated_title_review_exhibition_curator(self):
        review = self._make_review_exhibition()
        review_view = ReviewExhibitionView(review, None)
        review.title = None
        review.subtitle = None
        review.isPermanentExhibition = True
        review.exhibiting_institution = [{"name": "", "gnd": ""}]
        review.exhibiting_organisation = [{"name": "", "gnd": ""}]

        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Alexander Pilz: Permanent Exhibition, München "
                    "(Exhibition reviewed by Cillian de Roiste)",
                )

    def test_decorated_title_review_exhibition_blank(self):
        review = self._make_review_exhibition()
        review_view = ReviewExhibitionView(review, None)
        review.title = None
        review.subtitle = None
        review.isPermanentExhibition = True
        review.exhibiting_institution = [{"name": "", "gnd": ""}]
        review.exhibiting_organisation = [{"name": "", "gnd": ""}]
        review.curators = []

        with patch("plone.api.portal.translate", new_callable=lambda: translate):
            with patch("plone.api.portal.get_current_language", return_value="en"):
                self.assertEqual(
                    review_view.getDecoratedTitle(),
                    "Permanent Exhibition, München "
                    "(Exhibition reviewed by Cillian de Roiste)",
                )


def person(firstname, lastname):
    mock_author = Mock()
    mock_author.firstname = firstname
    mock_author.lastname = lastname
    mock_relation = Mock()
    mock_relation.to_object = mock_author
    return mock_relation


class TestFormattedAuthorsEditorial(unittest.TestCase):
    """Test formatted authors and editorial."""

    def test_single_author_formatting(self):
        """A single author (and no editors) is returned with leading first
        name."""
        review = ReviewMonograph()
        review_view = ReviewMonographView(review, None)
        provideAdapter(Authors, provides=IAuthors)
        provideAdapter(Editorial, provides=IEditorial)

        setattr(review, "authors", [person("Tadeusz", "Kot\xc5\x82owski")])
        setattr(review, "editorial", [])
        provideAdapter(Authors, provides=IAuthors)
        self.assertEqual(
            review_view.formatted_authors_editorial(), "Tadeusz Kot\xc5\x82owski"
        )

    def test_multiple_authors_formatting(self):
        review = ReviewMonograph()
        review_view = ReviewMonographView(review, None)
        provideAdapter(Authors, provides=IAuthors)
        provideAdapter(Editorial, provides=IEditorial)

        setattr(
            review,
            "authors",
            [person("Tadeusz", "Kot\xc5\x82owski"), person("Aldous", "Huxley")],
        )
        setattr(review, "editorial", [])
        self.assertEqual(
            review_view.formatted_authors_editorial(),
            "Tadeusz Kot\xc5\x82owski / Aldous Huxley",
        )

        setattr(
            review,
            "authors",
            [person("Aldous", "Huxley"), person("Tadeusz", "Kot\xc5\x82owski")],
        )
        setattr(review, "editorial", [])
        self.assertEqual(
            review_view.formatted_authors_editorial(),
            "Aldous Huxley / Tadeusz Kot\xc5\x82owski",
        )

    def test_single_author_single_editor_formatting(self):
        review = ReviewMonograph()
        review_view = ReviewMonographView(review, None)
        provideAdapter(Authors, provides=IAuthors)
        provideAdapter(Editorial, provides=IEditorial)

        setattr(review, "authors", [person("Aldous", "Huxley")])
        setattr(review, "editorial", [person("Tadeusz", "Kot\xc5\x82owski")])
        authors_editorial = "Tadeusz Kot\xc5\x82owski (ed.): Aldous Huxley"
        self.assertEqual(review_view.formatted_authors_editorial(), authors_editorial)

    def test_multiple_authors_multiple_editors_formatting(self):
        review = ReviewMonograph()
        review_view = ReviewMonographView(review, None)
        provideAdapter(Authors, provides=IAuthors)
        provideAdapter(Editorial, provides=IEditorial)

        setattr(
            review,
            "authors",
            [person("Tadeusz", "Kot\xc5\x82owski"), person("Aldous", "Huxley")],
        )
        setattr(
            review,
            "editorial",
            [person("Ed", "Itor"), person("Vitali", "Testchev")],
        )
        self.assertEqual(
            review_view.formatted_authors_editorial(),
            (
                "Ed Itor / Vitali Testchev (eds.): "
                "Tadeusz Kot\xc5\x82owski "
                "/ Aldous Huxley"
            ),
        )

        setattr(
            review,
            "authors",
            [person("Aldous", "Huxley"), person("Tadeusz", "Kot\xc5\x82owski")],
        )
        setattr(
            review,
            "editorial",
            [person("Vitali", "Testchev"), person("Ed", "Itor")],
        )
        self.assertEqual(
            review_view.formatted_authors_editorial(),
            (
                "Vitali Testchev / Ed Itor (eds.): "
                "Aldous Huxley "
                "/ Tadeusz Kot\xc5\x82owski"
            ),
        )
