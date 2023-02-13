from plone.registry.interfaces import IRegistry
from recensio.plone import _
from recensio.plone.controlpanel.settings import IRecensioSettings
from recensio.plone.tools import convertToString
from zope.component import getUtility

import xlrd


class ExcelURNExtractor:
    """Convert a given excel file to a dictionary of UUID->URN."""

    REFERENCE_HEADER = ["recensio-id", "urn"]

    def __call__(self, xls_file):
        retval = []
        try:
            workbook = xlrd.open_workbook(xls_file)
            import pdb

            pdb.set_trace()
            xls_data = workbook.read().data
        except TypeError:
            raise TypeError(_("Excel Datei konnte nicht gelesen werden"))
        except xlrd.XLRDError:
            raise Exception(
                _(
                    "help_import_error_unsupported_xls",
                    (
                        "Please ensure that the xls file you selected is a valid "
                        "Excel file"
                    ),
                )
            )
        header = xls_data[0]
        errors = []
        for i in range(max(len(header), len(self.REFERENCE_HEADER))):
            if len(header) < i - 1:
                errors.append(
                    "Das Excel Dokument enthält zu wenige Spalten. Folgende Spalten sind das Minimum: %s"
                    % (" ".join(self.REFERENCE_HEADER))
                )
                break
            if len(self.REFERENCE_HEADER) < i - 1:
                errors.append(
                    "Das Excel Dokument enthält zu viele Spalten. Es dürfen nur folgende Spalten vorkommen: %s"
                    % (" ".join(self.REFERENCE_HEADER))
                )
                break
            if header[0].lower().strip() != self.REFERENCE_HEADER[0]:
                errors.append(
                    "Spalte %i ist falsch. Ist: %s, Soll: %s (Gross und Kleinschreibung wird ignoriert"
                    % (i + 1, header[0].strip(), self.REFERENCE_HEADER[i])
                )
        if errors:
            raise TypeError("Do not understand Excel File", errors=errors)

        retval = []
        for count, row in enumerate(xls_data[1:]):
            retval.append(row)
        return retval


