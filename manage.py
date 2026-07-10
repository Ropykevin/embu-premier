import os

import click

from app import create_app, db
from app.config import _env_first
from app.db_init import init_database

app = create_app()


@app.cli.command("check-config")
def check_config_command():
    """Show loaded email/SMS settings (no secrets printed)."""
    cfg = app.config
    print("=== Email ===")
    print(f"  MAIL_ENABLED:   {cfg['MAIL_ENABLED']}")
    print(f"  SMTP_HOST:      {cfg['SMTP_HOST']}:{cfg['SMTP_PORT']}")
    print(f"  SMTP_USER:      {cfg['SMTP_USER']}")
    pwd = cfg["SMTP_PASSWORD"]
    print(f"  Password chars: {len(pwd)} (must be 16 for Gmail)")
    if len(pwd) != 16:
        spaced = _env_first("EMAIL_PASSWORD", "SMTP_PASSWORD")
        if spaced and " " in spaced:
            parts = spaced.strip('"').strip("'").split()
            print(f"  Password groups: {parts} → lengths {[len(p) for p in parts]} (each should be 4)")
        print("  FIX: Regenerate at https://myaccount.google.com/apppasswords")
        print("       Paste as 16 chars with NO spaces, e.g. EMAIL_PASSWORD=abcdefghijklmnop")
    else:
        print("  Password length OK.")
    print(f"  NOTIFY_EMAIL:   {cfg['ADMIN_NOTIFY_EMAIL']}")
    print()
    print("=== SMS ===")
    print(f"  SMS_ENABLED:    {cfg['SMS_ENABLED']}")
    print(f"  AT_USERNAME:    {cfg['AT_USERNAME']}")
    print(f"  AT_SANDBOX:     {cfg.get('AT_SANDBOX', False)}")
    print(f"  AT_API_URL:     {cfg.get('AT_API_URL')}")
    print(f"  AT_SENDER_ID:   {cfg.get('AT_SENDER_ID') or '(none)'}")
    print(f"  API key chars:  {len(cfg.get('AT_API_KEY', ''))}")
    print(f"  NOTIFY_PHONE:   {cfg['ADMIN_NOTIFY_PHONE']}")
    print()
    if len(cfg["SMTP_PASSWORD"]) == 16:
        print("Email password length OK — if login still fails, regenerate App Password in Google.")
    else:
        print("FIX EMAIL: See group lengths above. Use a fresh 16-character App Password.")
    if cfg.get("AT_SANDBOX"):
        print("SMS sandbox mode — use sandbox API key from africastalking.com sandbox app.")
    else:
        print("SMS production mode — AT_USERNAME must match your Africa's Talking dashboard username exactly.")
    print()
    print("=== SEO ===")
    print(f"  SITE_URL:                 {cfg.get('SITE_URL') or '(not set — set DOMAIN in .env)'}")
    print(f"  GOOGLE_SITE_VERIFICATION: {'set' if cfg.get('GOOGLE_SITE_VERIFICATION') else 'not set'}")
    if cfg.get("SITE_URL"):
        print(f"  Sitemap:                  {cfg['SITE_URL']}/sitemap.xml")
        print(f"  Robots:                   {cfg['SITE_URL']}/robots.txt")


@app.cli.command("init-db")
def init_db_command():
    """Create tables and optionally seed a default admin user."""
    seed = os.environ.get("SEED_SAMPLE_DOCTORS", "0") == "1"
    init_database(seed_sample_doctors=seed)
    print("Database initialized.")


@app.cli.command("test-email")
def test_email_command():
    """Send a test email using .env SMTP settings."""
    from app.services.email_service import _send_email

    cfg = app.config
    print("Email configuration:")
    print(f"  MAIL_ENABLED: {cfg['MAIL_ENABLED']}")
    print(f"  SMTP_HOST:    {cfg['SMTP_HOST']}")
    print(f"  SMTP_USER:    {cfg['SMTP_USER']}")
    print(f"  NOTIFY_TO:    {cfg['ADMIN_NOTIFY_EMAIL']}")
    print(f"  Password len: {len(cfg['SMTP_PASSWORD'])} chars (Gmail app password = 16)")
    print()

    if not cfg["MAIL_ENABLED"]:
        print("FAIL: Email disabled. Set EMAIL_USERNAME and EMAIL_PASSWORD in .env")
        return

    ok = _send_email(
        subject="[Embu Premier Clinic] Test email",
        body_text="Test email — SMTP is working.",
        body_html="<p><strong>Test email</strong> — SMTP is working.</p>",
    )

    if ok:
        print(f"SUCCESS: Test email sent to {cfg['ADMIN_NOTIFY_EMAIL']}")
    else:
        print("FAIL: Could not send email. See error log above.")


@app.cli.command("test-sms")
@click.argument("phone", required=False)
def test_sms_command(phone):
    """Send a test SMS. Optional: flask test-sms +254742670714"""
    import logging

    from app.services.sms_service import normalize_phone, send_sms

    cfg = app.config
    phone = phone or cfg["ADMIN_NOTIFY_PHONE"]
    normalized = normalize_phone(phone)

    print("SMS configuration:")
    print(f"  SMS_ENABLED:  {cfg['SMS_ENABLED']}")
    print(f"  AT_USERNAME:  {cfg['AT_USERNAME']}")
    print(f"  AT_SANDBOX:   {cfg.get('AT_SANDBOX', False)}")
    print(f"  AT_API_URL:   {cfg.get('AT_API_URL')}")
    print(f"  AT_SENDER_ID: {cfg.get('AT_SENDER_ID') or '(none — using AT default shortcode)'}")
    print(f"  API key len:  {len(cfg.get('AT_API_KEY', ''))}")
    print(f"  NOTIFY_PHONE: {phone}")
    if normalized != phone:
        print(f"  Normalized:   {normalized}")
    print()

    if not cfg["SMS_ENABLED"]:
        print("FAIL: SMS disabled. Set AT_USERNAME and AT_API_KEY in .env")
        return

    if cfg.get("AT_SANDBOX"):
        print("Sandbox mode — only numbers added in your AT sandbox app receive SMS.")
        print("Add your phone at https://account.africastalking.com/apps/sandbox")
        print()

    with app.app_context():
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        sms_logger = logging.getLogger("app.services.sms_service")
        sms_logger.addHandler(handler)
        sms_logger.setLevel(logging.INFO)

        ok = send_sms(
            phone,
            "Test SMS from Embu Premier Physicians Clinic. SMS is working.",
        )
        sms_logger.removeHandler(handler)

    if ok:
        print(f"SUCCESS: Test SMS accepted by Africa's Talking for {normalized or phone}")
        print("Check the phone in 1–2 minutes. If not received, check AT dashboard Message Logs.")
    else:
        print("FAIL: SMS not sent.")
        print("Common fixes:")
        print("  406 blacklist  → remove number in AT dashboard SMS blacklist")
        print("  402 sender ID  → keep AT_FROM empty until EmbuPremier is approved")
        print("  405 balance    → top up Africa's Talking account")
        print("  401 auth       → check AT_USERNAME=embupremier and production API key")
