from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from recensio.plone.testing import RECENSIO_PLONE_INTEGRATION_TESTING

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that recensio.plone is properly installed."""

    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if recensio.plone is installed."""
        self.assertTrue(self.installer.is_product_installed("recensio.plone"))

    def test_browserlayer(self):
        """Test that IRecensioPloneLayer is registered."""
        from plone.browserlayer import utils
        from recensio.plone.interfaces import IRecensioPloneLayer

        self.assertIn(IRecensioPloneLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):
    layer = RECENSIO_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstall_product("recensio.plone")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if recensio.plone is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("recensio.plone"))

    def test_browserlayer_removed(self):
        """Test that IRecensioPloneLayer is removed."""
        from plone.browserlayer import utils
        from recensio.plone.interfaces import IRecensioPloneLayer

        self.assertNotIn(IRecensioPloneLayer, utils.registered_layers())
