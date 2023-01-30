from Products.Five import BrowserView
from recensio.plone.adapter.parentgetter import IParentGetter
from recensio.plone.browser.interfaces import IRedirectToPublication
from zope.interface import implementer


@implementer(IRedirectToPublication)
class RedirectToPublication(BrowserView):
    def __call__(self):
        pub = IParentGetter(self).get_parent_object_of_type("Publication")
        uid = self.context.UID()
        return self.request.RESPONSE.redirect(
            pub.absolute_url() + "?expand:list=" + uid + "#" + uid
        )
