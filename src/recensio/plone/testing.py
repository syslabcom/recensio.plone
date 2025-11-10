from collective.solr.local import marker
from collective.solr.local import setLocal
from collective.solr.testing import CollectiveSolrLayer
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

import recensio.plone


class RecensioSolrLayer(CollectiveSolrLayer):
    """While CollectiveSolrLayer provides a port override option in __init__, it
    does not respect that port because it already fires up a solr on the default
    port and stores that connection as a thread local.

    Hence, we need to nuke that threadlocal and THEN properly start Solr.
    """

    def setUpPloneSite(self, portal):
        setLocal("connection", marker)
        super().setUpPloneSite(portal)


RECENSIO_SOLR_FIXTURE = RecensioSolrLayer(solr_port=8984, solr_active=True)


class RecensioPloneLayer(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=recensio.plone)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "recensio.plone:default")


RECENSIO_PLONE_FIXTURE = RecensioPloneLayer()


RECENSIO_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RECENSIO_PLONE_FIXTURE,),
    name="RecensioPloneLayer:IntegrationTesting",
)

RECENSIO_PLONE_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RECENSIO_PLONE_FIXTURE, RECENSIO_SOLR_FIXTURE),
    name="RecensioPloneLayer:SolrIntegrationTesting",
)
