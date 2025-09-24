from ftw.upgrade import UpgradeStep
from logging import getLogger
from plone import api
from transaction import commit


log = getLogger(__name__)


class InstallCollectiveSolr(UpgradeStep):
    """Install collective solr."""

    def __call__(self):
        self.install_upgrade_profile()

        # ensure solr activation is persisted before performing the reindex
        commit()

        portal = api.portal.get()
        maintenance = api.content.get_view("solr-maintenance", portal)
        log.info("Reindexing to Solr. This will take a while.")
        maintenance.reindex()
        log.info("Solr reindexing done.")
