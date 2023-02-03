from plone.app.dexterity.behaviors.nextprevious import NextPreviousBase
from plone.app.layout.nextprevious.interfaces import INextPreviousProvider
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from recensio.plone.config import REVIEW_TYPES
from recensio.plone.content.issue import IIssue
from recensio.plone.content.volume import IVolume
from zope.component import adapter
from zope.interface import implementer


@implementer(INextPreviousProvider)
class RecensioFolderNextPrevious(NextPreviousBase):
    """Use EffectiveDate to determine next/previous instead of
    getObjPositionInParent."""

    @property
    def enabled(self):
        return True

    @memoize
    def itemRelatives(self, oid):
        """Get the relative next and previous items."""
        catalog = getToolByName(self.context, "portal_catalog")
        obj = self.context[oid]
        path = "/".join(obj.getPhysicalPath())

        previous = None
        next = None

        result = sorted(
            catalog(self.buildNextPreviousQuery()),
            key=lambda x: x.get("listAuthorsAndEditors", [])
            and x["listAuthorsAndEditors"][0],
        )
        if result and len(result) > 1:
            pathlist = [x.getPath() for x in result]
            if path in pathlist:
                index = pathlist.index(path)
                if index - 1 >= 0:
                    previous = self.buildNextPreviousItem(result[index - 1])
                if index + 1 < len(result):
                    next = self.buildNextPreviousItem(result[index + 1])

        nextPrevious = {
            "next": next,
            "previous": previous,
        }

        return nextPrevious

    def buildNextPreviousQuery(self):
        query = {}
        query["portal_type"] = REVIEW_TYPES
        query["path"] = dict(query="/".join(self.context.getPhysicalPath()), depth=1)
        query["b_size"] = 10000

        # Filters on content
        query["is_default_page"] = False
        query["is_folderish"] = False

        return query


@adapter(IVolume)
class RecensioVolumeNextPrevious(RecensioFolderNextPrevious):
    pass


@adapter(IIssue)
class RecensioIssueNextPrevious(RecensioFolderNextPrevious):
    pass
