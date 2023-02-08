from z3c.form.term import CollectionTermsVocabulary


class TreeTermsVocabulary(CollectionTermsVocabulary):
    def __iter__(self):
        """Iterate over all values in the tree, not only the first level."""
        return iter(self.terms.term_by_token.values())
