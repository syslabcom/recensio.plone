from datetime import datetime
from datetime import timedelta
from datetime import timezone
from DateTime import DateTime
from io import StringIO
from os import path
from os import remove
from os import stat
from plone import api
from plone.namedfile.file import NamedBlobFile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.controlpanel.settings import IRecensioSettings
from recensio.plone.interfaces import IRecensioExporter
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
from zExceptions import NotFound
from zipfile import ZipFile
from zope.annotation import IAnnotations
from zope.component import queryUtility
from zope.component.factory import Factory
from zope.component.hooks import getSite
from zope.component.interfaces import IFactory
from zope.interface import implementer

import csv
import logging
import requests
import tempfile


log = logging.getLogger(__name__)


class ContainerExportView(BrowserView):
    template = ViewPageTemplateFile("browser/templates/export_container_contextless.pt")


class StatusSuccess:
    value = True

    def __repr__(self):
        return "Success"


class StatusFailure:
    value = False

    def __repr__(self):
        return "Failure"


class StatusSuccessFile(StatusSuccess):
    def __init__(self, filename):
        self.filename = filename


class StatusSuccessFileCreated(StatusSuccessFile):
    def __repr__(self):
        return f"{self.filename} created"


class StatusSuccessFileExists(StatusSuccessFile):
    def __init__(self, filename, modified=None):
        self.filename = filename
        self.modified = modified

    def __repr__(self):
        return f"current file found ({self.filename}, {self.modified})"


class StatusFailureAlreadyInProgress(StatusFailure):
    def __init__(self, since=None):
        self.since = since

    def __repr__(self):
        return f"export in progress since {self.since}"


class BaseExporter:
    def get_export_obj(self, portal):
        try:
            export_xml = portal.unrestrictedTraverse(self.export_filename)
        except (KeyError, ValueError, NotFound):
            export_xml = None
        return export_xml

    def is_recent(self, export_xml_obj):
        if export_xml_obj is not None:
            modified = export_xml_obj.modified()
            if DateTime() - 6 < modified:
                return True
        return False


