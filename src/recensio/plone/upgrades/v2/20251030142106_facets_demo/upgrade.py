from ftw.upgrade import UpgradeStep


class FacetsDemo(UpgradeStep):
    """facets-demo.
    """

    def __call__(self):
        self.install_upgrade_profile()
