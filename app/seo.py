"""SEO helpers: site URL, canonical links, sitemap, robots.txt."""

from xml.etree.ElementTree import Element, SubElement, tostring

from flask import current_app, request, url_for


def build_site_url(domain=None, https_enabled=None, web_port=None):
    """Build public site base URL from env (no trailing slash)."""
    domain = (domain if domain is not None else current_app.config.get("DOMAIN", "")).strip()
    if not domain:
        return ""

    if https_enabled is None:
        https_enabled = current_app.config.get("HTTPS_ENABLED", False)
    if web_port is None:
        web_port = str(current_app.config.get("WEB_PORT", "8005"))

    scheme = "https" if https_enabled else "http"
    if scheme == "https" or web_port in ("80", "443"):
        return f"{scheme}://{domain}"
    return f"{scheme}://{domain}:{web_port}"


def canonical_url_for(path=None):
    """Absolute canonical URL for the current or given path."""
    site_url = current_app.config.get("SITE_URL") or build_site_url()
    if not site_url:
        return ""

    if path is None:
        path = request.path

    if path == "/":
        return f"{site_url}/"
    return f"{site_url}{path}"


def public_sitemap_paths():
    """Named public routes included in sitemap.xml (excluding dynamic doctor pages)."""
    return [
        "public.index",
        "public.about",
        "public.services",
        "public.specialists",
        "public.book_appointment",
        "public.contact",
    ]


def render_sitemap_xml():
    from app.models import Doctor

    site_url = current_app.config.get("SITE_URL") or build_site_url()
    if not site_url:
        site_url = request.url_root.rstrip("/")

    urlset = Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
    )

    def add_url(loc, changefreq="monthly", priority="0.8"):
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = loc
        SubElement(url_el, "changefreq").text = changefreq
        SubElement(url_el, "priority").text = priority

    for endpoint in public_sitemap_paths():
        path = url_for(endpoint)
        priority = "1.0" if endpoint == "public.index" else "0.8"
        changefreq = "weekly" if endpoint == "public.index" else "monthly"
        add_url(f"{site_url}{path}", changefreq=changefreq, priority=priority)

    for doctor in Doctor.query.order_by(Doctor.doctor_id).all():
        path = url_for("public.doctor_profile", doctor_id=doctor.doctor_id)
        add_url(f"{site_url}{path}", changefreq="monthly", priority="0.6")

    return tostring(urlset, encoding="unicode", xml_declaration=False)


def render_robots_txt():
    site_url = current_app.config.get("SITE_URL") or build_site_url()
    sitemap_line = ""
    if site_url:
        sitemap_line = f"\nSitemap: {site_url}/sitemap.xml"

    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        f"{sitemap_line}\n"
    ).lstrip()


def inject_seo_context():
    site_url = current_app.config.get("SITE_URL") or build_site_url()
    return {
        "site_url": site_url,
        "canonical_url": canonical_url_for(),
        "google_site_verification": current_app.config.get(
            "GOOGLE_SITE_VERIFICATION", ""
        ),
        "clinic_name": current_app.config.get(
            "CLINIC_NAME", "Embu Premier Physicians Clinic"
        ),
    }
