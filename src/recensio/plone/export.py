# -* coding: utf-8 *-
from Acquisition import aq_parent
from base64 import b64encode
from datetime import datetime
from datetime import timedelta
from DateTime import DateTime
from io import FileIO
from os import path
from os import remove
from os import stat
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.interfaces import IRecensioExporter
from recensio.plone.controlpanel.settings import IRecensioSettings
from io import StringIO
from tempfile import NamedTemporaryFile
from Testing.makerequest import makerequest
from urllib.request import HTTPError
from urllib.request import Request
from urllib.request import urlopen
from zExceptions import NotFound
from zipfile import ZipFile
from zope.annotation import IAnnotations
from zope.component import queryUtility
from zope.component.factory import Factory
from zope.component.hooks import getSite
from zope.component.interfaces import IFactory
from zope.interface import implementer
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

import csv
import logging
import tempfile


log = logging.getLogger(__name__)


class StatusSuccess(object):
    value = True

    def __repr__(self):
        return "Success"


class StatusFailure(object):
    value = False

    def __repr__(self):
        return "Failure"


class StatusSuccessFile(StatusSuccess):
    def __init__(self, filename):
        self.filename = filename


class StatusSuccessFileCreated(StatusSuccessFile):
    def __repr__(self):
        return "{0} created".format(self.filename)


class StatusSuccessFileExists(StatusSuccessFile):
    def __init__(self, filename, modified=None):
        self.filename = filename
        self.modified = modified

    def __repr__(self):
        return "current file found ({0}, {1})".format(self.filename, self.modified)


class StatusFailureAlreadyInProgress(StatusFailure):
    def __init__(self, since=None):
        self.since = since

    def __repr__(self):
        return "export in progress since {0}".format(self.since)


class BaseExporter(object):
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

    template = "browser/templates/export_container_contextless.pt"
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
        return unicode(self.get_parent("Publication").getId(), "utf-8")

    def get_publication_title(self):
        return unicode(self.get_parent("Publication").Title(), "utf-8")

    def get_package_journal_volume(self):
        return unicode(self.get_parent("Volume").getId(), "utf-8")

    def get_package_journal_volume_title(self):
        return unicode(self.get_parent("Volume").Title(), "utf-8")

    def get_package_journal_pubyear(self):
        return self.get_parent("Volume").getYearOfPublication() or None

    def get_package_journal_issue(self):
        issue = self.get_parent("Issue")
        if issue is None:
            return None
        return unicode(issue.getId(), "utf-8")

    def get_package_journal_issue_title(self):
        issue = self.get_parent("Issue")
        if issue is None:
            return None
        return unicode(issue.Title(), "utf-8")

    def get_issue_filename(self):
        issue = self.get_package_journal_issue()
        if issue is not None:
            return "recensio_%s_%s_%s.xml" % (
                self.get_publication_shortname(),
                self.get_package_journal_volume(),
                issue,
            )
        else:
            return "recensio_%s_%s.xml" % (
                self.get_publication_shortname(),
                self.get_package_journal_volume(),
            )

    def finish_issue(self):
        pt = PageTemplateFile(self.template)
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
        xml = pt(**options)
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
        stream = FileIO(cache_file_name, mode="w")
        zipfile = ZipFile(stream, "w")
        self.write_zipfile(zipfile)
        zipfile.close()
        stream.close()

        stream = FileIO(cache_file_name, mode="r")
        zipdata = stream.readall()
        stream.close()
        remove(cache_file_name)
        return zipdata

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
        export_xml_obj.setFile(self.get_zipdata(), filename=self.export_filename)
        export_xml_obj.setModificationDate(DateTime())
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
        if review.getBv():
            try:
                use_canonical = review.isUseCanonicalUriForBVID()
            except AttributeError:
                use_canonical = False
            if use_canonical:
                url = review.getCanonical_uri()
            else:
                url = review.absolute_url()
            self.items.append((review.getBv(), url))

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

        export_file.setFile(csvfile.getvalue(), filename=self.export_filename)
        export_file.setModificationDate(DateTime())
        return StatusSuccessFileCreated(self.export_filename)


