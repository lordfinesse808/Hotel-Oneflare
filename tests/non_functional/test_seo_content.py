"""SEO files, Open Graph tags, copy/content review across pages."""

import re

import pytest

PAGES = ["/", "/rooms", "/branches", "/gallery", "/about", "/contact"]
COPY_PROBLEMS = re.compile(
    r"whatever amount|lorem ipsum|placeholder|TODO|Live changing|\bteh\b|all three houses|test@", re.I
)


@pytest.mark.seo
@pytest.mark.tc("TC-115")
@pytest.mark.parametrize("path,ctype", [("/robots.txt", "text/plain"), ("/sitemap.xml", "xml")])
def test_robots_and_sitemap(api, path, ctype):
    resp = api.get(path)
    assert resp.status == 200 and ctype in resp.headers.get("content-type", "")


@pytest.mark.seo
@pytest.mark.tc("TC-115")
def test_robots_points_to_sitemap_and_hides_private_paths(api):
    text = api.get("/robots.txt").text()
    assert "Sitemap:" in text and "Disallow: /account" in text and "Disallow: /api/" in text


@pytest.mark.seo
@pytest.mark.tc("TC-115")
def test_sitemap_lists_public_pages(api):
    xml = api.get("/sitemap.xml").text()
    for path in ("/rooms", "/branches"):
        assert f"{path}</loc>" in xml, f"{path} missing from sitemap"


@pytest.mark.seo
@pytest.mark.tc("TC-115")
@pytest.mark.parametrize("path", ["/", "/rooms", "/contact"])
def test_open_graph_tags(page, path):
    page.goto(path)
    for prop in ("og:title", "og:description", "og:image"):
        content = page.locator(f'meta[property="{prop}"]').get_attribute("content")
        assert content, f"{prop} missing on {path}"


@pytest.mark.tc("TC-121")
@pytest.mark.parametrize("path", PAGES)
def test_no_placeholder_or_typo_copy(page, path):
    page.goto(path, wait_until="networkidle")
    found = COPY_PROBLEMS.findall(page.get_by_role("main").inner_text())
    assert not found, f"{path}: {found}"
