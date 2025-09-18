from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer

import recensio.plone


class RecensioPloneLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # This re-implements PLONE_APP_CONTENTTYPES_FIXTURE
        # in order to avoid depending on robotframework
        import plone.app.contenttypes

        self.loadZCML(package=plone.app.contenttypes)
        self.loadZCML(package=recensio.plone)

    def setUpPloneSite(self, portal):
        portal.portal_workflow.setDefaultChain("simple_publication_workflow")
        applyProfile(portal, "recensio.plone:default")


RECENSIO_PLONE_FIXTURE = RecensioPloneLayer()


RECENSIO_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RECENSIO_PLONE_FIXTURE,),
    name="RecensioPloneLayer:IntegrationTesting",
)
