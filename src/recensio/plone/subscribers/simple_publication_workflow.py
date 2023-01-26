from DateTime import DateTime
from logging import getLogger
from plone import api
from recensio.plone import _
from recensio.plone.controlpanel.settings import IRecensioSettings


logger = getLogger(__name__)


def mail_after_publication(obj, event):
    """Send an email if the workflow of the obj is simple publication workflow
    and the object is published."""
    wf = api.portal.get_tool("portal_workflow")

    if wf.getChainFor(obj)[0] != "simple_publication_workflow":
        return

    review_state = api.content.get_state(obj, "review_state")
    if review_state != "published":
        return

    from_name = api.portal.get_registry_record(
        "plone.email_from_name", default="Recensio"
    )
    from_email = api.portal.get_registry_record("plone.email_from_address", default="")
    mail_from = f"{from_name} <{from_email}>"

    user = api.user.get_current()
    user_email = user.getProperty("email")

    msg = ""

    if event.action == "publish":
        obj.setEffectiveDate(DateTime())
        obj.reindexObject()

    if event.action == "submit":
        subject = _("label_item_submitted", default="Content was submitted")
        mail_to = api.portal.get_registry_record(
            name="review_submitted_email",
            interface=IRecensioSettings,
            default=mail_from,
        )
        msg = f"""User {user.getUserName()} (mailto:{user_email}) has submitted a {obj.portal_type} for review.

Please check it out a {obj.absolute_url()}.
"""  # noqa: E501

    elif (
        event.action == "publish"
        and obj.workflow_history["simple_publication_workflow"][-2]["review_state"]
        == "pending"
    ):
        owner = obj.getOwner()
        mail_to = owner.getProperty("email")
        pref_lang = owner.getProperty("preferred_language", "de")
        subject = api.portal.translate(
            _("label_item_published", default="Your item has been published"),
            domain="recensio",
            lang=pref_lang,
        )

        api.content.get_view("mail_new_presentation", context=obj)()

        publish_notification_template = _(
            "publish_notification_template",
            default="""Ihr Artikel "${title}" wurde freigeschaltet und ist nun unter ${url} verfügbar.""",
            mapping=dict(
                title=obj.Title(),
                url=obj.absolute_url(),
            ),
        )
        msg = api.portal.translate(
            publish_notification_template,
            domain="recensio",
            lang=pref_lang,
        )

    if not msg:
        return

    try:
        logger.info("I am sending the following msg:\n%r", msg)
        api.portal.send_email(
            recipient=mail_to,
            subject=subject,
            body=msg,
        )
    except Exception:
        logger.exception(
            "Not possible to send email notification for workflow change on %r",
            obj.absolute_url(),
        )
