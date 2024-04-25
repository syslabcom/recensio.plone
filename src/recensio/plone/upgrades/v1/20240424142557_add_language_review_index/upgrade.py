from ftw.upgrade import UpgradeStep
from plone import api


class AddLanguageReviewIndex(UpgradeStep):
    """Add languageReview index."""

    def __call__(self):
        self.install_upgrade_profile()
        catalog = api.portal.get_tool("portal_catalog")
        catalog.manage_reindexIndex(ids=["languageReview"])