@implementer(IRecensioExporter)
class ChroniconExporter(BaseExporter):
    """Export review metadata (but not full text) to a zip file containing one
    XML file per issue/volume"""

    export_filename = "export_metadata_xml.zip"
    xml_view_name = "@@xml"

    def __init__(self):
        self.current_issue = None
        self.issues_xml = {}
        self.reviews_xml = []

    def get_parent(self, meta_type):
        if not self.current_issue:
            return None
        return IParentGetter(self.current_issue).get_parent_object_of_type(meta_type)

    def get_publication_shortname(self):
        return self.get_parent("Publication").getId()

    def get_publication_title(self):
        return self.get_parent("Publication").Title()

    def get_package_journal_volume(self):
        return self.get_parent("Volume").getId()

    def get_package_journal_volume_title(self):
        return self.get_parent("Volume").Title()

    def get_package_journal_pubyear(self):
        volume = self.get_parent("Volume")
        return getattr(volume, "year_of_publication", None) or None

    def get_package_journal_issue(self):
        issue = self.get_parent("Issue")
        if issue is None:
            return None
        return issue.getId()

    def get_package_journal_issue_title(self):
        issue = self.get_parent("Issue")
        if issue is None:
            return None
        return issue.Title()

    def get_issue_filename(self):
        issue = self.get_package_journal_issue()
        if issue is not None:
            return "recensio_{}_{}_{}.xml".format(
                self.get_publication_shortname(),
                self.get_package_journal_volume(),
                issue,
            )
        else:
            return "recensio_{}_{}.xml".format(
                self.get_publication_shortname(),
                self.get_package_journal_volume(),
            )

    def finish_issue(self):
        view = ContainerExportView(self.current_issue, self.current_issue.REQUEST)
        options = {
            "package": {
                "publication_title": self.get_publication_title,
                "package_journal_volume_title": self.get_package_journal_volume_title,
                "package_journal_pubyear": self.get_package_journal_pubyear,
                "package_journal_issue_title": self.get_package_journal_issue_title,
            },
            "reviews": self.reviews_xml,
        }
        filename = self.get_issue_filename()
        xml = view.template(**options)
        self.issues_xml[filename] = xml
        self.reviews_xml = []
        self.current_issue = None

    @property
    def cache_filename(self):
        return path.join(tempfile.gettempdir(), "chronicon_cache.zip")

    def write_zipfile(self, zipfile):
        for filename, xml in self.issues_xml.items():
            zipfile.writestr(filename, bytes(xml.encode("utf-8")))

    def get_zipdata(self):
        cache_file_name = self.cache_filename
        try:
            open(cache_file_name, "wb").close()
            with NamedTemporaryFile(mode="w+b", suffix=".zip") as stream:
                with ZipFile(stream, "w") as zf:
                    self.write_zipfile(zf)
                stream.seek(0)
                return stream.read()
        finally:
            if path.exists(cache_file_name):
                remove(cache_file_name)

    def running_export(self):
        if path.exists(self.cache_filename):
            mtime = stat(self.cache_filename).st_mtime
            cache_time = datetime.fromtimestamp(mtime)
            if datetime.now() - cache_time < timedelta(0, 60 * 60):
                return cache_time

    def needs_to_run(self):
        portal = getSite()
        export_xml_obj = self.get_export_obj(portal)
        return not self.is_recent(export_xml_obj) and not self.running_export()

    def add_review(self, review):
        """Expects reviews of the same issue to be added consecutively"""
        review_issue = IParentGetter(review).get_parent_object_of_type("Issue")
        if review_issue is None:
            review_issue = IParentGetter(review).get_parent_object_of_type("Volume")
        if self.current_issue != review_issue:
            if self.current_issue:
                self.finish_issue()
            self.current_issue = review_issue
        self.reviews_xml.append(review.restrictedTraverse(self.xml_view_name)())

    def export(self):
        if self.current_issue:
            self.finish_issue()

        portal = getSite()
        export_xml_obj = self.get_export_obj(portal)
        cache_time = self.running_export()
        if cache_time:
            return StatusFailureAlreadyInProgress(cache_time.isoformat())

        pt = getToolByName(portal, "portal_types")
        type_info = pt.getTypeInfo("File")
        if export_xml_obj is None:
            export_xml_obj = type_info._constructInstance(portal, self.export_filename)
        export_xml_obj.file = NamedBlobFile(
            data=self.get_zipdata(),
            filename=self.export_filename,
            contentType="application/zip",
        )
        export_xml_obj.modification_date = datetime.now(timezone.utc)
        return StatusSuccessFileCreated(self.export_filename)


@implementer(IRecensioExporter)
class BVIDExporter(BaseExporter):

    export_filename = "bvid_export.csv"

    def __init__(self):
        self.items = []

    def needs_to_run(self):
        portal = getSite()
        export_file = self.get_export_obj(portal)
        return not self.is_recent(export_file)

    def add_review(self, review):
        bv = getattr(review, "bv", None)
        if bv:
            use_canonical = getattr(review, "use_canonical_uri_for_bvid", False)
            if use_canonical:
                url = getattr(review, "canonical_uri", "") or review.absolute_url()
            else:
                url = review.absolute_url()
            self.items.append((bv, url))

    def export(self):
        csvfile = StringIO()
        csvwriter = csv.writer(csvfile)

        csvwriter.writerows(self.items)

        portal = getSite()
        export_file = self.get_export_obj(portal)
        if export_file is None:
            pt = getToolByName(portal, "portal_types")
            type_info = pt.getTypeInfo("File")
            export_file = type_info._constructInstance(portal, self.export_filename)

        export_file.file = NamedBlobFile(
            data=csvfile.getvalue().encode("utf-8"),
            filename=self.export_filename,
            contentType="text/csv",
        )
        export_file.modification_date = datetime.now(timezone.utc)
        return StatusSuccessFileCreated(self.export_filename)