class LZAExporter(ChroniconExporter):
    """Like ChroniconExporter but
    * also exports full text (PDF)
    * only exports each review once, then never again"""

    export_filename = "export_lza_xml.zip"
    xml_view_name = "@@xml-lza"

    def __init__(self):
        super(LZAExporter, self).__init__()
        self.reviews_pdf = {}

    @property
    def cache_filename(self):
        return path.join(tempfile.gettempdir(), "lza_cache.zip")

    def _set_exported(self, review, value=True):
        IAnnotations(review)["LZA_EXPORTED"] = value and True or False

    def _is_exported(self, review):
        return IAnnotations(review).get("LZA_EXPORTED")

    def add_review(self, review):
        if self._is_exported(review):
            return
        super(LZAExporter, self).add_review(review)
        pdf_path = "/".join(review.getPhysicalPath()[2:]) + ".pdf"
        pdf_blob = review.get_review_pdf()["blob"].open()
        self.reviews_pdf[pdf_path] = pdf_blob.read()
        pdf_blob.close()
        self._set_exported(review)

    def write_zipfile(self, zipfile):
        super(LZAExporter, self).write_zipfile(zipfile)
        for filename, pdf in self.reviews_pdf.items():
            zipfile.writestr(filename, bytes(pdf))


@implementer(IRecensioExporter)
class MissingBVIDExporter(BVIDExporter):

    export_filename = "missing_bvid.csv"

    def add_review(self, review):
        if not review.getBv():
            if hasattr(review, "getIsbn"):
                isbn_or_issn = review.getIsbn()
            else:
                isbn_or_issn = review.getIssn()
            self.items.append((review.UID(), isbn_or_issn))


class DaraExporter(BaseExporter):
    def __init__(self):
        self.reviews_xml = []

    def add_review(self, review):
        self.reviews_xml.append(review.restrictedTraverse("@@xml-dara")())

    def export(self):
        pass


BVIDExporterFactory = Factory(BVIDExporter, IFactory, "exporter")
MissingBVIDExporterFactory = Factory(MissingBVIDExporter, IFactory, "exporter")
ChroniconExporterFactory = Factory(ChroniconExporter, IFactory, "exporter")
LZAExporterFactory = Factory(LZAExporter, IFactory, "exporter")


def register_doi_raw(obj):
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IRecensioSettings)
    username = settings.doi_registration_username
    password = settings.doi_registration_password
    auth = b64encode("{0}:{1}".format(username, password))
    url = settings.doi_registration_url.encode("utf-8")

    xml = obj.restrictedTraverse("@@xml-dara")().encode("utf-8")
    headers = {
        "Content-type": "application/xml;charset=UTF-8",
        "Authorization": "Basic " + auth,
    }
    result = urlopen(Request(url, xml, headers))
    return_code = result.getcode()
    result.close()
    return return_code


def register_doi(obj):
    try:
        return_code = register_doi_raw(obj)
    except HTTPError as e:
        if e.code == 401:
            message = (
                "Dara login failed - check DOI registration " "user name and password"
            )
        elif e.code == 400:
            message = "Request rejected by dara - check generated XML"
        elif e.code == 500:
            message = "Dara server error - try again later"
        else:
            message = "Error returned by dara server: {0}".format(e)
        status = "error"
        log.error(message)
        body = e.read()
        if "\n" in body:
            dump_file = NamedTemporaryFile(suffix=".html", delete=False)
            dump_file.write(body)
            dump_file.close()
            log.info("HTTPError dumped to " + dump_file.name)
        else:
            log.error(body)
    except ValueError as e:
        exc_msg = e.__class__.__name__ + ": " + str(e)
        message = "Error while updating dara record (" + exc_msg + ")"
        status = "error"
    except IOError as e:
        exc_msg = e.__class__.__name__ + ": " + str(e)
        message = "Error contacting dara server (" + exc_msg + ")"
        status = "error"
    else:
        if return_code == 201:
            message = "DOI successfully registered"
        elif return_code == 200:
            message = "Metadata updated"
        else:
            message = "Success (status {0})".format(return_code)
        status = "success"
    return status, message

