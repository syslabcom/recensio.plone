from ftw.upgrade import UpgradeStep
from plone import api


class SetMenuStructure(UpgradeStep):
    """Set menu structure."""

    def __call__(self):
        self.install_upgrade_profile()

        # Set the "rezensionen" folder to use the "latest-review-items" layout
        # for all languages
        portal = api.portal.get()
        reviews = portal.rezensionen

        reviews_de = api.content.create(
            container=reviews,
            type="Document",
            id="rezensionen",
            title="Rezensionen",
            language="de",
        )
        reviews_de.setLayout("latest-review-items")
        api.content.transition(reviews_de, "publish")

        reviews_fr = api.content.create(
            container=reviews,
            type="Document",
            id="recensions",
            title="Recensions",
            language="fr",
        )
        reviews_fr.setLayout("latest-review-items")
        api.content.transition(reviews_fr, "publish")

        reviews_en = api.content.create(
            container=reviews,
            type="Document",
            id="reviews",
            title="Reviews",
            language="en",
        )
        reviews_en.setLayout("latest-review-items")
        api.content.transition(reviews_en, "publish")

        reviews.setDefaultPage("rezensionen")
