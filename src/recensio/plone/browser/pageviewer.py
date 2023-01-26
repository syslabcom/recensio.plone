from Products.Five.browser import BrowserView


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
