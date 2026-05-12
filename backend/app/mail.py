"""Outbound SMTP for admin replies.

Stdlib smtplib over STARTTLS (port 587) — the admin reply flow is
low-volume (~handfuls/day), so we don't need a queue or aiosmtplib.
The send is synchronous from the endpoint's POV; FastAPI runs the
handler in a threadpool so this doesn't block the event loop.
"""

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from app.config import settings

log = logging.getLogger(__name__)


class MailNotConfigured(RuntimeError):
    """Raised when smtp_pass is empty — endpoint should 503."""


class MailSendError(RuntimeError):
    """Raised when the SMTP transaction fails — endpoint should 502."""


def is_configured() -> bool:
    return bool(settings.smtp_user and settings.smtp_pass)


def send_email(*, to: str, subject: str, body: str) -> str:
    """Send a plain-text email. Returns the Message-ID header on success.

    Raises MailNotConfigured when SMTP credentials aren't set, and
    MailSendError on any SMTP-level failure. The caller is expected to
    record both outcomes in the bug_report_replies table for audit.
    """
    if not is_configured():
        raise MailNotConfigured(
            "SMTP not configured: set SMTP_USER and SMTP_PASS env vars."
        )

    from_email = settings.smtp_from_email or settings.smtp_user
    message_id = make_msgid(domain=from_email.split("@", 1)[-1] or "wowumbra.gg")

    msg = EmailMessage()
    msg["From"] = formataddr((settings.smtp_from_name, from_email))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(settings.smtp_user, settings.smtp_pass)
            s.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        log.exception("SMTP send to %s failed", to)
        raise MailSendError(str(e)) from e

    return message_id
