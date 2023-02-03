from Products.Five.browser import BrowserView
from recensio.plone.subscribers.review import review_pdf_updated_eventhandler


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
        no = self.request.get("no", 1)
        refresh = self.request.get("refresh", False)

        images = getattr(self.context, "pagePictures", [])

        if images is None or refresh:
            review_pdf_updated_eventhandler(self, None)
            images = getattr(self.context, "pagePictures", [])

        if no > len(images):
            no = 0

        try:
            image = images[no - 1]
            image.size
        except (TypeError, AttributeError):
            # 17.8.2012 Fallback if upgrade is not done yet
            review_pdf_updated_eventhandler(self, None)
            images = getattr(self.context, "pagePictures", [])

        image = images[no - 1]
        self.request.response.setHeader("Content-Type", "image/gif")
        self.request.response.setHeader("Content-Length", image.size)

        return image.data
