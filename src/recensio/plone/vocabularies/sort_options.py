from recensio.plone import _
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class SortOptionsVocabulary:
    def __call__(self, *args, **kwargs):
        options = {
            "relevance": _("Relevance"),
            "sortable_title": _("Titel/alphabetisch"),
            "modified": _("label_modification_date"),
            "created": _("label_creation_date", default="Erstellungsdatum"),
        }
        return SimpleVocabulary(
            [SimpleTerm(key, key, value) for key, value in options.items()]
        )
