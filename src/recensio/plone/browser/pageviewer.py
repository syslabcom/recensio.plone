from plone.namedfile.file import NamedBlobImage
from Products.Five.browser import BrowserView


def review_pdf_updated_eventhandler(obj, event):
    """XXX: replace me with the proper handler"""


class Pageviewer(BrowserView):
    """Views a review's page images (generated from pdf)"""

    def get_no_pages(self):
        """Return the number of pages that are stored as images See
        get_page_image()"""
        pagePictures = getattr(self.context, "pagePictures", [])
        return len(pagePictures)

    def __call__(self):
        html = '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n<head></head>\n<body>\n'
        for i in range(self.get_no_pages() + 1)[1:]:
            html = (
                html
                + '    <div>\n      <img src="'
                + self.context.absolute_url()
                + "/get_page_image?no:int=%d" % i
                + '" alt="Review page %d">' % i
                + "\n    </div>\n"
            )
        html = html + "</body>\n</html>\n"

        return html


class GetPageImage(BrowserView):
    def __call__(self):
        """Return a page of the review text."""
        # XXX Remove me
        images_default = [
            NamedBlobImage(
                data=b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",  # noqa: E501
                filename="blank.gif",
            )
        ]
        no = self.request.get("no", 1)
        refresh = self.request.get("refresh", False)

        images = getattr(self, "pagePictures", images_default)

        if images is None or refresh:
            review_pdf_updated_eventhandler(self, None)
            images = getattr(self, "pagePictures", images_default)

        if no > len(images):
            no = 0

        try:
            image = images[no - 1]
            image.size
        except (TypeError, AttributeError):
            # 17.8.2012 Fallback if upgrade is not done yet
            review_pdf_updated_eventhandler(self, None)
            images = getattr(self, "pagePictures", images_default)

        image = images[no - 1]
        self.request.response.setHeader("Content-Type", "image/gif")
        self.request.response.setHeader("Content-Length", image.size)

        return image.data
