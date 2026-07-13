from datetime import date
from paramiko import SFTPClient
from paramiko import Transport
from paramiko.ssh_exception import SSHException
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from recensio.plone.config import REVIEW_TYPES_TO_EXPORT
from recensio.plone.export import LZAExporter
from recensio.plone.export import register_doi
from recensio.plone.interfaces import IRecensioExporter
from recensio.plone.interfaces import IReview
from time import time
from zope.annotation.interfaces import IAnnotations
from zope.component import getFactoriesFor
from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.interface import alsoProvides

import logging


log = logging.getLogger(__name__)

EXPORT_TIMESTAMP_KEY = "recensio.plone.metadata_export_timestamp"


class MetadataExport(BrowserView):
    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        log.info("Starting export")
        annotations = IAnnotations(self.context)
        if self.request.get("force", False):
            if EXPORT_TIMESTAMP_KEY in annotations:
                del annotations[EXPORT_TIMESTAMP_KEY]
        timestamp = annotations.get(EXPORT_TIMESTAMP_KEY, 0)
        if time() - timestamp < 2 * 60 * 60:  # 2 hours
            log.info("export already running, abort")
            return "An export is already running, aborting"

        annotations[EXPORT_TIMESTAMP_KEY] = time()

        try:
            exporters = [
                (name, factory())
                for name, factory in getFactoriesFor(IRecensioExporter)
            ]
            exporters_to_run = [(name, e) for name, e in exporters if e.needs_to_run()]
        except Exception as e:
            log.exception(e)
            del annotations[EXPORT_TIMESTAMP_KEY]
            msg = "Error, aborting export: " + str(e)
            log.error(msg)
            return msg

        if not exporters_to_run:
            del annotations[EXPORT_TIMESTAMP_KEY]
            log.info("export finished, nothing to do")
            return "Nothing to do, no exporter requested an export run."

        for issue_or_volume in self.issues_and_volumes():
            for review in self.reviews(issue_or_volume):
                for name, exporter in exporters_to_run:
                    try:
                        exporter.add_review(review)
                    except Exception as e:
                        log.error(
                            "Error in {} - {}: {}".format(
                                review.getId(), e.__class__.__name__, e
                            )
                        )
        statuses = []
        for name, exporter in exporters_to_run:
            status = exporter.export()
            statuses.append((name, status))

        del annotations[EXPORT_TIMESTAMP_KEY]
        log.info("export finished")

        return "<br />\n".join([name + ": " + str(status) for name, status in statuses])

    def items(self, portal_type=(), context=None, depth=None):
        pc = api.portal.get_tool("portal_catalog")
        if context is None:
            context = self.context
        parent_path = dict(query="/".join(context.getPhysicalPath()))
        if depth is not None:
            parent_path["depth"] = depth
        query = dict(
            review_state="published", portal_type=portal_type, path=parent_path
        )
        results = pc(**query)
        if None in results:
            query["b_size"] = len(results)
            results = pc(**query)
        for item in results:
            try:
                yield item.getObject()
            except AttributeError:
                log.warn("Could not getObject: " + item.getPath())
                continue

    def issues_and_volumes(self):
        return self.items(portal_type=("Issue", "Volume"))

    def reviews(self, issue):
        return self.items(portal_type=REVIEW_TYPES_TO_EXPORT, context=issue, depth=1)


class ChroniconExport(BrowserView):
    @property
    def filename(self):
        prefix = api.portal.get_registry_record(
            name="recensio.plone.settings.xml_export_filename_prefix"
        )
        return "{}_{}_all.zip".format(
            prefix,
            date.today().strftime("%d%m%y"),
        )

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        host = api.portal.get_registry_record(
            name="recensio.plone.settings.xml_export_server"
        )
        username = api.portal.get_registry_record(
            name="recensio.plone.settings.xml_export_username"
        )
        password = api.portal.get_registry_record(
            name="recensio.plone.settings.xml_export_password"
        )
        if not host:
            return "no host configured"
        log.info("Starting XML export to sftp")

        exporter = getUtility(IFactory, name="chronicon_exporter")()
        export_xml = exporter.get_export_obj(self.context)
        if export_xml is None:
            msg = "Could not get export file object: {}".format(
                exporter.export_filename
            )
            log.error(msg)
            return msg

        zipstream = export_xml.file
        transport = None
        try:
            transport = Transport((host, 2222))
            transport.connect(username=username, password=password)
            sftp = SFTPClient.from_transport(transport)
            attribs = sftp.putfo(zipstream.open(), self.filename)
        except (OSError, SSHException) as ioe:
            msg = f"Export failed, {ioe.__class__.__name__}: {ioe}"
            log.error(msg)
            return msg
        finally:
            if transport is not None:
                transport.close()
        if attribs.st_size == zipstream.size:
            msg = "Export successful"
            log.info(msg)
            return msg
        else:
            msg = "Export failed, {}/{} bytes transferred".format(
                attribs.st_size, zipstream.size
            )
            log.error(msg)
            return msg


class DaraUpdate(BrowserView):
    """Send metadata to da|ra, in effect registering the object's DOI or
    updating its metadata if already registered."""

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        if self.request.get("REQUEST_METHOD") == "POST":
            status, message = register_doi(self.context)
            IStatusMessage(self.request).addStatusMessage(message, type=status)
        self.request.response.redirect(self.context.absolute_url())


class ResetLZAExportFlag(BrowserView):
    def _reset_flag(self, context):
        paths = []
        if IReview.providedBy(context):
            self.exporter._set_exported(context, value=False)
            paths.append("/".join(context.getPhysicalPath()))
        for child in getattr(context, "objectValues", lambda: [])():
            paths += self._reset_flag(child)
        return paths

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        self.exporter = LZAExporter()
        paths = self._reset_flag(self.context)
        return "Reset LZA export flag for the following objects:\n\n" + "\n".join(paths)
