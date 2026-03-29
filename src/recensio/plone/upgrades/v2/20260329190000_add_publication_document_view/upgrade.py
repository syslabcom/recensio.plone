from ftw.upgrade import UpgradeStep


class AddPublicationDocumentView(UpgradeStep):
    """Add publication document view."""

    def __call__(self):
        self.install_upgrade_profile()
