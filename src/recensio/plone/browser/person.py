from plone import api
from Products.Five import BrowserView


class BaseView(BrowserView):
    def __call__(self):
        """This is needed for the migrated Person instances.

        In the old system the person instances
        have the layout property set to "base_view".

        We can get rid of this view after the migration if an upgrade step
        cleans up the layout property.
        """
        return api.content.get_view(
            name="view",
            context=self.context,
            request=self.request,
        )()
