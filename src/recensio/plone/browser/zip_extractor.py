from io import BytesIO
from recensio.plone import _
from zipfile import ZipFile


class ZipExtractor:
    def __call__(self, zipfile):
        zipfile = ZipFile(zipfile)
        filenames = zipfile.namelist()
        xls_files = [x for x in filenames if x.endswith("xls")]
        doc_files = [x for x in filenames if x.endswith("doc")]
        if len(xls_files) > 1:
            raise Exception(_("Zip file contains too many excel files"))
        if not xls_files:
            raise Exception(_("Zip file contains no excel files"))
        return (
            BytesIO(zipfile.open(xls_files[0]).read()),
            [BytesIO(zipfile.open(x).read()) for x in doc_files],
        )
