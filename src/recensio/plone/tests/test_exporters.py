"""Tests for recensio.plone.export exporter classes."""

from datetime import datetime
from io import BytesIO
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedBlobFile
from recensio.plone.export import BVIDExporter
from recensio.plone.export import ChroniconExporter
from recensio.plone.export import LZAExporter
from recensio.plone.export import MissingBVIDExporter
from recensio.plone.export import register_doi
from recensio.plone.export import register_doi_raw
from recensio.plone.export import StatusFailureAlreadyInProgress
from recensio.plone.export import StatusSuccessFileCreated
from recensio.plone.export import StatusSuccessFileExists
from recensio.plone.interfaces import IRecensioExporter
from recensio.plone.interfaces import IRecensioPloneLayer
from recensio.plone.testing import RECENSIO_PLONE_FUNCTIONAL_TESTING
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING
from reportlab.pdfgen.canvas import Canvas
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import PropertyMock
from zipfile import ZipFile
from zope.component import getFactoriesFor
from zope.interface import alsoProvides

import requests
import unittest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_review(container, portal_type="Review Monograph", **kw):
    """Create a minimal review inside *container* and return it."""
    obj_id = kw.pop("id", "review-%s" % portal_type.replace(" ", "-").lower())
    with api.env.adopt_user(SITE_OWNER_NAME):
        review = api.content.create(
            type=portal_type,
            id=obj_id,
            title=kw.pop("title", "A review"),
            container=container,
            **kw,
        )
    return review


def _make_container(portal):
    """Return a Publication / Volume / Issue hierarchy suitable for tests."""
    with api.env.adopt_user(SITE_OWNER_NAME):
        folder = api.content.create(
            type="Folder",
            id="test-reviews",
            title="Test Reviews",
            container=portal,
        )
        pub = api.content.create(
            type="Publication",
            id="test-pub",
            title="Test Publication",
            container=folder,
        )
        vol = api.content.create(
            type="Volume",
            id="test-vol",
            title="Test Volume",
            container=pub,
        )
        issue = api.content.create(
            type="Issue",
            id="test-issue",
            title="Test Issue",
            container=vol,
        )
    return pub, vol, issue


# ---------------------------------------------------------------------------
# Status objects
# ---------------------------------------------------------------------------


class TestStatusObjects(unittest.TestCase):

    def test_success_file_created_repr(self):
        s = StatusSuccessFileCreated("myfile.zip")
        self.assertIn("myfile.zip", repr(s))
        self.assertTrue(s.value)

    def test_success_file_exists_repr(self):
        s = StatusSuccessFileExists("myfile.zip", "2026-01-01")
        self.assertIn("myfile.zip", repr(s))
        self.assertTrue(s.value)

    def test_failure_in_progress_repr(self):
        s = StatusFailureAlreadyInProgress("2026-01-01T10:00:00")
        self.assertIn("2026-01-01", repr(s))
        self.assertFalse(s.value)


# ---------------------------------------------------------------------------
# BVIDExporter
# ---------------------------------------------------------------------------


