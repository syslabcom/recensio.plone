"""Contains code migrated from the old recensio packages."""
from plone import api
from Products.Five import BrowserView
from recensio.plone import _
from recensio.plone.utils import get_formatted_names


NOTIFICATION_LOG_ADDR = "maillog@recensio.net"


class MailNewPublication(BrowserView):
    """Moved and adapted from recensio.policy.browser.email."""

    def __call__(self):
        from_name = api.portal.get_registry_record(
            "plone.email_from_name", default="Recensio"
        )
        from_email = api.portal.get_registry_record(
            "plone.email_from_address", default=""
        )
        mail_from = f"{from_name} <{from_email}>"

        referenceAuthors = getattr(self.context, "referenceAuthors", [])

        for author in referenceAuthors:
            if "email" in author:
                continue
            args = {}
            args["reviewed_author"] = " ".join(
                [author["firstname"], author["lastname"]]
            )
            args["mail_from"] = mail_from
            pref_lang = "en"
            args["title"] = self.context.title + (
                self.context.subtitle and f": {self.context.subtitle}" or ""
            )
            args["review_author"] = get_formatted_names(self.context.reviewAuthors)
            args["concept_url"] = f"{api.portal.get_url()}/ueberuns/konzept"
            args["context_url"] = self.context.absolute_url()
            pref_lang = author["preferred_language"]
            if author.get("email"):
                args["mail_to"] = author["email"]
                msg_template = api.portal.translate(
                    _("mail_new_publication_body", mapping=args),
                    target_language=pref_lang,
                )
            else:
                args["mail_to"] = args["mail_from"]
                msg_template = api.portal.translate(
                    _("mail_new_publication_intro", mapping=args),
                    target_language=pref_lang,
                ) + api.portal.translate(
                    _("mail_new_publication_body", mapping=args),
                    target_language=pref_lang,
                )
            subject = api.portal.translate(
                _(
                    "mail_new_publication_subject",
                    default="Es wurde eine Rezension von ${title} veröffentlicht",
                    mapping=args,
                ),
                target_language=pref_lang,
            )
            self.sendMail(msg_template, args["mail_to"], mail_from, subject)

    def sendMail(
        self,
        msg,
        mail_to,
        mail_from,
        subject,
    ):
        bcc_to = []
        if NOTIFICATION_LOG_ADDR:
            msg = (
                """From: %s
To: %s
Bcc: %s
Subject: %s

"""
                % (mail_from, mail_to, NOTIFICATION_LOG_ADDR, subject)
                + msg
            )
            bcc_to = bcc_to + [NOTIFICATION_LOG_ADDR]
        if not isinstance(mail_to, list):
            mail_to = [mail_to]

        api.portal.send_email(
            recipient=mail_to + bcc_to,
            sender=mail_from,
            subject=subject,
            body=msg,
        )
