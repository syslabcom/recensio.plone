from ftw.upgrade import UpgradeStep


class SetRedirectToPublicationAsDefaultView(UpgradeStep):
    """Set redirect-to-publication as default view."""

    def __call__(self):
        self.install_upgrade_profile()
