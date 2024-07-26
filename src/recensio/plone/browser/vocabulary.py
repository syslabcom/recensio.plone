from AccessControl import getSecurityManager
from Acquisition import aq_base
from html import unescape
from plone.app.content.browser.vocabulary import _parseJSON
from plone.app.content.browser.vocabulary import _safe_callable_metadata
from plone.app.content.browser.vocabulary import _unsafe_metadata
from plone.app.content.browser.vocabulary import DEFAULT_PERMISSION_SECURE
from plone.app.content.browser.vocabulary import MAX_BATCH_SIZE
from plone.app.content.browser.vocabulary import VocabLookupException
from plone.app.content.browser.vocabulary import VocabularyView
from plone.app.content.utils import json_dumps
from plone.base import PloneMessageFactory as _
from plone.base.utils import safe_text
from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.MimeTypeItem import guess_icon_path
from Products.MimetypesRegistry.MimeTypeItem import PREFIX
from Products.PortalTransforms.transforms.safe_html import SafeHTML
from zope.i18n import translate

import itertools


class RecensioVocabularyView(VocabularyView):
    def __call__(self):
        """
        Accepts GET parameters of:
        name: Name of the vocabulary
        field: Name of the field the vocabulary is being retrieved for
        query: string or json object of criteria and options.
            json value consists of a structure:
                {
                    criteria: object,
                    sort_on: index,
                    sort_order: (asc|reversed)
                }
        attributes: comma separated, or json object list
        batch: {
            page: 1-based page of results,
            size: size of paged results
        }
        """
        context = self.get_context()
        self.request.response.setHeader(
            "Content-Type", "application/json; charset=utf-8"
        )

        try:
            vocabulary = self.get_vocabulary()
        except VocabLookupException as e:
            return json_dumps({"error": e.args[0]})

        results_are_brains = False
        if hasattr(vocabulary, "search_catalog"):
            query = self.parsed_query()
            results = vocabulary.search_catalog(query)
            results_are_brains = True
        elif hasattr(vocabulary, "search"):
            try:
                query = self.parsed_query()["SearchableText"]["query"]
            except KeyError:
                results = iter(vocabulary)
            else:
                results = vocabulary.search(query)
        else:
            results = vocabulary

        try:
            total = len(results)
        except TypeError:
            # do not error if object does not support __len__
            # we'll check again later if we can figure some size
            # out
            total = 0

        # get batch
        batch = _parseJSON(self.request.get("batch", ""))
        if batch and ("size" not in batch or "page" not in batch):
            batch = None  # batching not providing correct options
        if batch:
            # must be sliceable for batching support
            page = int(batch["page"])
            size = int(batch["size"])
            if size > MAX_BATCH_SIZE:
                raise Exception("Max batch size is 500")
            # page is being passed in is 1-based
            start = (max(page - 1, 0)) * size
            end = start + size
            # Try __getitem__-based slice, then iterator slice.
            # The iterator slice has to consume the iterator through
            # to the desired slice, but that shouldn't be the end
            # of the world because at some point the user will hopefully
            # give up scrolling and search instead.
            try:
                results = results[start:end]
            except TypeError:
                results = itertools.islice(results, start, end)

        # build result items
        items = []

        attributes = _parseJSON(self.request.get("attributes", ""))
        if isinstance(attributes, str) and attributes:
            attributes = attributes.split(",")

        translate_ignored = self.get_translated_ignored()
        transform = SafeHTML()
        if attributes:
            base_path = self.get_base_path(context)
            sm = getSecurityManager()
            can_edit = sm.checkPermission(DEFAULT_PERMISSION_SECURE, context)
            mtt = getToolByName(self.context, "mimetypes_registry")
            for vocab_item in results:
                if not results_are_brains:
                    vocab_item = vocab_item.value
                item = {}
                for attr in attributes:
                    key = attr
                    if ":" in attr:
                        key, attr = attr.split(":", 1)
                    if attr in _unsafe_metadata and not can_edit:
                        continue
                    if key == "path":
                        attr = "getPath"
                    val = getattr(vocab_item, attr, None)
                    if callable(val):
                        if attr in _safe_callable_metadata:
                            val = val()
                        else:
                            continue
                    if key == "path" and val is not None:
                        val = val[len(base_path) :]
                    if key not in translate_ignored and isinstance(val, str):
                        val = translate(_(safe_text(val)), context=self.request)
                    item[key] = val
                    if key == "getMimeIcon":
                        item[key] = None
                        # get mime type icon url from mimetype registry'
                        contenttype = aq_base(getattr(vocab_item, "mime_type", None))
                        if contenttype:
                            ctype = mtt.lookup(contenttype)
                            if ctype:
                                item[key] = "/".join(
                                    [base_path, guess_icon_path(ctype[0])]
                                )
                            else:
                                item[key] = "/".join(
                                    [
                                        base_path,
                                        PREFIX.rstrip("/"),
                                        "unknown.png",
                                    ]
                                )
                items.append(item)
        else:
            items = [
                {
                    "id": item.value,
                    "text": (item.title if item.title else ""),
                }
                for item in results
            ]

        if total == 0:
            total = len(items)

        return unescape(
            transform.scrub_html(json_dumps({"results": items, "total": total}))
        )
