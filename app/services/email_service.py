import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from app.security_utils import escape_html, is_valid_email, sanitize_email_header

logger = logging.getLogger(__name__)


def _redact_email(email):
    if not email or "@" not in str(email):
        return "***"
    local, domain = str(email).split("@", 1)
    visible = local[:2] if len(local) > 2 else "*"
    return f"{visible}***@{domain}"


def _smtp_login_and_send(smtp_host, smtp_port, smtp_user, smtp_password, use_tls, use_ssl, mail_from, recipient, raw_message):
    context = ssl.create_default_context()

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(mail_from, [recipient], raw_message)
        return

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        if use_tls:
            server.starttls(context=context)
            server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(mail_from, [recipient], raw_message)


def _send_email(subject, body_text, body_html=None, to_email=None):
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        logger.info("Mail suppressed: %s", subject)
        return True

    if not current_app.config.get("MAIL_ENABLED"):
        logger.debug("Mail disabled; skipping: %s", subject)
        return False

    smtp_host = current_app.config["SMTP_HOST"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_user = current_app.config["SMTP_USER"]
    smtp_password = current_app.config["SMTP_PASSWORD"]
    mail_from = current_app.config["MAIL_FROM"]
    use_tls = current_app.config["SMTP_USE_TLS"]
    use_ssl = current_app.config.get("SMTP_USE_SSL", False)
    recipient = to_email or current_app.config["ADMIN_NOTIFY_EMAIL"]

    if to_email and not is_valid_email(to_email):
        logger.warning("Invalid recipient email rejected: %s", _redact_email(to_email))
        return False

    if not smtp_user or not smtp_password:
        logger.warning("SMTP credentials not configured; email not sent.")
        return False

    pwd_len = len(smtp_password)
    if pwd_len != 16:
        logger.error(
            "Gmail App Password should be exactly 16 characters (loaded %s). "
            'Use EMAIL_PASSWORD="xxxx xxxx xxxx xxxx" in .env or 16 chars without spaces.',
            pwd_len,
        )

    message = MIMEMultipart("alternative")
    message["Subject"] = sanitize_email_header(subject)
    message["From"] = mail_from
    message["To"] = recipient
    message.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        message.attach(MIMEText(body_html, "html", "utf-8"))
    raw_message = message.as_string()

    try:
        _smtp_login_and_send(
            smtp_host, smtp_port, smtp_user, smtp_password,
            use_tls, use_ssl, mail_from, recipient, raw_message,
        )
        logger.info("Email sent to %s: %s", _redact_email(recipient), sanitize_email_header(subject))
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail rejected login for %s (password length: %s). "
            "Create a NEW App Password at https://myaccount.google.com/apppasswords "
            "for the same account as EMAIL_USERNAME. Normal Gmail passwords will NOT work.",
            smtp_user,
            pwd_len,
        )
        return False
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", recipient, exc)
        return False


def notify_new_contact_message(message):
    clinic = current_app.config["CLINIC_NAME"]
    subject = sanitize_email_header(f"[{clinic}] New contact message")
    body_text = (
        f"A new contact message was received.\n\n"
        f"Name: {message.full_name}\n"
        f"Phone: {message.phone}\n"
        f"Email: {message.email}\n"
        f"Subject: {message.subject}\n\n"
        f"Message:\n{message.message}\n"
    )
    body_html = f"""
    <h2>New Contact Message</h2>
    <ul>
      <li><strong>Name:</strong> {escape_html(message.full_name)}</li>
      <li><strong>Phone:</strong> {escape_html(message.phone)}</li>
      <li><strong>Email:</strong> {escape_html(message.email)}</li>
      <li><strong>Subject:</strong> {escape_html(message.subject)}</li>
    </ul>
    <p><strong>Message:</strong></p>
    <p>{escape_html(message.message)}</p>
    """
    return _send_email(subject, body_text, body_html)
