from ftw.upgrade import UpgradeStep


class BrowseWithoutSearchabletext(UpgradeStep):
    """browse-without-searchabletext.
    """

    def __call__(self):
        self.install_upgrade_profile()
