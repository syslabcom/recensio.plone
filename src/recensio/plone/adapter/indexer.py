from plone.indexer.decorator import indexer
from recensio.plone.interfaces import IReview


@indexer(IReview)
def authorsUID(obj):
    authors = (
        getattr(obj, "authors", [])
        + getattr(obj, "reviewAuthors", [])
        + getattr(obj, "editorial", [])
        + getattr(obj, "curators", [])
    )
    uids = []
    for author in authors:
        author_obj = author.to_object
        if author_obj:
            uids.append(author_obj.UID())
    return uids
