from ftw.upgrade import UpgradeStep
from recensio.plone.setuphandlers import set_theme_browser_layout


class SetBrowseTopicsAsLayout(UpgradeStep):
    """set-browse-topics-as-layout."""

    def __call__(self):
        set_theme_browser_layout()
