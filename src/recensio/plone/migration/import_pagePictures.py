# z3c.form that has one FileUpload field and a submit button
from logging import getLogger
from pathlib import Path
from plone import api
from plone.namedfile import NamedBlobImage
from plone.namedfile.field import NamedBlobFile
from recensio.plone import _
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope import interface

import json
import os


logger = getLogger(__name__)

COLLECTIVE_EXPORTIMPORT_BLOB_HOME = os.environ.get("COLLECTIVE_EXPORTIMPORT_BLOB_HOME")
if COLLECTIVE_EXPORTIMPORT_BLOB_HOME:
    COLLECTIVE_EXPORTIMPORT_BLOB_HOME = Path(COLLECTIVE_EXPORTIMPORT_BLOB_HOME)


class IImportPagePicturesForm(interface.Interface):
    file = NamedBlobFile(
        title=_("File"),
        description=_("Upload a file."),
        required=True,
    )


class ImportPagePicturesForm(form.Form):
    fields = field.Fields(IImportPagePicturesForm)
    ignoreContext = True
    label = _("Import Page Pictures")
    description = _("Import Page Pictures")

    def update(self):
        super().update()
        self.request.set("disable_border", True)

    @button.buttonAndHandler(_("Submit"))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        file = data["file"]
        data = json.loads(file.data)
        brains = api.content.find(UID=list(data))
        total = len(brains)

        for brain_idx, brain in enumerate(brains):
            obj = brain.getObject()
            pagePictures = []
            logger.info(
                "%4d/%4d: Importing pagePictures for %r", brain_idx + 1, total, obj
            )
            for blob_idx, blob_path in enumerate(data[brain.UID]):
                if COLLECTIVE_EXPORTIMPORT_BLOB_HOME:
                    blob_path = (
                        COLLECTIVE_EXPORTIMPORT_BLOB_HOME
                        / blob_path.partition("blobs/")[-1]
                    )
                    with blob_path.open("rb") as f:
                        pagePictures.append(
                            NamedBlobImage(data=f.read(), filename=f"{blob_idx+1}.gif")
                        )
            obj.pagePictures = pagePictures

        self.status = _("File uploaded")
        api.portal.show_message(
            _(
                (
                    "Imported pagePictures for ${total_imported} "
                    "objects out of ${total_to_import}."
                ),
                mapping={
                    "total_imported": total,
                    "total_to_import": len(data),
                },
            )
        )
        self.request.response.redirect(self.nextURL())

    def nextURL(self):
        return "%s/@@import-page-pictures" % self.context.absolute_url()

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        """User cancelled.

        Redirect back to the front page.
        """
        api.portal.show_message(_("Import cancelled."))
        self.request.response.redirect(self.nextURL())
