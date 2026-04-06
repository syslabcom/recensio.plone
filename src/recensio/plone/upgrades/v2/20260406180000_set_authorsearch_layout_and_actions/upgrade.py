from collective.ftw.upgrade import UpgradeStep
from plone import api

import logging


log = logging.getLogger(__name__)


class SetAuthorsearchLayoutAndActions(UpgradeStep):
    """Set @@authorsearch as layout on autoren folder and fix authors action URL."""

    def __call__(self):
        portal = api.portal.get()
        portal_path = "/".join(portal.getPhysicalPath())

        # Set layout on the autoren folder
        if "autoren" in portal:
            autoren = portal["autoren"]
            if autoren.hasProperty("layout"):
                old = autoren.getProperty("layout")
                autoren.manage_changeProperties({"layout": "@@authorsearch"})
                log.info(
                    "%s/autoren: layout changed from %r to '@@authorsearch'",
                    portal_path,
                    old,
                )
            else:
                autoren.manage_addProperty("layout", "@@authorsearch", "string")
                log.info(
                    "%s/autoren: layout property added as '@@authorsearch'",
                    portal_path,
                )
        else:
            log.warning(
                "%s: 'autoren' folder not found, skipping layout update", portal_path
            )

        # Update portal_actions/portal_tabs/authors URL
        portal_actions = api.portal.get_tool("portal_actions")
        try:
            action = portal_actions["portal_tabs"]["authors"]
            old_expr = action.url_expr
            action.url_expr = "string:${portal_url}/autoren"
            log.info(
                "%s: portal_tabs/authors url_expr changed from %r to 'string:${portal_url}/autoren'",
                portal_path,
                old_expr,
            )
        except (KeyError, AttributeError):
            log.warning(
                "%s: portal_tabs/authors action not found, skipping url_expr update",
                portal_path,
            )
