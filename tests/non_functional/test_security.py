import pytest

RECOMMENDED = ["x-content-type-options", "referrer-policy", "x-frame-options", "content-security-policy"]


@pytest.mark.security
def test_http_redirects_to_https(playwright, base_url):
    if not base_url.startswith("https://"):
        pytest.skip("Base URL is not HTTPS")
    ctx = playwright.request.new_context()  # raw HTTP client, no browser
    resp = ctx.get(base_url.replace("https://", "http://", 1), max_redirects=0)
    assert resp.status in (301, 302, 307, 308)
    assert resp.headers["location"].startswith("https://")
    ctx.dispose()


@pytest.mark.security
def test_hsts_header_present(page, base_url):
    resp = page.request.get(base_url)
    assert "max-age" in resp.headers.get("strict-transport-security", "")


@pytest.mark.security
@pytest.mark.parametrize("header", RECOMMENDED)
@pytest.mark.xfail(reason="Hardening header - advisory until the team decides to enforce", strict=False)
def test_recommended_security_headers(page, base_url, header):
    assert header in page.request.get(base_url).headers


@pytest.mark.security
def test_no_server_version_leak(page, base_url):
    server = page.request.get(base_url).headers.get("server", "")
    assert not any(ch.isdigit() for ch in server), f"Server header leaks version: {server}"
