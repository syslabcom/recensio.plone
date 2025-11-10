from ftw.upgrade import UpgradeStep
from logging import getLogger
from plone import api


log = getLogger(__name__)


class ReindexToSolr(UpgradeStep):
    """Reindex all content into Solr."""

    def __call__(self):
        self.install_upgrade_profile()

        portal = api.portal.get()
        maintenance = api.content.get_view("solr-maintenance", portal)
        log.info("Reindexing to Solr. This will take a while.")
        maintenance.reindex()
        log.info("Solr reindexing done.")
