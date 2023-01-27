from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from recensio.plone import _
from recensio.plone.interfaces import IReview
from zope.interface import implementer


class IGetPDFPortlet(IPortletDataProvider):
    """A portlet to get a pdf from a review."""


@implementer(IGetPDFPortlet)
class Assignment(base.Assignment):

    title = _("label_log_in", default="Recensio PDF Portlet")


class Renderer(base.Renderer):
    render = ViewPageTemplateFile("templates/get_pdf.pt")

    @property
    def available(self):
        return IReview.providedBy(self.context)


class AddForm(base.NullAddForm):
    def create(self):
        return Assignment()
