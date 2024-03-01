from plone.app.dexterity.textindexer.interfaces import IDexterityTextIndexFieldConverter
from recensio.plone.interfaces import IReview
from z3c.form.interfaces import IWidget
from z3c.relationfield.interfaces import IRelationList
from zope.component import adapter
from zope.interface import implementer


@implementer(IDexterityTextIndexFieldConverter)
@adapter(IReview, IRelationList, IWidget)
class AuthorsDexterityTextIndexFieldConverter:
    """Extract author names for indexing in SearchableText"""

    def __init__(self, context, field, _):
        """Initialize field converter"""
        self.context = context
        self.field = field

    def convert(self):
        names = []
        for relation in self.field.get(self.context):
            obj = relation.to_object
            if not obj:
                continue
            names.append(obj.title)
        return ", ".join(names)
