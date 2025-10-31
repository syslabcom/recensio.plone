from ftw.upgrade import UpgradeStep


class DisableLivesearch(UpgradeStep):
    """disable-livesearch."""

    def __call__(self):
        self.install_upgrade_profile()
