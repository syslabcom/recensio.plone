from Acquisition import aq_base
from logging import getLogger
from plone.protect import createToken
from Products.Five.browser import BrowserView
from recensio.plone.utils import review_pdf_fieldname

import transaction

logger = getLogger(__name__)

REVIEW_TYPES = [
    "Review Monograph",
    "Review Journal",
    "Review Exhibition",
    "Review Article Journal",
    "Review Article Collection",
    "Presentation Monograph",
    "Presentation Collection",
    "Presentation Article Review",
    "Presentation Online Resource",
]

BATCH_SIZE = 1000


class CleanupPreviewsView(BrowserView):
    """Release legacy page preview images (pagePictures) from reviews.

    Reviews with a usable PDF no longer need their generated page images:
    the preview is rendered from the PDF by pdf.js. Reviews without a PDF
    keep their images as their only visual.
    """

    feedback = None
    stats = None

    def _walk_reviews(self):
        catalog = self.context.portal_catalog
        seen = 0
        for portal_type in REVIEW_TYPES:
            brains = catalog.unrestrictedSearchResults(portal_type=portal_type)
            for brain in brains:
                try:
                    obj = brain.getObject()
                except Exception:
                    continue
                seen += 1
                if seen % 200 == 0:
                    self.context._p_jar.cacheMinimize()
                yield obj

    def collect_stats(self):
        cleanable_objects = 0
        cleanable_images = 0
        kept_urls = []
        for obj in self._walk_reviews():
            page_pictures = getattr(aq_base(obj), "pagePictures", None)
            if not page_pictures:
                continue
            if review_pdf_fieldname(obj):
                cleanable_objects += 1
                cleanable_images += len(page_pictures)
            else:
                kept_urls.append(obj.absolute_url())
        return {
            "cleanable_objects": cleanable_objects,
            "cleanable_images": cleanable_images,
            "kept_urls": kept_urls,
        }

    def run_cleanup(self):
        portal_id = self.context.getId()
        processed = 0
        purged_objects = 0
        purged_images = 0
        logger.info("cleanup-previews %s: starting", portal_id)
        for obj in self._walk_reviews():
            processed += 1
            page_pictures = getattr(aq_base(obj), "pagePictures", None)
            if page_pictures and review_pdf_fieldname(obj):
                purged_images += len(page_pictures)
                delattr(obj, "pagePictures")
                purged_objects += 1
            if processed % BATCH_SIZE == 0:
                transaction.commit()
                logger.info(
                    "cleanup-previews %s: %d objects processed, %d cleaned",
                    portal_id,
                    processed,
                    purged_objects,
                )
        transaction.commit()
        logger.info(
            "cleanup-previews %s: finished - %d objects processed, "
            "%d cleaned, %d preview images released",
            portal_id,
            processed,
            purged_objects,
            purged_images,
        )
        return {
            "processed": processed,
            "purged_objects": purged_objects,
            "purged_images": purged_images,
        }

    def token(self):
        return createToken()

    def __call__(self):
        if self.request.method == "POST" and self.request.form.get("confirm") == "yes":
            self.feedback = self.run_cleanup()
        self.stats = self.collect_stats()
        return self.index()