class ExcelConverter:
    """Convert a given excel file to a list of content types and their initial
    data."""

    translate_headers = {
        "isbn/issn werk": "isbn/issn",
        "isbn/issn (work)": "isbn/issn",
        "jahr werk": "jahr",
        "year (work)": "jahr",
        "rez. vorname": "rez. vorname",
        "reviewer firstname": "rez. vorname",
        "rez. nachname": "rez. nachname",
        "reviewer last name": "rez. nachname",
        "titel werk": "titel werk",
        "title of the work": "titel werk",
        "print seite start": "print seite start",
        "print start page": "print seite start",
        "print seite ende": "print seite ende",
        "print end page": "print seite ende",
        "pdf start": "pdf start",
        "pdf ende": "pdf ende",
        "pdf end": "pdf ende",
        "typ": "typ",
        "type": "typ",
        "rez.sprache": "rez.sprache",
        "language rev.": "rez.sprache",
        "textsprache": "textsprache",
        "language text": "textsprache",
        "original url": "original url",
        "optionales zitierschema": "optionales zitierschema",
        "optional custom citation format": "optionales zitierschema",
        "doi": "doi",
    }

    ignored_fields = ["typ", ""]

    unicode_convert = [
        "isbn/issn",
        "jahr",
        "rez. vorname",
        "rez. nachname",
        "titel werk",
        "optionales zitierschema",
        "rez.sprache",
        "textsprache",
    ]

    reference_header_zip = [
        "",
        "isbn/issn",
        "jahr",
        "rez. vorname",
        "rez. nachname",
        "titel werk",
        "print seite start",
        "print seite ende",
        "filename",
        "typ",
        "rez.sprache",
        "textsprache",
        "original url",
        "optionales zitierschema",
        "doi",
        "",
        "review journal",
        "rj",
    ]
    reference_header_xls = [
        "",
        "isbn/issn",
        "jahr",
        "rez. vorname",
        "rez. nachname",
        "titel werk",
        "print seite start",
        "print seite ende",
        "pdf start",
        "pdf ende",
        "typ",
        "rez.sprache",
        "textsprache",
        "original url",
        "optionales zitierschema",
        "doi",
        "",
        "review journal",
        "rj",
    ]

    portal_type_mappings = {
        "rm": {
            "type": "Review Monograph",
            "isbn/issn": "isbn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStartOfReviewInJournal",
            "print seite ende": "pageEndOfReviewInJournal",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "review journal": "ignore",
            "rez.sprache": "languageReview",
            "textsprache": "languageReviewedText",
            "rj": "ignore",
            "original url": "canonical_uri",
            "optionales zitierschema": "customCitation",
            "doi": "doi",
        },
        "rj": {
            "type": "Review Journal",
            "isbn/issn": "issn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStartOfReviewInJournal",
            "print seite ende": "pageEndOfReviewInJournal",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "rez.sprache": "languageReview",
            "textsprache": "languageReviewedText",
            "original url": "canonical_uri",
            "optionales zitierschema": "customCitation",
            "doi": "doi",
        },
        "raj": {
            "type": "ReviewArticleJournal",
            "isbn/issn": "issn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStartOfReviewInJournal",
            "print seite ende": "pageEndOfReviewInJournal",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "rez.sprache": "languageReview",
            "textsprache": "languageReviewedText",
            "original url": "canonical_uri",
            "optionales zitierschema": "customCitation",
            "doi": "doi",
        },
        "raev": {
            "type": "Review Article Collection",
            "isbn/issn": "issn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStartOfReviewInJournal",
            "print seite ende": "pageEndOfReviewInJournal",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "rez.sprache": "languageReview",
            "textsprache": "languageReviewedText",
            "original url": "canonical_uri",
            "optionales zitierschema": "customCitation",
            "doi": "doi",
        },
        "re": {
            "type": "Review Exhibition",
            "isbn/issn": "ignore",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStartOfReviewInJournal",
            "print seite ende": "pageEndOfReviewInJournal",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "rez.sprache": "languageReview",
            "textsprache": "ignore",
            "original url": "canonical_uri",
            "optionales zitierschema": "customCitation",
            "doi": "doi",
        },
        "pm": {
            "type": "Presentation Monograph",
            "isbn/issn": "isbn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStart",
            "print seite ende": "pageEnd",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "original url": "ignore",
            "optionales zitierschema": "customCitation",
        },
        "pace": {
            "type": "Presentation Collection",
            "isbn/issn": "isbn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStart",
            "print seite ende": "pageEnd",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "review journal": "ignore",
            "rj": "ignore",
            "typ": "ignore",
            "original url": "ignore",
            "optionales zitierschema": "customCitation",
        },
        "paj": {
            "type": "Presentation Article Review",
            "isbn/issn": "issn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStart",
            "print seite ende": "pageEnd",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "original url": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "typ": "ignore",
            "optionales zitierschema": "customCitation",
        },
        "por": {
            "type": "Presentation Online Resource",
            "isbn/issn": "isbn",
            "jahr": "yearOfPublication",
            "rez. vorname": "firstname_review_authors_1",
            "rez. nachname": "lastname_review_authors_1",
            "titel werk": "title",
            "print seite start": "pageStart",
            "print seite ende": "pageEnd",
            "filename": "filename",
            "pdf start": "pdfPageStart",
            "pdf ende": "pdfPageEnd",
            "typ": "ignore",
            "original url": "ignore",
            "review journal": "ignore",
            "rj": "ignore",
            "typ": "ignore",
            "optionales zitierschema": "customCitation",
        },
    }

    def __init__(self):
        self.warnings = []

    def convert_zip(self, xls_file):
        return self.convert(xls_file, self.reference_header_zip)

    def convert_xls(self, xls_file):
        return self.convert(xls_file, self.reference_header_xls)

    def check_header_column(self, header, column, error_message):
        try:
            return header[column]
        except IndexError:
            return error_message

    def match_headers(self, reference_header, header, column):
        try:
            return (
                reference_header[column] == header[column].strip().lower()
                and _("Ja")
                or _("Nein")
            )
        except IndexError:
            return _("Nein")

    def xls_format_errors(self, sheet, keys, reference_header):
        if keys == reference_header:
            return
        columns = []
        header = sheet.row_values(4)
        for i in range(max(len(keys), len(reference_header))):
            column = []
            column.append(
                self.check_header_column(
                    reference_header, i, _("Spalte muss leer sein!")
                )
            )
            column.append(self.check_header_column(header, i, _("Spalte ist Leer!")))
            column.append(self.match_headers(reference_header, header, i))
            if column[-1] == _("Nein"):
                css_class = "bad"
            else:
                css_class = "good"
            columns.append({"columns": column, "css_class": css_class})
        self.header_error = columns
        raise Exception(
            _("Die Excel Datei enthaelt Daten, " "die das Programm nicht versteht")
        )

    def extact_row_data(self, sheet, row_index, keys):
        row = sheet.row_values(row_index)
        if len([x for x in row[1:15] if x]) <= 1:
            return
        try:
            mapping = self.portal_type_mappings[row[keys.index("typ")]]
        except KeyError:
            raise KeyError(
                _(
                    "Die Excel Datei beinhaltet Daten, "
                    "die das Programm nicht versteht."
                    " Bitte schauen Sie, ob jeder Date"
                    "nsatz einen Typ angegeben hat."
                )
            )
        data = {"type": mapping["type"]}
        for index, key in enumerate(keys):
            if key not in self.ignored_fields:
                if key in self.unicode_convert:
                    try:
                        data[mapping[key]] = str(int(row[index]))
                    except ValueError:
                        data[mapping[key]] = str(row[index])
                else:
                    data[mapping[key]] = row[index]
        data["reviewAuthors"] = [
            {
                "firstname": data["firstname_review_authors_1"],
                "lastname": data["lastname_review_authors_1"],
            },
        ]
        (data["pageStartOfReviewInJournal"], data["pageEndOfReviewInJournal"],) = map(
            int,
            [
                data["pageStartOfReviewInJournal"] or 0,
                data["pageEndOfReviewInJournal"] or 0,
            ],
        )
        data["languageReview"] = self.convertLanguages(data["languageReview"])
        if data.get("languageReviewedText"):
            data["languageReviewedText"] = self.convertLanguages(
                data["languageReviewedText"]
            )
        data = convertToString(data)
        return data

    def convert(self, xls_file, reference_header):
        try:
            workbook = xlrd.open_workbook(file_contents=xls_file.read())
            sheet = workbook.sheet_by_index(0)
        except TypeError:
            raise TypeError(
                _(
                    "Excel Datei konnte nicht gelesen werden, "
                    "evtl. mit PDF vertauscht?"
                )
            )
        except xlrd.XLRDError:
            raise Exception(
                _(
                    "help_import_error_unsupported_xls",
                    (
                        "Please ensure that the xls file you selected is a valid "
                        "Excel file"
                    ),
                )
            )

        keys = [
            self.translate_headers.get(x.strip().lower(), x.strip().lower())
            for x in sheet.row_values(4)
        ]

        self.xls_format_errors(sheet, keys, reference_header)

        retval = []
        start_row = 6
        end_row = sheet.nrows - 1
        for row_index in range(start_row, end_row):
            data = self.extact_row_data(sheet, row_index, keys)
            if data is None:
                continue
            retval.append(data)
        return retval

    def convertLanguages(self, data):
        data = (
            data.replace(";", " ").replace(".", " ").replace(":", " ").replace(",", " ")
        )
        data = [x.strip().lower() for x in data.split() if x.strip()]
        retval = []
        for lang in data:
            if lang in self.supported_languages:
                retval.append(lang)
            else:
                warning = _(
                    'The language "${lang}" is unknown',
                    default='Die Sprache "${lang}" is unbekannt',
                    mapping={"lang": lang},
                )
                self.warnings.append(warning)
        return tuple(retval)

    @property
    def supported_languages(self):
        if not hasattr(self, "_supported_languages"):
            registry = getUtility(IRegistry)
            settings = registry.forInterface(
                IRecensioSettings, prefix="recensio.plone.settings"
            )
            self._supported_languages = settings.available_content_languages
        return self._supported_languages
