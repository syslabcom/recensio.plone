from io import BytesIO
from plone.namedfile.file import NamedBlobFile

import pypdf


class RecensioPdfWriter(pypdf.PdfWriter):
    def _sweepIndirectReferences(self, externMap, data):
        try:
            return super()._sweepIndirectReferences(externMap, data)
        except KeyError:
            return data


def cutPDF(pdf, start, end):
    reader = pypdf.PdfReader(pdf)
    writer = RecensioPdfWriter()
    pages = reader.pages[int(start) - 1 : int(end)]
    for page in pages:
        writer.add_page(page)
    fakefile = BytesIO()
    writer.write(fakefile)
    fakefile.seek(0)
    return NamedBlobFile(
        filename="recensio.pdf",
        data=fakefile.read(),
    )
