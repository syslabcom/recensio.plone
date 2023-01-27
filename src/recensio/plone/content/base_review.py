class BaseReview:
    @property
    def page_start_end_in_print(self):
        """See #2630 PAJ/PAEV/RJ/RM have page start and end fields."""

        page_start = getattr(
            self.context,
            "pageStartOfPresentedTextInPrint",
            getattr(self.context, "pageStartOfReviewInJournal", ""),
        )

        page_end = getattr(
            self.context,
            "pageEndOfPresentedTextInPrint",
            getattr(self.context, "pageEndOfReviewInJournal", ""),
        )
        return self.format_page_start_end(page_start, page_end)

    @property
    def page_start_end_in_print_article(self):
        page_start = getattr(self.context, "pageStartOfArticle", "")
        page_end = getattr(self.context, "pageEndOfArticle", "")
        return self.format_page_start_end(page_start, page_end)

    def format_page_start_end(self, page_start, page_end):
        # page_start is set to 0 when it is left empty in the bulk
        # import spreadsheet #4054
        if page_start in (None, 0):
            page_start = ""
        page_start = str(page_start).strip()

        # page_end is set to 0 when it is left empty in the bulk
        # import spreadsheet #4054
        if page_end in (None, 0):
            page_end = ""
        page_end = str(page_end).strip()

        if page_start == page_end:
            # both the same/empty
            page_start_end = page_start
        elif page_start and page_end:
            page_start_end = f"{page_start}-{page_end}"
        else:
            # one is not empty
            page_start_end = page_start or page_end
        return page_start_end
