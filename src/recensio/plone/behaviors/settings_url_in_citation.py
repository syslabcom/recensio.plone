from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import provider


description_is_url_shown_in_citation_note = _(
    "description_is_url_shown_in_citation_note",
    default=(
        'Zeige die URL der Rezension in der "Zitierhinweis"-Box. '
        "Diese Option kann hier nicht deaktiviert werden, wenn sie "
        "bereits auf einer übergeordneten Ebene (Zeitschrift, Band, "
        "Ausgabe) deaktiviert ist. Die Einstellung hat außerdem keine "
        "Wirkung, falls ein externer Volltext für die Rezension "
        "benutzt wird; in diesem Fall bleibt die URL immer versteckt. "
        "Beachten Sie, dass diese Einstellung weder den eigentlichen "
        "Zitierhinweis noch die Anzeige der Original-URL beeinflusst."
    ),
)


@provider(IFormFieldProvider)
class ISettingsURLInCitation(model.Schema):
    # TODO:
    # schemata="review",
    # condition="python:object.aq_parent.isURLShownInCitationNote() if object.aq_parent != object else True",
    # Show only as label, if:
    #     condition="python:not object.aq_parent.isURLShownInCitationNote() if object.aq_parent != object else False",
    URLShownInCitationNote = schema.Bool(
        title=_(
            "label_is_url_shown_in_citation_note",
            default="Show URL in citation rules box",
        ),
        description=description_is_url_shown_in_citation_note,
        default=True,
        required=False,
    )


@adapter(IDexterityContent)
class SettingsURLInCitation:
    """Adapter for ISettingsURLInCitation."""

    def __init__(self, context):
        self.context = context

    @property
    def URLShownInCitationNote(self):
        return self.context.URLShownInCitationNote

    @URLShownInCitationNote.setter
    def URLShownInCitationNote(self, value):
        self.context.URLShownInCitationNote = value
