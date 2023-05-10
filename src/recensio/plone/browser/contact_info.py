from plone import api
from Products.Five import BrowserView


class RecensioContactInfoRedirect(BrowserView):
    def __call__(self):
        return self.request.RESPONSE.redirect(
            f"{api.portal.get().absolute_url()}/ueber-uns/kontakt"
        )
