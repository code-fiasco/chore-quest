import logging
import smtplib
from email.message import EmailMessage
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmailError(Exception):
    pass


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> None:
    """Send an email via SMTP (local) or Resend (production)."""
    plain = text_body or _html_to_plain_text(html_body)

    if settings.is_production:
        _send_via_resend(to=to, subject=subject, html_body=html_body, text_body=plain)
    else:
        _send_via_smtp(to=to, subject=subject, html_body=html_body, text_body=plain)


def _send_via_smtp(
    *, to: str, subject: str, html_body: str, text_body: str
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = to
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.send_message(message)

    logger.info("Sent SMTP email to %s: %s", to, subject)


def _send_via_resend(
    *, to: str, subject: str, html_body: str, text_body: str
) -> None:
    if not settings.resend_api_key:
        raise EmailError("RESEND_API_KEY is required in production")

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        },
        timeout=30.0,
    )

    if response.status_code >= 400:
        logger.error("Resend API error %s: %s", response.status_code, response.text)
        raise EmailError(f"Failed to send email via Resend: {response.text}")

    logger.info("Sent Resend email to %s: %s", to, subject)


def _html_to_plain_text(html: str) -> str:
    text = html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("</p>", "\n\n").replace("</li>", "\n")
    for token in ("<p>", "</p>", "<ul>", "</ul>", "<ol>", "</ol>", "<li>", "<strong>", "</strong>"):
        text = text.replace(token, "")
    return _strip_tags(text)


def _strip_tags(html: str) -> str:
    result = []
    in_tag = False
    for char in html:
        if char == "<":
            in_tag = True
            continue
        if char == ">":
            in_tag = False
            continue
        if not in_tag:
            result.append(char)
    return "".join(result).strip()
