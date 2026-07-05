import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

logger = logging.getLogger(__name__)


def normalize_phone(phone):
    """Normalize Kenyan/international numbers to +254... format."""
    if not phone:
        return None

    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if cleaned.startswith("+"):
        return cleaned
    if cleaned.startswith("0"):
        return "+254" + cleaned[1:]
    if cleaned.startswith("254"):
        return "+" + cleaned
    if len(cleaned) == 9:
        return "+254" + cleaned
    return "+" + cleaned if not cleaned.startswith("+") else cleaned


def _send_via_africas_talking(phone, message):
    username = current_app.config["AT_USERNAME"]
    api_key = current_app.config["AT_API_KEY"]
    sender_id = current_app.config.get("AT_SENDER_ID") or None

    if not username or not api_key:
        logger.warning("Africa's Talking credentials not configured.")
        return False

    payload = {
        "username": username,
        "to": phone,
        "message": message,
    }
    # Custom sender IDs require AT approval; skip in sandbox mode
    if sender_id and not current_app.config.get("AT_SANDBOX"):
        payload["from"] = sender_id

    data = urllib.parse.urlencode(payload).encode("utf-8")
    api_url = current_app.config.get(
        "AT_API_URL", "https://api.africastalking.com/version1/messaging"
    )
    request = urllib.request.Request(
        api_url,
        data=data,
        method="POST",
        headers={
            "apiKey": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            logger.info("Africa's Talking SMS sent successfully to ****%s", phone[-4:])
            return True
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        logger.error(
            "Africa's Talking HTTP error %s (user=%s): %s",
            exc.code,
            username,
            error_body,
        )
        if exc.code == 401:
            logger.error(
                "Check AT_API_KEY matches AT_USERNAME. "
                "For sandbox testing set AT_SANDBOX=true in .env"
            )
        return False
    except Exception:
        logger.exception("Africa's Talking SMS failed for %s", phone)
        return False


def _send_via_twilio(phone, message):
    account_sid = current_app.config["TWILIO_ACCOUNT_SID"]
    auth_token = current_app.config["TWILIO_AUTH_TOKEN"]
    from_number = current_app.config["TWILIO_FROM_NUMBER"]

    if not all([account_sid, auth_token, from_number]):
        logger.warning("Twilio credentials not configured.")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = urllib.parse.urlencode(
        {"To": phone, "From": from_number, "Body": message}
    ).encode("utf-8")

    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, account_sid, auth_token)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(handler)

    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with opener.open(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            logger.info("Twilio SMS sent successfully")
            return True
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        logger.error("Twilio HTTP error %s: %s", exc.code, error_body)
        return False
    except Exception:
        logger.exception("Twilio SMS failed for %s", phone)
        return False


def send_sms(phone, message):
    if current_app.config.get("SMS_SUPPRESS_SEND"):
        logger.info("SMS suppressed to %s: %s", phone, message[:60])
        return True

    if not current_app.config.get("SMS_ENABLED"):
        logger.debug("SMS disabled; skipping message to %s", phone)
        return False

    normalized = normalize_phone(phone)
    if not normalized:
        logger.warning("Invalid phone number: %s", phone)
        return False

    provider = current_app.config.get("SMS_PROVIDER", "africastalking").lower()
    if provider == "twilio":
        return _send_via_twilio(normalized, message)
    return _send_via_africas_talking(normalized, message)
