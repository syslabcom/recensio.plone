from ftw.upgrade import UpgradeStep
from recensio.plone.setuphandlers import create_main_nav_content


class MainNavActions(UpgradeStep):
    """Main nav actions."""

    def __call__(self):
        create_main_nav_content()
