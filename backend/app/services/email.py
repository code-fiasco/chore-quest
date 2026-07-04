import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

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
    """Send an email via authenticated SMTP (STARTTLS by default)."""
    plain = text_body or _html_to_plain_text(html_body)
    _send_via_smtp(to=to, subject=subject, html_body=html_body, text_body=plain)


def _send_via_smtp(
    *, to: str, subject: str, html_body: str, text_body: str
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.email_from_name, settings.email_from))
    message["To"] = to
    message["Reply-To"] = settings.reply_to
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            smtp.ehlo()
            if settings.smtp_use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        logger.exception("SMTP error sending email to %s", to)
        raise EmailError(f"Failed to send email: {exc}") from exc

    logger.info("Sent SMTP email to %s: %s", to, subject)


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
