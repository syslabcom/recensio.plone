#!/usr/bin/python
from plone.base.navigationroot import get_navigation_root
from plone.base.utils import safe_text
from plone.memoize import instance
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from string import ascii_uppercase
from urllib.parse import urlencode

import unicodedata


class AuthorSearchBase(BrowserView):
    """Author index helpers shared by full-page and batch views."""

    ALPHABET = ascii_uppercase
    BATCH_SIZE = 30
    BATCH_FRAGMENT_ID = "authorsearch-batch"

    def _request_int(self, name, default=0):
        value = self.request.get(name, default)
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return default

    def _request_bool(self, name, default=True):
        value = self.request.get(name, default)
        if isinstance(value, str):
            return value.lower() not in {"", "0", "false", "no", "off"}
        return bool(value)

    def _brain_title(self, brain):
        return safe_text(getattr(brain, "Title", "") or brain["Title"])

    def _brain_uid(self, brain):
        return getattr(brain, "UID", "") or brain["UID"]

    def _author_initial(self, title):
        """Return a stable A-Z section label for the author title."""
        for character in (safe_text(title) or "").strip():
            if character.isdigit():
                return "#"
            normalized = unicodedata.normalize("NFKD", character)
            normalized = normalized.encode("ascii", "ignore").decode("ascii")
            if normalized and normalized[0].isalpha():
                return normalized[0].upper()
        return "#"

    def _letter_suffix(self, label):
        return "other" if label == "#" else label.lower()

    def _panel_id(self, label):
        return f"authorsearch-panel-{self._letter_suffix(label)}"

    def _tab_id(self, label):
        return f"authorsearch-tab-{self._letter_suffix(label)}"

    def _authorsearch_query(self, letter=""):
        query = {
            "use_navigation_root:boolean": (
                "True" if self.use_navigation_root else "False"
            )
        }
        if self.search_term:
            query["authors"] = self.search_term
        if letter:
            query["letter"] = letter
        return query

    def authorsearch_href(self, letter=""):
        encoded = urlencode(self._authorsearch_query(letter=letter), doseq=True)
        if encoded:
            return f"{self.authorsearch_url}?{encoded}"
        return self.authorsearch_url

    def batch_url(self, letter, start=0):
        query = self._authorsearch_query()
        query["letter"] = letter
        query["b_start:int"] = start
        query["b_size:int"] = self.BATCH_SIZE
        encoded = urlencode(query, doseq=True)
        return f"{self.context.absolute_url()}/@@authorsearch-batch?{encoded}"

    @property
    def search_term(self):
        return safe_text(self.request.get("authors", "") or "").strip()

    @property
    def use_navigation_root(self):
        return self._request_bool("use_navigation_root", True)

    @property
    @instance.memoize
    def authors(self):
        """All matching authors (lazy catalog result set)."""
        catalog = getToolByName(self.context, "portal_catalog")
        return catalog(self._base_query())

    def _base_query(self):
        """Common catalog query parameters."""
        query = {
            "portal_type": "Person",
            "sort_on": "sortable_title",
            "fl": "Title,UID,path_string",
        }
        if self.use_navigation_root:
            query["path"] = get_navigation_root(self.context)
        if self.search_term:
            query["SearchableText"] = self.search_term.strip("\"'")
        return query

    def _letter_query(self, letter):
        """Catalog query scoped to titles starting with *letter*."""
        query = self._base_query()
        if letter == "#":
            query["sortable_title"] = {"query": ("0", ":"), "range": "min:max"}
        else:
            low = letter.lower()
            high = chr(ord(low) + 1)
            query["sortable_title"] = {"query": (low, high), "range": "min:max"}
        return query

    @instance.memoize
    def _letter_results(self, letter):
        """Lazy catalog results for a single letter (memoized per request)."""
        catalog = getToolByName(self.context, "portal_catalog")
        return catalog(self._letter_query(letter))

    @property
    @instance.memoize
    def available_letters(self):
        letters = [lt for lt in self.ALPHABET if len(self._letter_results(lt))]
        if len(self._letter_results("#")):
            letters.append("#")
        return letters

    @property
    def selected_letter(self):
        requested = safe_text(self.request.get("letter", "") or "").strip().upper()
        if requested in self.available_letters:
            return requested
        if self.available_letters:
            return self.available_letters[0]
        return ""

    def letter_authors(self, letter):
        return self._letter_results(letter)

    def letter_count(self, letter):
        return len(self._letter_results(letter))

    def next_batch_start(self, letter, current_start):
        next_start = current_start + self.BATCH_SIZE
        if next_start < self.letter_count(letter):
            return next_start
        return None

    def next_batch_url(self, letter, current_start):
        next_start = self.next_batch_start(letter, current_start)
        if next_start is None:
            return ""
        return self.batch_url(letter, start=next_start)

    def author_results_url(self, author_uid):
        portal_url = (
            getToolByName(self.context, "portal_url").getPortalObject().absolute_url()
        )
        query = {
            "authorsUID:list": author_uid,
            "advanced_search:boolean": "True",
            "use_navigation_root:boolean": (
                "True" if self.use_navigation_root else "False"
            ),
        }
        return f"{portal_url}/search?{urlencode(query, doseq=True)}"

    def _author_card(self, brain, letter=None):
        title = self._brain_title(brain)
        return {
            "initial": letter or self._author_initial(title),
            "title": title,
            "url": self.author_results_url(self._brain_uid(brain)),
        }

    def _author_cards(self, brains, letter=None):
        return [self._author_card(brain, letter=letter) for brain in brains]

    def panel(self, letter):
        current = letter == self.selected_letter
        initial_authors = (
            self.letter_authors(letter)[: self.BATCH_SIZE] if current else []
        )
        return {
            "authors": self._author_cards(initial_authors, letter=letter),
            "count": self.letter_count(letter),
            "current": current,
            "initial_url": "" if current else self.batch_url(letter, start=0),
            "letter": letter,
            "loaded": current,
            "next_url": current and self.next_batch_url(letter, 0) or "",
            "panel_id": self._panel_id(letter),
            "tab_id": self._tab_id(letter),
        }

    @property
    def panels(self):
        return [self.panel(letter) for letter in self.available_letters]

    @property
    def author_jump_links(self):
        available = set(self.available_letters)
        links = []
        labels = list(self.ALPHABET)
        if "#" in available:
            labels.append("#")
        for label in labels:
            enabled = label in available
            links.append(
                {
                    "current": enabled and label == self.selected_letter,
                    "enabled": enabled,
                    "href": enabled and self.authorsearch_href(label) or "",
                    "label": label,
                    "panel_id": enabled and self._panel_id(label) or "",
                    "tab_id": self._tab_id(label),
                }
            )
        return links

    @property
    def total_authors(self):
        return sum(self.letter_count(lt) for lt in self.available_letters)

    @property
    def portal_title(self):
        return getToolByName(self.context, "portal_url").getPortalObject().Title()

    @property
    def authorsearch_url(self):
        return f"{self.context.absolute_url()}/@@authorsearch"

    @property
    def batch_letter(self):
        letter = safe_text(self.request.get("letter", "") or "").strip().upper()
        if letter in self.available_letters:
            return letter
        return ""

    @property
    def batch_start(self):
        return self._request_int("b_start", 0)

    @property
    def batch_authors(self):
        if not self.batch_letter:
            return []
        authors = self.letter_authors(self.batch_letter)
        return authors[self.batch_start : self.batch_start + self.BATCH_SIZE]

    @property
    def batch_cards(self):
        return self._author_cards(self.batch_authors, letter=self.batch_letter)

    @property
    def batch_next_url(self):
        if not self.batch_letter:
            return ""
        return self.next_batch_url(self.batch_letter, self.batch_start)


class AuthorSearchView(AuthorSearchBase):
    """Full-page author index view."""

    template = ViewPageTemplateFile("templates/authorsearch.pt")

    def __call__(self):
        self.request.set("disable_border", True)
        return self.template(self)


class AuthorSearchBatchView(AuthorSearchBase):
    """Batch fragment view for lazy loading author results."""

    template = ViewPageTemplateFile("templates/authorsearch_batch.pt")

    def __call__(self):
        return self.template(self)
