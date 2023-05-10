from ftw.upgrade import UpgradeStep


class AddPatternslibBundle(UpgradeStep):
    """Add Patternslib bundle."""

    def __call__(self):
        self.install_upgrade_profile()
