from ftw.upgrade import UpgradeStep


class UpdateSearchSettings(UpgradeStep):
    """Update search settings."""

    def __call__(self):
        self.install_upgrade_profile()
