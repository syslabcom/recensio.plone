from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IRecensioPloneLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IReview(Interface):
    """Marker interface for reviews and other select content types."""

class IRecensioExporter(Interface):
    """Interface for bulk exporting review data"""

    def needs_to_run():
        """True if the exporter needs to be run at the time of the call,
        False if the exporter thinks it has nothing to do right now, e.g. a
        recent export is still stored"""

    def add_review():
        """Accepts a review that is to be exported in the current run."""

    def export():
        """Finishes the current export run. This should store the exported
        data in a way appropriate for the export."""
