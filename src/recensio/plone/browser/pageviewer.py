from Products.Five.browser import BrowserView
from recensio.plone.utils import review_pdf_fieldname
from zope.publisher.interfaces import NotFound


class Pageviewer(BrowserView):
    """Show the review PDF inline.

    Reviews without a usable PDF fall back to their legacy page images,
    which are kept for exactly that case.
    """

    def review_pdf_embed_url(self):
        fieldname = review_pdf_fieldname(self.context)
        if fieldname:
            return f"{self.context.absolute_url()}/@@display-file/{fieldname}"
        return None

    def get_no_pages(self):
        """Number of legacy page images kept on the review."""
        return len(getattr(self.context, "pagePictures", None) or [])


class GetPageImage(BrowserView):
    """Serve one legacy page image.

    Read-only: images are no longer regenerated, they are only served for
    reviews that kept them as their PDF-less fallback.
    """

    def __call__(self):
        no = self.request.get("no", 1)
        images = getattr(self.context, "pagePictures", None) or []
        if no < 1 or no > len(images):
            raise NotFound(self.context, f"page {no}", self.request)
        image = images[no - 1]
        try:
            size = image.size
        except (TypeError, AttributeError):
            raise NotFound(self.context, f"page {no}", self.request)
        self.request.response.setHeader("Content-Type", "image/gif")
        self.request.response.setHeader("Content-Length", size)
        return image.data