@implementer(IRecensioExporter)
class MissingBVIDExporter(BVIDExporter):

    export_filename = "missing_bvid.csv"

    def add_review(self, review):
        bv = getattr(review, "bv", None)
        if not bv:
            isbn_or_issn = (
                getattr(review, "isbn", None) or getattr(review, "issn", None) or ""
            )
            self.items.append((review.UID(), isbn_or_issn))


class DaraExporter(BaseExporter):
    def __init__(self):
        self.reviews_xml = []

    def add_review(self, review):
        self.reviews_xml.append(review.restrictedTraverse("@@xml-dara")())

    def export(self):
        pass


class LZAExporter(ChroniconExporter):
    """Like ChroniconExporter but
    * also exports full text (PDF)
    * only exports each review once, then never again"""

    export_filename = "export_lza_xml.zip"
    xml_view_name = "@@xml-lza"

    def __init__(self):
        super().__init__()
        self.reviews_pdf = {}

    @property
    def cache_filename(self):
        return path.join(tempfile.gettempdir(), "lza_cache.zip")

    def _set_exported(self, review, value=True):
        IAnnotations(review)["LZA_EXPORTED"] = bool(value)

    def _is_exported(self, review):
        return IAnnotations(review).get("LZA_EXPORTED")

    def add_review(self, review):
        if self._is_exported(review):
            return
        super().add_review(review)
        pdf_path = "/".join(review.getPhysicalPath()[2:]) + ".pdf"
        review_view = api.content.get_view(
            name="review", context=review, request=review.REQUEST
        )
        review_pdf = review_view.get_review_pdf()
        if review_pdf:
            self.reviews_pdf[pdf_path] = review_pdf
        self._set_exported(review)

    def write_zipfile(self, zipfile):
        super().write_zipfile(zipfile)
        for filename, review_pdf in self.reviews_pdf.items():
            pdf_blob = review_pdf.open()
            try:
                with zipfile.open(filename, "w") as zip_entry:
                    while True:
                        chunk = pdf_blob.read(64 * 1024)
                        if not chunk:
                            break
                        zip_entry.write(chunk)
            finally:
                pdf_blob.close()


BVIDExporterFactory = Factory(BVIDExporter, IFactory, "exporter")
MissingBVIDExporterFactory = Factory(MissingBVIDExporter, IFactory, "exporter")
ChroniconExporterFactory = Factory(ChroniconExporter, IFactory, "exporter")
LZAExporterFactory = Factory(LZAExporter, IFactory, "exporter")


def register_doi_raw(obj):
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IRecensioSettings)
    username = settings.doi_registration_username
    password = settings.doi_registration_password
    url = settings.doi_registration_url
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError(f"Disallowed URL scheme for DOI registration: {url!r}")

    xml = obj.restrictedTraverse("@@xml-dara")().encode("utf-8")
    response = requests.post(
        url,
        data=xml,
        headers={"Content-Type": "application/xml;charset=UTF-8"},
        auth=(username, password),
        timeout=30,
    )
    response.raise_for_status()
    return response.status_code


def register_doi(obj):
    try:
        return_code = register_doi_raw(obj)
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            message = (
                "Dara login failed - check DOI registration user name and password"
            )
        elif status_code == 400:
            message = "Request rejected by dara - check generated XML"
        elif status_code == 500:
            message = "Dara server error - try again later"
        else:
            message = f"Error returned by dara server: {e}"
        status = "error"
        log.error(message)
        body = e.response.text
        if "\n" in body:
            dump_file = NamedTemporaryFile(suffix=".html", delete=False, mode="w")
            dump_file.write(body)
            dump_file.close()
            log.info("HTTPError dumped to " + dump_file.name)
        else:
            log.error(body)
    except ValueError as e:
        exc_msg = e.__class__.__name__ + ": " + str(e)
        message = "Error while updating dara record (" + exc_msg + ")"
        status = "error"
    except OSError as e:
        exc_msg = e.__class__.__name__ + ": " + str(e)
        message = "Error contacting dara server (" + exc_msg + ")"
        status = "error"
    else:
        if return_code == 201:
            message = "DOI successfully registered"
        elif return_code == 200:
            message = "Metadata updated"
        else:
            message = f"Success (status {return_code})"
        status = "success"
    return status, message
