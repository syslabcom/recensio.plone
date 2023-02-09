from plone.autoform.form import AutoExtensibleForm
from plone.supermodel import model
from recensio.plone import _
from z3c.form import button
from z3c.form import form
from zope import schema


class ISearchSchema(model.Schema):
    SearchableText = schema.TextLine(
        title=_("label_search_text", default="Volltextsuche"),
        description=_(
            "help_search_text",
            default="For a full text search, enter your search term here. Multiple "
            "words may be found by combining them with <strong>AND</strong> and "
            "<strong>OR</strong>.",
        ),
        required=False,
    )
    isbn = schema.TextLine(
        title=_("label_isbn", default="ISBN"),
        description=_("help_isbn", default="Internationale Standardbuchnummer"),
        required=False,
    )

    search = button.Button(title=_("label_search", default="Search"))


class SearchForm(AutoExtensibleForm, form.Form):
    schema = ISearchSchema
    prefix = ""
    ignoreContext = True

    @property
    def action(self):
        return f"{self.context.absolute_url()}/@@search"

    def updateWidgets(self):
        return super().updateWidgets(prefix="")
