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


def _listAuthors(obj, listEditors=False):
    if not getattr(obj, "authors", None):
        return []
    retval = []
    if getattr(obj, "curators", None):
        for curator in obj.curators:
            curator_obj = curator.to_object
            if curator_obj.lastname or curator_obj.firstname:
                retval.append(f"{curator_obj.lastname}, {curator_obj.firstname}")
    if listEditors and getattr(obj, "editorial", None):
        for editor in obj.editorial:
            editor_obj = editor.to_object
            if editor_obj.lastname or editor_obj.firstname:
                retval.append(f"{editor_obj.lastname}, {editor_obj.firstname}")
    for author in obj.authors:
        author_obj = author.to_object
        if author_obj.lastname or author_obj.firstname:
            retval.append(f"{author_obj.lastname}, {author_obj.firstname}")
    return retval


@indexer(IReview)
def listAuthors(obj):
    return _listAuthors(obj, listEditors=False)


@indexer(IReview)
def listAuthorsAndEditors(obj):
    return _listAuthors(obj, listEditors=True)


@indexer(IReview)
def listReviewAuthors(obj):
    if not getattr(obj, "reviewAuthors", None):
        return []
    retval = []
    for author in obj.reviewAuthors:
        author_obj = author.to_object
        if author_obj and author_obj.lastname or author_obj.firstname:
            retval.append(f"{author_obj.lastname}, {author_obj.firstname}")
    return retval
