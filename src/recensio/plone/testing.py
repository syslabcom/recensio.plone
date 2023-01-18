from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer

import recensio.plone


class RecensioPloneLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=recensio.plone)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "recensio.plone:default")


RECENSIO_PLONE_FIXTURE = RecensioPloneLayer()


RECENSIO_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RECENSIO_PLONE_FIXTURE,),
    name="RecensioPloneLayer:IntegrationTesting",
)
