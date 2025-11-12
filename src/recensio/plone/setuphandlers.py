from plone import api
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


def create_main_nav_content():
    """Create the menu structure required for portal actions"""
    portal = api.portal.get()
    if "rezensionen" in portal.objectIds():
        return
    rezensionen = api.content.create(
        container=portal, title="Rezensionen", id="rezensionen", type="Folder"
    )
    api.content.transition(rezensionen, to_state="published")
    zeitschriften = api.content.create(
        container=rezensionen, title="Zeitschriften", id="zeitschriften", type="Folder"
    )
    api.content.transition(zeitschriften, to_state="published")
    themen_epochen_regionen = api.content.create(
        container=portal, title="Themen", id="themen-epochen-regionen", type="Folder"
    )
    api.content.transition(themen_epochen_regionen, to_state="published")
    ueber_uns = api.content.create(
        container=portal, title="Über uns", id="ueber-uns", type="Folder"
    )
    api.content.transition(ueber_uns, to_state="published")


def default(context):
    """Run when installing the default profile."""
    create_main_nav_content()


@implementer(INonInstallable)
class HiddenProfiles:
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "recensio.plone:uninstall",
        ]

    def getNonInstallableProducts(self):
        """Hide the upgrades package from site-creation and quickinstaller."""
        return ["recensio.plone.upgrades"]
