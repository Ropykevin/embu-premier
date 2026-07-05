"""Send a test email using settings from .env"""
from app import create_app
from app.services.email_service import _send_email

app = create_app()

with app.app_context():
    cfg = app.config
    print("Email configuration:")
    print(f"  MAIL_ENABLED: {cfg['MAIL_ENABLED']}")
    print(f"  SMTP_HOST:    {cfg['SMTP_HOST']}")
    print(f"  SMTP_PORT:    {cfg['SMTP_PORT']}")
    print(f"  SMTP_USER:    {cfg['SMTP_USER']}")
    print(f"  MAIL_FROM:    {cfg['MAIL_FROM']}")
    print(f"  NOTIFY_TO:    {cfg['ADMIN_NOTIFY_EMAIL']}")
    print()

    if not cfg["MAIL_ENABLED"]:
        print("FAIL: Email is disabled. Set EMAIL_USERNAME and EMAIL_PASSWORD in .env")
        raise SystemExit(1)

    ok = _send_email(
        subject="[Embu Premier Clinic] Test email",
        body_text=(
            "This is a test email from Embu Premier Physicians Clinic.\n\n"
            "If you received this, SMTP is configured correctly."
        ),
        body_html=(
            "<h2>Test Email</h2>"
            "<p>This is a test email from <strong>Embu Premier Physicians Clinic</strong>.</p>"
            "<p>If you received this, SMTP is configured correctly.</p>"
        ),
    )

    if ok:
        print(f"SUCCESS: Test email sent to {cfg['ADMIN_NOTIFY_EMAIL']}")
    else:
        print("FAIL: Email could not be sent. Check terminal logs above for details.")
        raise SystemExit(1)
