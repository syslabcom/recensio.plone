from recensio.plone.utils import getFormatter
from unittest import TestCase


class TestGetFormatter(TestCase):
    """Test copied almost verbatim from the docstring of
    recensio.contenttypes.citation.getFormatter."""

    def test_to(self):
        """Test a formatter that returns a string like "1 to 2"."""
        formatter = getFormatter(", ", ", ", " to ")
        self.assertEqual(formatter("1", "2", "3", "4"), "1, 2, 3 to 4")

        self.assertEqual(formatter("1", None, None, "2"), "1 to 2")

        self.assertEqual(formatter("1", None, "2", None), "1, 2")

        self.assertEqual(formatter(None, None, "1", "2"), "1 to 2")

        self.assertEqual(formatter("1", "2"), "1, 2")

        self.assertEqual(formatter(None, None, None, None), "")

    def test_rezensent(self):
        """Because we have complex requirements, here is a real example."""
        rezensent = getFormatter(", ")
        item = getFormatter(", ", ", ", ". ", ", ", ": ", ", ")
        mag_year = getFormatter("/")
        mag_number_and_year = getFormatter(", ", ", ", " ")
        full_citation_inner = getFormatter(": review of: ", ", in: ", ", ")

        def full_citation(*args):
            rezensent_string = rezensent(*args[0:2])
            item_string = item(*args[2:9])
            mag_year_string = mag_year(*args[12:14])
            mag_year_string = mag_year_string and "(" + mag_year_string + ")" or None
            mag_number_and_year_string = mag_number_and_year(
                args[9], args[10], args[11], mag_year_string
            )
            return full_citation_inner(
                rezensent_string, item_string, mag_number_and_year_string, args[14]
            )

        (
            rezensent_nachname,
            rezensent_vorname,
            werkautor_nachname,
            werkautor_vorname,
            werktitel,
            werk_untertitel,
            erscheinungsort,
            verlag,
            jahr,
            zs_titel,
            nummer,
            heftnummer,
            gezaehltes_jahr,
            erscheinungsjahr,
            url_recensio,
        ) = (
            "rezensent_nachname",
            "rezensent_vorname",
            "werkautor_nachname",
            "werkautor_vorname",
            "werktitel",
            "werk_untertitel",
            "erscheinungsort",
            "verlag",
            "jahr",
            "zs_titel",
            "nummer",
            "heftnummer",
            "gezaehltes_jahr",
            "erscheinungsjahr",
            "url_recensio",
        )
        example_args = (
            rezensent_nachname,
            rezensent_vorname,
            werkautor_nachname,
            werkautor_vorname,
            werktitel,
            werk_untertitel,
            erscheinungsort,
            verlag,
            jahr,
            zs_titel,
            nummer,
            heftnummer,
            gezaehltes_jahr,
            erscheinungsjahr,
            url_recensio,
        )
        self.assertEqual(
            full_citation(*example_args),
            "rezensent_nachname, "
            "rezensent_vorname: review of: werkautor_nachname, werkautor_vorname, "
            "werktitel. werk_untertitel, "
            "erscheinungsort: verlag, jahr, "
            "in: zs_titel, nummer, heftnummer (gezaehltes_jahr/erscheinungsjahr), "
            "url_recensio",
        )
