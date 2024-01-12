from collective.exportimport.import_other import ImportRelations as OrigImportRelations


class ImportRelations(OrigImportRelations):
    # Define relationship to field mapping for Recensio.
    RELATIONSHIP_FIELD_MAPPING = {
        # default relations of Plone 4 > 5
        "Working Copy Relation": "iterate-working-copy",
        "relatesTo": "relatedItems",
        # recensio specific relations
        "author": "authors",
        "reviewAuthor": "reviewAuthors",
        "editor": "editorial",
        "custom_licence": "licence_ref",
        "curator": "curators",
    }
