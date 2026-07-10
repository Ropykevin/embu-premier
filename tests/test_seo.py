def test_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    body = response.get_data(as_text=True)
    assert "User-agent: *" in body
    assert "Disallow: /admin/" in body
    assert "Sitemap: https://embupremierphysicians.co.ke/sitemap.xml" in body


def test_sitemap_xml(client, sample_doctor):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "application/xml" in response.mimetype
    body = response.get_data(as_text=True)
    assert "<?xml" in body
    assert "https://embupremierphysicians.co.ke/" in body
    assert "https://embupremierphysicians.co.ke/about" in body
    assert "https://embupremierphysicians.co.ke/book-appointment" in body
    assert f"https://embupremierphysicians.co.ke/doctor/{sample_doctor.doctor_id}" in body


def test_homepage_has_seo_tags(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'rel="canonical"' in body
    assert "https://embupremierphysicians.co.ke/" in body
    assert 'name="google-site-verification"' in body
    assert "test-verification-code" in body
    assert 'property="og:title"' in body


def test_admin_login_is_noindex(client):
    response = client.get("/admin/login")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'content="noindex, nofollow"' in body
