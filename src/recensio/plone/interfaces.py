from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IRecensioPloneLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IReview(Interface):
    """Marker interface for reviews and other select content types."""
