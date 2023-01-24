from plone import api
from plone.app.dexterity import textindexer
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from recensio.plone import _
from zope import schema
from zope.component import adapter
from zope.interface import provider


def get_user_email():
    return api.user.get_current().getProperty("email")


def get_user_home_page():
    return api.user.get_current().getProperty("home_page")


@provider(IFormFieldProvider)
class IBasePresentation(model.Schema):

    labelPresentationAuthor = schema.TextLine(
        title=_("label_presentation_author", default=("")),
        required=False,
    )
    directives.mode(labelPresentationAuthor="display")
    textindexer.searchable("labelPresentationAuthor")

    reviewAuthorHonorific = schema.Choice(
        title=_("Honorific Title"),
        vocabulary="recensio.plone.vocabularies.honorifics",
        required=True,
    )

    reviewAuthorEmail = schema.TextLine(
        title=_("Email address (not publicly visible)"),
        required=True,
        defaultFactory=get_user_email,
    )

    reviewAuthorPersonalUrl = schema.TextLine(
        title=_("Personal webpage URL/URN"),
        description=_(
            "description_personal_webpage",
            default=(
                "Here you can link to your personal website (e.g. within a "
                "network of historians, a university or research institution). "
                "It should preferably be persistent or be corrected by you in "
                "case of changes (e.g. change of university)."
            ),
        ),
        required=False,
        defaultFactory=get_user_home_page,
    )

    isLicenceApproved = schema.Bool(
        title=_("Licence Agreement"),
        description=_(
            "description_ccby_licence_approval",
            default=(
                "I agree that my presentation will be published by recensio.net "
                "under the <a "
                "href='http://creativecommons.org/licenses/by-nc-nd/2.0/deed.en' "
                "target='_blank'>"
                "creative-commons-licence Attribution-NonCommercial-"
                "NoDerivs (CC-BY-NC-ND)</a>. Under these conditions, platform "
                "users may use it electronically, distribute it, print it and "
                "provide it for download. The editorial team reserves its right "
                "to change incoming posts (see our user guidelines to this)."
            ),
        ),
        required=True,
        default=False,
    )


@adapter(IDexterityContent)
class BasePresentation:
    """Adapter for IBasePresentation."""

    def __init__(self, context):
        self.context = context

    @property
    def labelPresentationAuthor(self):
        return ""

    @labelPresentationAuthor.setter
    def labelPresentationAuthor(self, value):
        pass

    @property
    def reviewAuthorHonorific(self):
        return self.context.reviewAuthorHonorific

    @reviewAuthorHonorific.setter
    def reviewAuthorHonorific(self, value):
        self.context.reviewAuthorHonorific = value

    @property
    def reviewAuthorEmail(self):
        return self.context.reviewAuthorEmail

    @reviewAuthorEmail.setter
    def reviewAuthorEmail(self, value):
        self.context.reviewAuthorEmail = value

    @property
    def reviewAuthorPersonalUrl(self):
        return self.context.reviewAuthorPersonalUrl

    @reviewAuthorPersonalUrl.setter
    def reviewAuthorPersonalUrl(self, value):
        self.context.reviewAuthorPersonalUrl = value

    @property
    def isLicenceApproved(self):
        return self.context.isLicenceApproved

    @isLicenceApproved.setter
    def isLicenceApproved(self, value):
        self.context.isLicenceApproved = value
