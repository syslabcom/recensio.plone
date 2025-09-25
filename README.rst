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

Solr: cave canem
================

This package now works with collective.solr and performs fulltext indexing of PDF documents.

There are a few gotchas:

- Test runs will roughshod nuke your existing indexed data, unless you stop your development solr first.
  We're using a testlayer from collective.solr that connects to port 8983.

- Fulltext indexing of PDFs on reviews works fine, but fulltext indexing of standalone files will error out with a default Solr install.
  To get it to work properly, your Solr needs to be started up with special environment variables::

    SOLR_ENABLE_REMOTE_STREAMING=true SOLR_ENABLE_STREAM_BODY=true SOLR_OPTS="-Dsolr.allowPaths=${instance:blob-storage}"
