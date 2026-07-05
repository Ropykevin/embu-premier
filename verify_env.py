"""Verify .env against production security requirements."""
import os

from dotenv import load_dotenv

load_dotenv()

WEAK_SECRET = {"dev-only-change-me", "change-me", "change-me-to-a-long-random-string"}
WEAK_ADMIN = {"admin123", "password", "admin", "change-me-admin-password"}
WEAK_DB = {"postgres", "1234", "password", "change-me-strong-db-password"}


def check(label, value, min_len=None, weak=None):
    if not value:
        return False, f"{label}: missing"
    issues = []
    if min_len and len(value) < min_len:
        issues.append(f"length {len(value)} (need {min_len}+)")
    if weak and value in weak:
        issues.append("known weak default")
    if issues:
        return False, f"{label}: {', '.join(issues)}"
    return True, f"{label}: OK ({len(value)} chars)"


def main():
    email_pwd = os.getenv("EMAIL_PASSWORD", "").replace(" ", "").strip('"').strip("'")

    print("=== Production .env verification ===\n")

    checks = [
        check("SECRET_KEY", os.getenv("SECRET_KEY"), 32, WEAK_SECRET),
        check("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD"), 12, WEAK_ADMIN),
        check("POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD"), 12, WEAK_DB),
        check("EMAIL_PASSWORD", email_pwd, 16),
    ]

    for ok, msg in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")

    print("\n=== Configuration ===\n")
    print(f"  PRODUCTION in .env: {os.getenv('PRODUCTION') or '(not set — docker-compose.prod sets true)'}")
    print(f"  SESSION_COOKIE_SECURE: {os.getenv('SESSION_COOKIE_SECURE') or '(auto true when PRODUCTION=true)'}")
    print(f"  FLASK_DEBUG: {os.getenv('FLASK_DEBUG', 'not set')}")
    print(f"  AT_SANDBOX: {os.getenv('AT_SANDBOX', 'not set')}")
    print(f"  AT_USERNAME: {os.getenv('AT_USERNAME', 'not set')}")
    print(f"  AT_API_KEY: {len(os.getenv('AT_API_KEY', ''))} chars")
    print(f"  AT_FROM: {os.getenv('AT_FROM', 'not set')}")
    print(f"  SEED_SAMPLE_DOCTORS: {os.getenv('SEED_SAMPLE_DOCTORS', 'not set')}")
    print(f"  DOMAIN: {os.getenv('DOMAIN') or 'NOT SET (required for SSL)'}")
    db_url = os.getenv("DATABASE_URL")
    print(f"  DATABASE_URL: {'set' if db_url else 'not set (OK for Docker prod)'}")

    sk = os.getenv("SECRET_KEY", "")
    ap = os.getenv("ADMIN_PASSWORD", "")
    pp = os.getenv("POSTGRES_PASSWORD", "")
    if sk and sk == ap == pp:
        print("\n  [WARN] SECRET_KEY, ADMIN_PASSWORD, and POSTGRES_PASSWORD are identical — use unique values.")

    if os.getenv("SEED_SAMPLE_DOCTORS") == "1":
        print("  [WARN] SEED_SAMPLE_DOCTORS=1 — docker-compose.prod overrides to 0, but set 0 in .env for clarity.")

    commented_secrets = "Kevin254!" in open(".env", encoding="utf-8").read()
    if commented_secrets:
        print("  [WARN] Old password found in .env comments — remove commented credentials.")

    print("\n=== Simulated production startup ===\n")
    os.environ["PRODUCTION"] = "true"
    os.environ["SESSION_COOKIE_SECURE"] = "true"
    try:
        from app import create_app

        create_app()
        print("  [PASS] App would start in production mode.")
    except Exception as exc:
        print(f"  [FAIL] App would NOT start: {exc}")

    failed = sum(1 for ok, _ in checks if not ok)
    print(f"\n=== Result: {failed} blocking issue(s) ===")


if __name__ == "__main__":
    main()
