from html import escape
from io import BytesIO
from plone.i18n.locales.languages import _languagelist
from Products.Five.browser import BrowserView
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.config import REVIEW_TYPES
from zipfile import ZipFile
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


AUTHOR_TMPL = """        <author_%(num)s_first_name>%(firstname)s</author_%(num)s_first_name>
        <author_%(num)s_last_name>%(lastname)s</author_%(num)s_last_name>
"""
EDITOR_TMPL = """        <editor_%(num)s_first_name>%(firstname)s</editor_%(num)s_first_name>
        <editor_%(num)s_last_name>%(lastname)s</editor_%(num)s_last_name>
"""


class XMLRepresentation(BrowserView):
    filename = "recensio_exportx.xml"
    include_fulltext = False

    def get_lang_name(self, code):
        if not code:
            return ""
        return _languagelist.get(code, {"native": code})["native"]

    def get_parent(self, meta_type):
        return IParentGetter(self.context).get_parent_object_of_type(meta_type)

    def get_publication_shortname(self):
        return self.get_parent("Publication").getId()

    def get_publication_title(self):
        return self.get_parent("Publication").Title()

    def get_package_journal_volume(self):
        return self.get_parent("Volume").getId()

    def get_package_journal_volume_title(self):
        return self.get_parent("Volume").Title()

    _voc_names = {
        "ddcPlace": "recensio.plone.vocabularies.region_values",
        "ddcTime": "recensio.plone.vocabularies.epoch_values",
        "ddcSubject": "recensio.plone.vocabularies.topic_values",
    }

    def get_voc_title(self, typ, term):
        factory = getUtility(IVocabularyFactory, self._voc_names[typ])
        vocab = factory(self.context)
        try:
            return vocab.getTerm(term).title or ""
        except LookupError:
            return ""

    def list_authors(self):
        out = ""
        num = 1
        for rel in self.context.authors or []:
            obj = rel.to_object
            if obj:
                out += AUTHOR_TMPL % dict(
                    num=num,
                    firstname=escape(obj.firstname or ""),
                    lastname=escape(obj.lastname or ""),
                )
                num += 1
        return out

    def list_editors(self):
        out = ""
        num = 1
        for rel in self.context.editorial or []:
            obj = rel.to_object
            if obj:
                out += EDITOR_TMPL % dict(
                    num=num,
                    firstname=escape(obj.firstname or ""),
                    lastname=escape(obj.lastname or ""),
                )
                num += 1
        return out


class XMLRepresentationLZA(XMLRepresentation):
    include_fulltext = True


class XMLRepresentationContainer(XMLRepresentation):
    def __call__(self):
        self.request.response.setHeader("Content-type", "application/zip")
        self.request.response.setHeader(
            "Content-disposition", "inline;filename=%s" % self.filename
        )
        zipdata = self.get_zipdata()
        self.request.response.setHeader("content-length", str(len(zipdata)))
        return zipdata

    def issues(self):
        pc = self.context.portal_catalog
        parent_path = dict(query="/".join(self.context.getPhysicalPath()))
        results = pc(review_state="published", portal_type=("Issue"), path=parent_path)
        for item in results:
            yield item.getObject()

    def write_zipfile(self, zipfile):
        for issue in self.issues():
            xmlview = issue.restrictedTraverse("@@xml")
            xml = xmlview.template(xmlview)
            filename = xmlview.filename
            zipfile.writestr(filename, bytes(xml.encode("utf-8")))

    def get_zipdata(self):
        stream = BytesIO()
        zipfile = ZipFile(stream, "w")
        self.write_zipfile(zipfile)
        zipfile.close()
        zipdata = stream.getvalue()
        stream.close()
        return zipdata


class XMLRepresentationPublication(XMLRepresentationContainer):
    @property
    def filename(self):
        return "recensio_%s.zip" % (self.get_publication_shortname())


class XMLRepresentationVolume(XMLRepresentationContainer):
    @property
    def filename(self):
        return "recensio_{}_{}.zip".format(
            self.get_publication_shortname(),
            self.get_package_journal_volume(),
        )


class XMLRepresentationIssue(XMLRepresentation):

    def __call__(self):
        self.request.response.setHeader("Content-type", "application/xml")
        self.request.response.setHeader(
            "Content-disposition", "inline;filename=%s" % self.filename
        )
        return self.template(self)

    def get_package_journal_pubyear(self):
        volume = self.get_parent("Volume")
        return getattr(volume, "year_of_publication", None) or None

    def get_package_journal_issue(self):
        return self.get_parent("Issue").getId()

    def get_package_journal_issue_title(self):
        return self.get_parent("Issue").Title()

    @property
    def filename(self):
        return "recensio_{}_{}_{}.xml".format(
            self.get_publication_shortname(),
            self.get_package_journal_volume(),
            self.get_package_journal_issue(),
        )

    def reviews(self):
        pc = self.context.portal_catalog
        parent_path = dict(query="/".join(self.context.getPhysicalPath()), depth=3)
        results = pc(
            review_state="published", portal_type=REVIEW_TYPES, path=parent_path
        )
        for item in results:
            yield item.getObject()