class TestBVIDExporter(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        pub, vol, self.issue = _make_container(self.portal)

    def tearDown(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            api.content.delete(self.portal["test-reviews"])

    def _make_review_with_bv(self, bv="BV12345", **kw):
        review = _make_review(self.issue, **kw)
        review.bv = bv
        return review

    def test_add_review_without_bv_is_ignored(self):
        review = _make_review(self.issue)
        review.bv = None
        exporter = BVIDExporter()
        exporter.add_review(review)
        self.assertEqual(exporter.items, [])

    def test_add_review_with_bv_appends_url(self):
        review = self._make_review_with_bv()
        exporter = BVIDExporter()
        exporter.add_review(review)
        self.assertEqual(len(exporter.items), 1)
        bv, url = exporter.items[0]
        self.assertEqual(bv, "BV12345")
        self.assertIn("review-", url)

    def test_add_review_uses_canonical_uri_when_configured(self):
        review = self._make_review_with_bv()
        review.use_canonical_uri_for_bvid = True
        review.canonical_uri = "https://example.org/canonical"
        exporter = BVIDExporter()
        exporter.add_review(review)
        _, url = exporter.items[0]
        self.assertEqual(url, "https://example.org/canonical")

    def test_add_review_falls_back_to_absolute_url_when_canonical_empty(self):
        review = self._make_review_with_bv()
        review.use_canonical_uri_for_bvid = True
        review.canonical_uri = ""
        exporter = BVIDExporter()
        exporter.add_review(review)
        _, url = exporter.items[0]
        self.assertTrue(url.startswith("http"))

    def test_bv_and_url_captured_in_items(self):
        review = self._make_review_with_bv(bv="BV99999")
        review.canonical_uri = "https://example.org/r"
        review.use_canonical_uri_for_bvid = True
        exporter = BVIDExporter()
        exporter.add_review(review)
        self.assertEqual(len(exporter.items), 1)
        bv, url = exporter.items[0]
        self.assertEqual(bv, "BV99999")
        self.assertEqual(url, "https://example.org/r")


# ---------------------------------------------------------------------------
# MissingBVIDExporter
# ---------------------------------------------------------------------------


class TestMissingBVIDExporter(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        pub, vol, self.issue = _make_container(self.portal)

    def tearDown(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            api.content.delete(self.portal["test-reviews"])

    def test_review_without_bv_is_recorded(self):
        review = _make_review(self.issue)
        review.bv = None
        review.isbn = "978-3-16-148410-0"
        exporter = MissingBVIDExporter()
        exporter.add_review(review)
        self.assertEqual(len(exporter.items), 1)
        uid, isbn_or_issn = exporter.items[0]
        self.assertEqual(uid, review.UID())
        self.assertEqual(isbn_or_issn, "978-3-16-148410-0")

    def test_review_with_bv_is_skipped(self):
        review = _make_review(self.issue)
        review.bv = "BV12345"
        exporter = MissingBVIDExporter()
        exporter.add_review(review)
        self.assertEqual(exporter.items, [])

    def test_review_without_isbn_or_issn_records_empty_string(self):
        review = _make_review(self.issue)
        review.bv = None
        review.isbn = None
        review.issn = None
        exporter = MissingBVIDExporter()
        exporter.add_review(review)
        uid, isbn_or_issn = exporter.items[0]
        self.assertEqual(isbn_or_issn, "")

    def test_export_filename(self):
        self.assertEqual(MissingBVIDExporter.export_filename, "missing_bvid.csv")


# ---------------------------------------------------------------------------
# ChroniconExporter
# ---------------------------------------------------------------------------


class TestChroniconExporter(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.pub, self.vol, self.issue = _make_container(self.portal)

    def tearDown(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            api.content.delete(self.portal["test-reviews"])

    def test_get_issue_filename_with_issue(self):
        exporter = ChroniconExporter()
        exporter.current_issue = self.issue
        filename = exporter.get_issue_filename()
        self.assertIn("recensio_", filename)
        self.assertIn("test-pub", filename)
        self.assertIn("test-vol", filename)
        self.assertIn("test-issue", filename)
        self.assertTrue(filename.endswith(".xml"))

    def test_get_issue_filename_without_issue_uses_volume(self):
        exporter = ChroniconExporter()
        exporter.current_issue = self.vol
        filename = exporter.get_issue_filename()
        self.assertNotIn("test-issue", filename)
        self.assertIn("test-vol", filename)
        self.assertTrue(filename.endswith(".xml"))

    def test_add_review_calls_xml_view(self):
        review = _make_review(self.issue)
        xml_view = MagicMock(return_value="<review/>")
        exporter = ChroniconExporter()
        with patch.object(
            review, "restrictedTraverse", return_value=xml_view
        ) as mock_rt:
            exporter.add_review(review)
            mock_rt.assert_called_once_with(exporter.xml_view_name)
        xml_view.assert_called_once()
        self.assertEqual(exporter.reviews_xml, ["<review/>"])
        self.assertEqual(exporter.current_issue, self.issue)

    def test_add_review_finishes_previous_issue_on_change(self):
        review1 = _make_review(self.issue, id="r1")
        # create a second issue
        with api.env.adopt_user(SITE_OWNER_NAME):
            issue2 = api.content.create(
                type="Issue", id="issue2", title="Issue 2", container=self.vol
            )
        review2 = _make_review(issue2, id="r2")

        exporter = ChroniconExporter()
        xml1 = MagicMock(return_value="<review id='1'/>")
        xml2 = MagicMock(return_value="<review id='2'/>")

        # Patch finish_issue so we can record when it fires
        finished = []

        def capturing_finish():
            finished.append(exporter.current_issue)
            # minimal stub: just clear state without rendering template
            exporter.issues_xml[exporter.get_issue_filename()] = "stub"
            exporter.reviews_xml = []
            exporter.current_issue = None

        exporter.finish_issue = capturing_finish

        with patch.object(review1, "restrictedTraverse", return_value=xml1):
            exporter.add_review(review1)
        with patch.object(review2, "restrictedTraverse", return_value=xml2):
            exporter.add_review(review2)

        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0], self.issue)
        self.assertEqual(exporter.current_issue, issue2)

    def test_running_export_returns_none_when_no_cache(self):
        exporter = ChroniconExporter()
        with patch("recensio.plone.export.path.exists", return_value=False):
            self.assertIsNone(exporter.running_export())

    def test_export_produces_zip_with_xml_entries(self):
        exporter = ChroniconExporter()
        exporter.issues_xml = {"recensio_test-pub_test-vol_test-issue.xml": "<rms/>"}
        zipdata = exporter.get_zipdata()
        zf = ZipFile(BytesIO(zipdata))
        self.assertIn("recensio_test-pub_test-vol_test-issue.xml", zf.namelist())

    def test_export_returns_in_progress_when_cache_exists(self):
        from datetime import datetime

        exporter = ChroniconExporter()
        exporter.issues_xml = {}
        with patch.object(exporter, "running_export", return_value=datetime.now()):
            result = exporter.export()
        self.assertIsInstance(result, StatusFailureAlreadyInProgress)


# ---------------------------------------------------------------------------
# LZAExporter
# ---------------------------------------------------------------------------


class TestLZAExporter(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.pub, self.vol, self.issue = _make_container(self.portal)
        cache_dir = TemporaryDirectory()
        self.addCleanup(cache_dir.cleanup)
        cache_patch = patch.object(
            LZAExporter,
            "cache_filename",
            new_callable=PropertyMock,
            return_value=cache_dir.name + "/lza_cache.zip",
        )
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        self.review_view = MagicMock()
        self.review_view.get_review_pdf.return_value = NamedBlobFile(
            data=b"%PDF-test", filename="review.pdf"
        )

    def tearDown(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            api.content.delete(self.portal["test-reviews"])

    def test_export_filename(self):
        self.assertEqual(LZAExporter.export_filename, "export_lza_xml.zip")

    def test_xml_view_name(self):
        self.assertEqual(LZAExporter.xml_view_name, "@@xml-lza")

    def test_set_and_check_exported_flag(self):
        review = _make_review(self.issue)
        exporter = LZAExporter()
        self.assertFalse(exporter._is_exported(review))
        exporter._set_exported(review)
        self.assertTrue(exporter._is_exported(review))

    def test_set_exported_false_clears_flag(self):
        review = _make_review(self.issue)
        exporter = LZAExporter()
        exporter._set_exported(review, True)
        exporter._set_exported(review, False)
        self.assertFalse(exporter._is_exported(review))

    def test_already_exported_review_is_skipped(self):
        review = _make_review(self.issue)
        exporter = LZAExporter()
        exporter._set_exported(review)
        xml_view = MagicMock(return_value="<review/>")
        with patch.object(review, "restrictedTraverse", return_value=xml_view):
            exporter.add_review(review)
        xml_view.assert_not_called()
        self.assertEqual(exporter.reviews_xml, [])

    def test_new_review_is_added_without_marking(self):
        review = _make_review(self.issue)
        exporter = LZAExporter()
        xml_view = MagicMock(return_value="<review/>")
        review_view = MagicMock()
        review_view.get_review_pdf.return_value = None
        with patch.object(review, "restrictedTraverse", return_value=xml_view):
            with patch(
                "recensio.plone.export.api.content.get_view", return_value=review_view
            ):
                exporter.add_review(review)
        self.assertFalse(exporter._is_exported(review))
        self.assertEqual(exporter.reviews_xml, ["<review/>"])

    def test_reviews_are_marked_when_archive_is_stored(self):
        # Given real reviews, XML rendering and PDF blobs.
        reviews = [_make_review(self.issue, id="r1"), _make_review(self.issue, id="r2")]
        exporter = LZAExporter()
        for review in reviews:
            with patch(
                "recensio.plone.export.api.content.get_view",
                return_value=self.review_view,
            ):
                exporter.add_review(review)
        filename = exporter.get_issue_filename()

        # When the complete archive is generated and stored on the portal.
        result = exporter.export()

        # Then the stored ZIP contains both reviews and their PDFs.
        self.assertIsInstance(result, StatusSuccessFileCreated)
        self.assertTrue(result.value)
        archive = self.portal[exporter.export_filename].file
        with ZipFile(BytesIO(archive.data)) as zf:
            xml = zf.read(filename).decode("utf-8")
            for review in reviews:
                self.assertIn(review.UID(), xml)
                pdf_path = "/".join(review.getPhysicalPath()[2:]) + ".pdf"
                self.assertEqual(zf.read(pdf_path), b"%PDF-test")
                self.assertTrue(exporter._is_exported(review))

    def test_review_stays_unmarked_when_zip_generation_fails(self):
        # Given a collected review with real XML rendering.
        review = _make_review(self.issue)
        exporter = LZAExporter()
        with patch(
            "recensio.plone.export.api.content.get_view", return_value=self.review_view
        ):
            exporter.add_review(review)

        # When ZIP writing fails.
        with patch.object(exporter, "write_zipfile", side_effect=OSError("ZIP failed")):
            with self.assertRaises(OSError):
                exporter.export()

        # Then the review remains eligible for a later export.
        self.assertFalse(exporter._is_exported(review))

    def test_review_stays_unmarked_when_export_is_in_progress(self):
        # Given a collected review and an already running export.
        review = _make_review(self.issue)
        exporter = LZAExporter()
        with patch(
            "recensio.plone.export.api.content.get_view", return_value=self.review_view
        ):
            exporter.add_review(review)

        # When export returns its truthy failure status object.
        with patch.object(exporter, "running_export", return_value=datetime.now()):
            result = exporter.export()

        # Then status.value, rather than object truthiness, controls marking.
        self.assertIsInstance(result, StatusFailureAlreadyInProgress)
        self.assertTrue(result)
        self.assertFalse(result.value)
        self.assertFalse(exporter._is_exported(review))

    def test_review_stays_unmarked_when_archive_storage_fails(self):
        # Given a collected review and an existing portal-root archive object.
        review = _make_review(self.issue)
        exporter = LZAExporter()
        with patch(
            "recensio.plone.export.api.content.get_view", return_value=self.review_view
        ):
            exporter.add_review(review)
        archive = api.content.create(
            type="File", id=exporter.export_filename, container=self.portal
        )

        # When assigning the generated ZIP to the file field fails.
        with patch.object(
            type(archive.aq_base),
            "file",
            new_callable=PropertyMock,
            create=True,
            side_effect=OSError("storage failed"),
        ):
            with self.assertRaises(OSError):
                exporter.export()

        # Then collection has not persisted the exported flag.
        self.assertFalse(exporter._is_exported(review))

    def test_pdf_included_in_zip_when_present(self):
        review = _make_review(self.issue)
        exporter = LZAExporter()
        xml_view = MagicMock(return_value="<review/>")
        fake_pdf = MagicMock()
        fake_pdf.open.return_value.__enter__ = lambda s: s
        fake_pdf.open.return_value.__exit__ = MagicMock(return_value=False)
        fake_pdf_blob = MagicMock()
        fake_pdf_blob.read.side_effect = [b"%PDF-fake", b""]
        fake_pdf.open.return_value = fake_pdf_blob
        review_view = MagicMock()
        review_view.get_review_pdf.return_value = fake_pdf

        with patch.object(review, "restrictedTraverse", return_value=xml_view):
            with patch(
                "recensio.plone.export.api.content.get_view", return_value=review_view
            ):
                exporter.add_review(review)

        exporter.issues_xml["dummy.xml"] = "<rms/>"
        buf = BytesIO()
        zf = ZipFile(buf, "w")
        exporter.write_zipfile(zf)
        zf.close()
        buf.seek(0)
        names = ZipFile(buf).namelist()
        pdf_entries = [n for n in names if n.endswith(".pdf")]
        self.assertEqual(len(pdf_entries), 1)


# ---------------------------------------------------------------------------
# Factory registrations and the @@metadata-export runner view
# ---------------------------------------------------------------------------


class TestExporterFactoryRegistrations(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def test_all_exporters_registered_as_factories(self):
        names = sorted(name for name, _factory in getFactoriesFor(IRecensioExporter))
        self.assertEqual(
            names,
            [
                "bvid_exporter",
                "chronicon_exporter",
                "lza_exporter",
                "missing_bvid_exporter",
            ],
        )


class TestMetadataExportView(unittest.TestCase):

    layer = RECENSIO_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.pub, self.vol, self.issue = _make_container(self.portal)
        self.review = _make_review(self.issue)
        for obj in (self.issue, self.review):
            api.content.transition(obj=obj, to_state="published")

    def tearDown(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            for filename in (
                "export_metadata_xml.zip",
                "export_lza_xml.zip",
                "bvid_export.csv",
                "missing_bvid.csv",
            ):
                if self.portal.get(filename):
                    api.content.delete(self.portal[filename])
            api.content.delete(self.portal["test-reviews"])

    def test_export_creates_files_then_nothing_to_do(self):
        view = self.portal.restrictedTraverse("@@metadata-export")
        output = view()
        self.assertIn("chronicon_exporter", output)
        self.assertIn("created", output)
        self.assertIn("export_metadata_xml.zip", self.portal.objectIds())

        view = self.portal.restrictedTraverse("@@metadata-export")
        output = view()
        self.assertIn("Nothing to do", output)

    def test_lza_export_includes_uploaded_pdfs_using_registered_review_views(self):
        alsoProvides(self.layer["request"], IRecensioPloneLayer)
        pdf = BytesIO()
        canvas = Canvas(pdf)
        canvas.drawString(72, 720, "LZA export regression")
        canvas.save()
        pdf_data = pdf.getvalue()
        self.review.pdf = NamedBlobFile(
            data=pdf_data, filename="monograph.pdf", contentType="application/pdf"
        )
        journal_review = _make_review(
            self.issue,
            portal_type="Review Journal",
            pdf=NamedBlobFile(
                data=pdf_data, filename="journal.pdf", contentType="application/pdf"
            ),
        )
        api.content.transition(obj=journal_review, to_state="published")

        with TemporaryDirectory() as cache_dir:
            with patch.object(
                LZAExporter,
                "cache_filename",
                new_callable=PropertyMock,
                return_value=cache_dir + "/lza_cache.zip",
            ):
                output = self.portal.restrictedTraverse("@@metadata-export")()

        self.assertIn("lza_exporter: export_lza_xml.zip created", output)
        archive = self.portal["export_lza_xml.zip"].file
        with ZipFile(BytesIO(archive.data)) as zf:
            xml = b"".join(
                zf.read(name) for name in zf.namelist() if name.endswith(".xml")
            )
            for review in (self.review, journal_review):
                pdf_path = "/".join(review.getPhysicalPath()[2:]) + ".pdf"
                self.assertEqual(zf.read(pdf_path), pdf_data)
                self.assertIn(review.UID().encode("utf-8"), xml)
                self.assertIn(pdf_path.encode("utf-8"), xml)
                self.assertTrue(LZAExporter()._is_exported(review))


# ---------------------------------------------------------------------------
# register_doi / register_doi_raw
# ---------------------------------------------------------------------------


class TestRegisterDoi(unittest.TestCase):

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        pub, vol, self.issue = _make_container(self.portal)
        self.review = _make_review(self.issue)

    def tearDown(self):
        with api.env.adopt_user(SITE_OWNER_NAME):
            api.content.delete(self.portal["test-reviews"])

    def _mock_settings(self):
        settings = MagicMock()
        settings.doi_registration_username = "user"
        settings.doi_registration_password = "pass"
        settings.doi_registration_url = "https://dara.example.org/api"
        registry = MagicMock()
        registry.forInterface.return_value = settings
        return registry

    def _mock_response(self, status_code):
        response = MagicMock()
        response.status_code = status_code
        response.text = ""
        response.raise_for_status.return_value = None
        return response

    def _mock_http_error(self, status_code, body=""):
        response = MagicMock()
        response.status_code = status_code
        response.text = body
        err = requests.exceptions.HTTPError(response=response)
        return err

    def test_register_doi_raw_posts_with_basic_auth(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")
        fake_response = self._mock_response(201)

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch(
                    "recensio.plone.export.requests.post", return_value=fake_response
                ) as mock_post:
                    code = register_doi_raw(self.review)

        self.assertEqual(code, 201)
        _args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["auth"], ("user", "pass"))
        self.assertIn("application/xml", kwargs["headers"]["Content-Type"])

    def test_register_doi_returns_success_on_201(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")
        fake_response = self._mock_response(201)

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch(
                    "recensio.plone.export.requests.post", return_value=fake_response
                ):
                    status, message = register_doi(self.review)

        self.assertEqual(status, "success")
        self.assertIn("registered", message)

    def test_register_doi_returns_success_on_200(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")
        fake_response = self._mock_response(200)

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch(
                    "recensio.plone.export.requests.post", return_value=fake_response
                ):
                    status, message = register_doi(self.review)

        self.assertEqual(status, "success")
        self.assertIn("updated", message.lower())

    def test_register_doi_handles_401(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")
        err = self._mock_http_error(401)

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch("recensio.plone.export.requests.post", side_effect=err):
                    status, message = register_doi(self.review)

        self.assertEqual(status, "error")
        self.assertIn("login", message.lower())

    def test_register_doi_handles_400(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")
        err = self._mock_http_error(400)

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch("recensio.plone.export.requests.post", side_effect=err):
                    status, message = register_doi(self.review)

        self.assertEqual(status, "error")
        self.assertIn("xml", message.lower())

    def test_register_doi_handles_connection_error(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch(
                    "recensio.plone.export.requests.post",
                    side_effect=OSError("connection refused"),
                ):
                    status, message = register_doi(self.review)

        self.assertEqual(status, "error")
        self.assertIn("contacting", message.lower())

    def test_register_doi_raw_rejects_non_http_scheme(self):
        registry = self._mock_settings()
        registry.forInterface.return_value.doi_registration_url = "file:///etc/passwd"
        xml_view = MagicMock(return_value="<dara_xml/>")

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with self.assertRaises(ValueError):
                    register_doi_raw(self.review)

    def test_register_doi_handles_valueerror(self):
        registry = self._mock_settings()
        xml_view = MagicMock(return_value="<dara_xml/>")

        with patch("recensio.plone.export.queryUtility", return_value=registry):
            with patch.object(self.review, "restrictedTraverse", return_value=xml_view):
                with patch(
                    "recensio.plone.export.requests.post",
                    side_effect=ValueError("bad url"),
                ):
                    status, message = register_doi(self.review)

        self.assertEqual(status, "error")
        self.assertIn("updating", message.lower())
