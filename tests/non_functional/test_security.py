"""Transport security, response headers, access control, API error hygiene, server-side validation."""

import json

import pytest

HEADERS = [
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]
PATHS = ["/", "/rooms", "/booking"]


@pytest.mark.security
@pytest.mark.tc("TC-058")
def test_http_redirects_to_https(playwright, base_url):
    if not base_url.startswith("https://"):
        pytest.skip("Base URL is not HTTPS")
    ctx = playwright.request.new_context()  # raw HTTP client, no browser
    resp = ctx.get(base_url.replace("https://", "http://", 1), max_redirects=0)
    assert resp.status in (301, 302, 307, 308)
    assert resp.headers["location"].startswith("https://")
    ctx.dispose()


@pytest.mark.security
@pytest.mark.tc("TC-058")
def test_hsts_header_present(api):
    hsts = api.get("/").headers.get("strict-transport-security", "")
    assert "max-age" in hsts and int(hsts.split("max-age=")[1].split(";")[0]) >= 15552000, hsts


@pytest.mark.security
@pytest.mark.tc("TC-118", "TC-058")
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("header", HEADERS)
def test_security_headers_present(api, path, header):
    assert header in api.get(path).headers, f"{header} missing on {path}"


@pytest.mark.security
@pytest.mark.tc("TC-118")
def test_csp_blocks_framing(api):
    h = api.get("/").headers
    assert "frame-ancestors 'self'" in h.get("content-security-policy", "") or h.get("x-frame-options") in (
        "DENY",
        "SAMEORIGIN",
    )


@pytest.mark.security
@pytest.mark.tc("TC-058")
def test_no_mixed_content(page):
    insecure = []
    page.on("request", lambda r: insecure.append(r.url) if r.url.startswith("http://") else None)
    for path in ["/", "/rooms", "/gallery", "/contact"]:
        page.goto(path, wait_until="networkidle")
    assert not insecure, f"Mixed content: {insecure}"


@pytest.mark.security
@pytest.mark.tc("TC-058")
@pytest.mark.defect(reason="Server header 'Vercel' is fine; x-powered-by: Next.js discloses the framework")
def test_no_technology_disclosure_headers(api):
    assert "x-powered-by" not in api.get("/").headers


@pytest.mark.security
@pytest.mark.tc("TC-017")
@pytest.mark.parametrize("path", ["/staff", "/staff/dashboard", "/admin"])
def test_staff_console_not_reachable_anonymously(api, path):
    resp = api.get(path, max_redirects=0)
    assert resp.status in (301, 302, 307, 308, 401, 403, 404)
    assert "dashboard" not in resp.text().lower() or resp.status >= 400


@pytest.mark.security
@pytest.mark.tc("TC-017", "TC-107")
def test_auth_me_without_session(api):
    body = api.get("/api/auth/me").json()
    assert body.get("data") is None


@pytest.mark.security
@pytest.mark.api
@pytest.mark.tc("TC-119")
def test_unknown_api_route_returns_json_404(api):
    resp = api.get("/api/unknown-route-qa")
    assert resp.status == 404
    assert "application/json" in resp.headers.get("content-type", "")


QUOTE_CASES = {
    "past-dates": {"checkIn": "2020-01-01", "checkOut": "2020-01-03", "adults": 1},
    "inverted": {"checkIn": "2027-01-10", "checkOut": "2027-01-05", "adults": 1},
    "over-90-nights": {"checkIn": "2027-01-01", "checkOut": "2027-06-01", "adults": 1},
    "over-capacity": {"checkIn": "2027-01-10", "checkOut": "2027-01-12", "adults": 9},
    "negative-children": {"checkIn": "2027-01-10", "checkOut": "2027-01-12", "adults": 1, "children": -1},
    "bad-room-id": {"roomId": "not-a-uuid", "checkIn": "2027-01-10", "checkOut": "2027-01-12", "adults": 1},
}


@pytest.mark.security
@pytest.mark.api
@pytest.mark.tc("TC-098")
@pytest.mark.parametrize("case", QUOTE_CASES.values(), ids=QUOTE_CASES.keys())
def test_server_rejects_invalid_quotes(api, site, case):
    payload = {"roomId": site.bookable_room["id"], **case}
    resp = api.post("/api/booking/quote", data=payload)
    assert resp.status >= 400, f"{payload} accepted with {resp.status}"


@pytest.mark.security
@pytest.mark.api
@pytest.mark.tc("TC-119", "TC-098")
@pytest.mark.defect("BUG-042")
@pytest.mark.parametrize("case", ["past-dates", "bad-room-id"])
def test_quote_validation_errors_are_4xx_and_generic(api, site, case):
    resp = api.post("/api/booking/quote", data={"roomId": site.bookable_room["id"], **QUOTE_CASES[case]})
    assert 400 <= resp.status < 500, f"validation error returned HTTP {resp.status}"
    text = resp.text()
    assert "Catalog request failed" not in text and "statusCode" not in text, text[:200]


@pytest.mark.security
@pytest.mark.api
@pytest.mark.tc("TC-077", "TC-121")
@pytest.mark.defect("BUG-046")
def test_public_api_exposes_no_test_contacts(api):
    text = json.dumps(api.get("/api/customization").json()) + json.dumps(api.get("/api/settings").json())
    assert "test@" not in text.lower() and "test-image" not in text.lower(), "test data in public API"
