# Retiring generated page preview images

Branch `api/retire-preview-images` replaces the generated per-page GIF
previews (`pagePictures`) with previews rendered from the review PDF by a
vendored pdf.js (`browser/resources/pdfjs`).

## Operational procedure

1. Deploy the branch and restart the instances.
2. As a Manager, run the cleanup view on **all three portals**:
   - `/recensio/@@cleanup-previews`
   - `/regio/@@cleanup-previews`
   - `/altertum/@@cleanup-previews`

   The view shows what will be cleaned (objects with a PDF) and what
   will be kept (objects without a PDF, expandable list). The button
   starts the cleanup; it runs inside the request, commits every 1000
   objects, and logs progress to the instance log.
3. Run a ZEO pack. Only the pack frees the disk space (~44 GB of
   preview GIFs across the three portals, per the 2026-11 storage
   analysis in `docs/db-bloat` of the recensio workspace).
4. Verify: `@@cleanup-previews` on each portal should show 0 cleanable
   objects; the kept list should contain only the no-PDF exceptions.

## What stays for the kept objects

The 195 objects on recensio (a few more may exist on regio and
altertum) that keep their preview images are clean-up items for the
recensio staff: each should be given a PDF (or removed). This is being
communicated to them.

While they exist, reviews without a PDF still display their legacy
images, so the following must stay:

- `browser/pageviewer.py` `GetPageImage` and the `get_page_image`
  registration in `browser/configure.zcml`.
- The fallback branches in `browser/templates/review.pt` (the gallery)
  and `browser/templates/pageviewer.pt` (the image loop).
- The gallery CSS in `browser/styles/main.css`
  (`review-gallery__*`) and `browser/javascript/gallery.js` (also used
  by the PDF lightbox).

Once every kept object has been given a PDF (upload one, or make the
review text/doc usable and edit the object so `generatedPdf` is built),
run the cleanup view again; when the kept list is empty everywhere, the
fallback machinery above can be deleted in a final commit, together
with `review_pdf_fieldname`'s `None` branches.
