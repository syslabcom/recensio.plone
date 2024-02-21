from lxml import etree

import logging


logger = logging.getLogger(__name__)


class NoReview(Exception):
    pass


class SehepunkteParser:
    def parse(self, data):
        # XXX protect against XML attacks?
        # We do trust the sehepunkte website,  but in case it gets taken over by a
        # malicious actor some extra protection would be good.
        # Bandit recommends `defusedxml`
        root = etree.fromstring(data)  # nosec B320
        global_data = self._getGlobalData(root)
        for review in root:
            try:
                review_data = self._getReviewData(review)
            except NoReview:
                continue
            review_data.update(global_data)
            for book in review.xpath("book"):
                book_data = self._getBookData(book)
                book_data.update(review_data)
                yield book_data

    def _getGlobalData(self, elem):
        return {
            "issue": elem.get("number"),
            "volume": elem.get("volume"),
            "year": elem.get("year"),
        }

    def _getReviewData(self, root):
        def xpath_single(x):
            return "".join(root.xpath(x)).strip()

        if root.tag != "review":
            logger.error(
                "This XML Format seems to be unclean, it contained an "
                "unknown element after the issue tag"
            )
            raise NoReview()
        canonical_uri = xpath_single("filename/text()")

        return {
            "category": xpath_single("category/text()"),
            "reviewAuthors": [
                {
                    "lastname": xpath_single("reviewer/last_name/text()"),
                    "firstname": xpath_single("reviewer/first_name/text()"),
                }
            ],
            "canonical_uri": canonical_uri,
        }

    def _getBookData(self, root):
        def xpath_single(x):
            return "".join(root.xpath(x)).strip()

        authors = []
        for i in range(1, 4):
            authors.append(
                {
                    "lastname": xpath_single("author_%i_last_name/text()" % i),
                    "firstname": xpath_single("author_%i_first_name/text()" % i),
                }
            )
        authors = [x for x in authors if x["lastname"] or x["firstname"]]

        return {
            "authors": authors,
            "isbn": xpath_single("isbn/text()"),
            "title": xpath_single("title/text()"),
            "subtitle": xpath_single("subtitle/text()"),
            "placeOfPublication": xpath_single("place_of_publication/text()"),
            "publisher": xpath_single("publishing_company/text()"),
            "yearOfPublication": xpath_single("year/text()"),
            "series": xpath_single("series/text()"),
            "pages": xpath_single("pages/text()"),
        }


sehepunkte_parser = SehepunkteParser()
