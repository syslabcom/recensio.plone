==============
recensio.plone
==============

Base package of the Recensio Plone portal.

Requirements
============

We need some system packages to be available for this package to be fully functional:

- abiword (doc to pdf)
- ghostscript (pdf)
- imagemagick (to use convert for pdf pages images)
- openjdk (pdftk/solr)
- pdftk (works on pdf)
- poppler_utils (pdf)
- html-tidy (cleans up the html that will be converted to pdf)


Migration
=========

Read `Notes on speed and large migrations <https://github.com/collective/collective.exportimport#notes-on-speed-and-large-migrations>`_ in the collective.exportimport README.

Then decide if you want to do an export from Plone 4 and only set blob paths.
If so, set the `COLLECTIVE_EXPORTIMPORT_BLOB_HOME` variable on import.

Also disable the recensio event subscribers which would generate PDFs from already generated content.
To do this, set `RECENSIO_DISABLE_SUBSCRIBERS=true`.

After successful migration import the page pictures, which were not in the Recensio Archetypes schema in Plone 4 and therefore not exported.
The blob home environment variable must be set to import the page pictures.

`http://localhost:8080/recensio/@@import-page-pictures`
