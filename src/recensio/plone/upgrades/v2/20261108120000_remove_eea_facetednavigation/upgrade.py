from collective.ftw.upgrade import UpgradeStep
from zope.annotation.interfaces import IAnnotations
from zope.interface import noLongerProvides

import logging

log = logging.getLogger(__name__)

# object_provides stores the defining dotted name; eea.facetednavigation.interfaces only re-exports it
MARKER_INTERFACE = "eea.facetednavigation.subtypes.interfaces.IFacetedNavigable"
FACETED_VIEW = "facetednavigation_view"
DEFAULT_PROFILE = "eea.facetednavigation:default"
UNINSTALL_PROFILE = "profile-eea.facetednavigation:uninstall"

try:
    from eea.facetednavigation.subtypes.interfaces import IFacetedNavigable
except ImportError:
    IFacetedNavigable = None


class RemoveEeaFacetednavigation(UpgradeStep):
    """Remove eea.facetednavigation leftovers.

    - Reset the layout, remove the IFacetedNavigable marker interface and
      delete the faceted widget configuration annotations on all content
      objects where faceted navigation was enabled.
    - Apply the eea.facetednavigation uninstall profile (removes registry
      records, control panel action and rolemap settings).
    - Remove any remaining eea.facetednavigation registry records directly,
      so the step is also effective when the egg is no longer importable.
    """

    def __call__(self):
        self.cleanup_faceted_objects()
        self.apply_uninstall_profile()
        self.cleanup_registry_records()

    def cleanup_faceted_objects(self):
        log.warning(
            "Querying the catalog via unrestrictedSearchResults for all objects "
            "that need eea.facetednavigation cleanup and reindexing each of them. "
            "On large databases this can take a while."
        )
        queries = [{"object_provides": MARKER_INTERFACE}]
        if self.catalog_has_index("layout"):
            queries.append({"layout": FACETED_VIEW})
        seen = set()
        for query in queries:
            for brain in self.catalog.unrestrictedSearchResults(query):
                path = brain.getPath()
                if path in seen:
                    continue
                seen.add(path)
                try:
                    obj = brain.getObject()
                except Exception:
                    log.exception("Could not get object for %s, skipping", path)
                    continue
                if obj is None:
                    log.warning("Catalog brain %s has no object, skipping", path)
                    continue
                self.cleanup_object(obj)

    def cleanup_object(self, obj):
        if getattr(obj, "layout", None) == FACETED_VIEW:
            obj.layout = ""
        if IFacetedNavigable is not None and IFacetedNavigable.providedBy(obj):
            noLongerProvides(obj, IFacetedNavigable)
        annotations = IAnnotations(obj)
        for key in [key for key in annotations.keys() if "faceted" in str(key).lower()]:
            del annotations[key]
        obj.reindexObject()
        log.info("Cleaned faceted navigation from %s", "/".join(obj.getPhysicalPath()))

    def apply_uninstall_profile(self):
        if IFacetedNavigable is None:
            log.warning(
                "eea.facetednavigation is not importable, cannot apply its "
                "uninstall profile. Registry records are removed directly instead."
            )
            return
        if not self.is_profile_installed(DEFAULT_PROFILE):
            log.info("%s is not installed, nothing to uninstall.", DEFAULT_PROFILE)
            return
        self.setup_install_profile(UNINSTALL_PROFILE)
        self.portal_setup.unsetLastVersionForProfile(DEFAULT_PROFILE)
        log.info("Applied %s", UNINSTALL_PROFILE)

    def cleanup_registry_records(self):
        registry = self.getToolByName("portal_registry")
        for key in [
            key for key in registry.records if key.startswith("eea.facetednavigation")
        ]:
            del registry.records[key]
            log.info("Removed registry record %s", key)
