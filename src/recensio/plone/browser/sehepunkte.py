from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from guess_language import guessLanguage as originalGuessLanguage
from itertools import chain
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from recensio.plone.sehepunkte import sehepunkte_parser
from recensio.plone.tools import convertToString
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.event import notify
from zope.interface import alsoProvides
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory

import datetime
import html.entities
import logging
import re
import requests


log = logging.getLogger(__name__)


def convert(vocab):
    retval = {}
    if not vocab:
        return retval
    for key, value in vocab.items():
        if isinstance(value, tuple):
            retval[value[0]] = key
            retval.update(convert(value[1]))
        elif isinstance(value, str):
            retval[value] = key
    return retval


def superclean(text):
    def unescape(text):
        def fixup1(m):
            return inner_fixup(m)

        def fixup2(m):
            return inner_fixup(m, True)

        def inner_fixup(m, i_thought_i_can_write_html_by_hand_but_i_cant=False):
            tailcut = -1
            if i_thought_i_can_write_html_by_hand_but_i_cant:
                tailcut = 1000
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return chr(int(text[3:tailcut], 16))
                    else:
                        return chr(int(text[2:tailcut]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = chr(html.entities.name2codepoint[text[1:tailcut]])
                except KeyError:
                    pass
            return text  # leave as is

        return re.sub(r"&#?\d+", fixup2, re.sub(r"&#?\d+;", fixup1, text))

    return unescape(text)


class Import(BrowserView):
    """"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.mag = self.context.rezensionen.zeitschriften.sehepunkte
        self.plone_utils = getToolByName(context, "plone_utils")

        self.topic_values = convert(
            getUtility(IVocabularyFactory, "recensio.plone.vocabularies.topic_values")(
                context
            ).vdex.getVocabularyDict(lang="de")
        )
        self.epoch_values = convert(
            getUtility(IVocabularyFactory, "recensio.plone.vocabularies.epoch_values")(
                context
            ).vdex.getVocabularyDict(lang="de")
        )
        self.region_values = convert(
            getUtility(IVocabularyFactory, "recensio.plone.vocabularies.region_values")(
                context
            ).vdex.getVocabularyDict(lang="de")
        )

    def __call__(self):
        data = []
        before = datetime.datetime.now()
        review_count = 0
        for url in self._getTargetURLs():
            try:
                response = requests.get(url)
                sehepunkte_xml = response.content
                data.append(sehepunkte_parser.parse(sehepunkte_xml))
            except OSError:
                pass  # The library takes care of logging a failure
        for review in chain(*data):
            try:
                self._addReview(self._convertVocabulary(convertToString(review)))
                review_count += 1
            except Exception:
                log.exception(
                    "Warning, sehepunkte import failed! Exception "
                    "has not been caught, but bubbled. Probably sehepunkte "
                    "is broken now! Please see #4656 for fixes"
                )
                raise

        total = (datetime.datetime.now() - before).seconds / 1.0
        log.info(
            "Sehepunkte finished. Imported %i reviews in %f seconds. %f reviews/s",
            review_count,
            total,
            total and review_count / total or review_count,
        )
        if review_count > 0:
            alsoProvides(self.request, IDisableCSRFProtection)
        return "Success"

    def _getTargetURLs(self):
        base = "https://www.sehepunkte.de/export/sehepunkte_%s.xml"
        now = datetime.datetime.now()
        past_months = int(self.request.get("past_months", 1))
        for idx in reversed(range(past_months + 1)):
            target_date = now - relativedelta(months=idx)
            yield base % (target_date).strftime("%Y_%m")
        target_date = now + relativedelta(months=1)
        yield base % (target_date).strftime("%Y_%m")

    def _convertAuthors(self, authors):
        author_objects = []
        gnd_view = api.content.get_view(
            context=self.context,
            request=self.request,
            name="gnd-view",
        )
        for author in authors:
            if author["firstname"] or author["lastname"]:
                existing = gnd_view.getByName(
                    firstname=author["firstname"],
                    lastname=author["lastname"],
                    solr=False,  # solr is only committed on transaction commit
                )
                if existing:
                    author_objects.append(existing[0].getObject())
                else:
                    author_objects.append(
                        gnd_view.createPerson(
                            firstname=author["firstname"],
                            lastname=author["lastname"],
                        )
                    )
        intids = getUtility(IIntIds)
        return [RelationValue(intids.getId(author)) for author in author_objects]

    def _addReview(self, review):
        if review["volume"] not in self.mag:
            self.mag.invokeFactory(
                type_name="Volume",
                id=review["volume"],
                title="{} ({})".format(review["volume"], review["year"]),
            )
        volume = self.mag[review["volume"]]
        if review["issue"] not in volume:
            volume.invokeFactory(
                type_name="Issue", id=review["issue"], title=review["issue"]
            )
        issue = volume[review["issue"]]
        new_id = self.plone_utils.normalizeString(review["title"])
        if new_id in issue:
            return

        def guessLanguage(text):
            lang = originalGuessLanguage(text)
            if lang == "UNKNOWN":
                lang = "de"
            return lang

        review = self._extractAndSanitizeHTML(review)
        languageReview = guessLanguage(review["review"])
        languageReviewedText = guessLanguage(review["title"])
        issue.invokeFactory(type_name="Review Monograph", id=new_id)
        review_ob = issue[new_id]
        review_ob.languageReview = [languageReview]
        review_ob.languageReviewedText = [languageReviewedText]

        authors = review.pop("authors")
        review_ob.authors = self._convertAuthors(authors)
        reviewAuthors = review.pop("reviewAuthors")
        review_ob.reviewAuthors = self._convertAuthors(reviewAuthors)

        review_ob.review = RichTextValue(review.pop("review"))

        for key, value in review.items():
            if isinstance(value, str):
                value = superclean(value)
            setattr(review_ob, key, value)
        notify(ObjectModifiedEvent(review_ob))

    def _convertVocabulary(self, review):
        category = review.pop("category")

        def setter(mapper):
            return [x for x in [mapper.get(category, "")] if x]

        review["ddcSubject"] = setter(self.topic_values)
        review["ddcTime"] = setter(self.epoch_values)
        review["ddcPlace"] = setter(self.region_values)
        return review

    def _extractAndSanitizeHTML(self, review):
        # XXX check scheme? (bandit)
        response = requests.get(review["canonical_uri"])
        html = response.content
        soup = BeautifulSoup(html, "lxml")
        dirt = soup.findAll("div", {"class": "box"})
        for div in dirt:
            div_header = div.find("div", {"class": "header"})
            if not div_header or div_header.text != "Empfohlene Zitierweise:":
                continue
            review["canonical_uri"] = div.p.a["href"]
            review["customCitation"] = div.p.text
        [x.extract() for x in dirt]
        try:
            review["review"] = soup.find("div", id="text_area").prettify()
        except AttributeError:
            try:
                review["review"] = soup.find("body", {"class": "printable"}).prettify()
            except AttributeError:
                review["review"] = soup.prettify()
        return review
