from collective.ftw.upgrade import UpgradeStep


class UpdateSolrPanelSettings(UpgradeStep):
    """update-solr-panel-settings."""

    def __call__(self):
        self.install_upgrade_profile()
