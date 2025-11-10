from ftw.upgrade import UpgradeStep


class InstallCollectiveSolr(UpgradeStep):
    """Install collective solr."""

    def __call__(self):
        self.install_upgrade_profile()
