from recensio.plone import _
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class HonorificsVocabulary:
    voc = SimpleVocabulary(
        [
            SimpleTerm(value=key, token=key, title=value)
            for key, value in {
                "frau": _("Frau"),
                "herr": _("Herr"),
                "frau_dr": _("Frau Dr."),
                "herr_dr": _("Herr Dr."),
                "frau_prof_dr": _("Frau Prof. Dr."),
                "herr_prof_dr": _("Herr Prof. Dr."),
            }.items()
        ]
    )

    def __call__(self, context=None):
        return self.voc


honorifics_factory = HonorificsVocabulary()
