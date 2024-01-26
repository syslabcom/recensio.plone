from plone.app.dexterity.behaviors.metadata import ICategorization
from plone.dexterity.browser import add
from plone.dexterity.browser import edit
from recensio.plone.behaviors.article import IArticle
from recensio.plone.behaviors.authors import IAuthors
from recensio.plone.behaviors.base import IBase
from recensio.plone.behaviors.book_review import IBookReview
from recensio.plone.behaviors.cover_picture import ICoverPicture
from recensio.plone.behaviors.cover_picture import ICoverPictureEditedVolume
from recensio.plone.behaviors.journal_review import IJournalArticleReview
from recensio.plone.behaviors.journal_review import IJournalReview
from recensio.plone.behaviors.printed_review import IPrintedReview
from recensio.plone.behaviors.printed_review import IPrintedReviewEditedVolume
from recensio.plone.behaviors.serial import ISerial
from recensio.plone.behaviors.serial import ISerialEditedVolume
from recensio.plone.behaviors.text_review import ITextReview


order = [
    IArticle,
    IBookReview,
    IJournalReview,
    IAuthors,
    ITextReview,
    IJournalArticleReview,
    IPrintedReview,
    IPrintedReviewEditedVolume,
    ISerial,
    ISerialEditedVolume,
    ICoverPicture,
    ICoverPictureEditedVolume,
    IBase,
    ICategorization,
]


class AddBase(add.DefaultAddForm):
    @property
    def additionalSchemata(self):
        schemata = list(super().additionalSchemata)
        return sorted(schemata, key=lambda s: order.index(s) if s in order else 999)


class AddReviewMonograph(AddBase):
    portal_type = "Review Monograph"


class AddReviewMonographView(add.DefaultAddView):
    form = AddReviewMonograph


class AddReviewJournal(AddBase):
    portal_type = "Review Journal"


class AddReviewJournalView(add.DefaultAddView):
    form = AddReviewJournal


class AddReviewArticleCollection(AddBase):
    portal_type = "Review Article Collection"


class AddReviewArticleCollectionView(add.DefaultAddView):
    form = AddReviewArticleCollection


class AddReviewArticleJournal(AddBase):
    portal_type = "Review Article Journal"


class AddReviewArticleJournalView(add.DefaultAddView):
    form = AddReviewArticleJournal


class AddReviewExhibition(AddBase):
    portal_type = "Review Exhibition"


class AddReviewExhibitionView(add.DefaultAddView):
    form = AddReviewExhibition


class EditForm(edit.DefaultEditForm):
    @property
    def additionalSchemata(self):
        schemata = list(super().additionalSchemata)
        return sorted(schemata, key=lambda s: order.index(s) if s in order else 999)
