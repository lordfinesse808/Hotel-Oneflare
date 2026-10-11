"""Responsive layout and device compatibility (mobile / tablet / large desktop, emulated phones)."""

import pytest
from playwright.sync_api import expect

VIEWPORTS = {
    "mobile": {"width": 375, "height": 812},
    "tablet": {"width": 768, "height": 1024},
    "desktop": {"width": 1440, "height": 900},
    "large": {"width": 1920, "height": 1080},
}
PAGES = ["/", "/rooms", "/branches", "/gallery", "/about", "/contact"]
TC_BY_VIEWPORT = {"mobile": "TC-046", "tablet": "TC-047", "desktop": "TC-048", "large": "TC-048"}


@pytest.mark.responsive
@pytest.mark.tc("TC-046", "TC-047", "TC-048", "TC-116")
@pytest.mark.parametrize("vp", VIEWPORTS.values(), ids=VIEWPORTS.keys())
@pytest.mark.parametrize("path", PAGES)
def test_no_horizontal_scroll(page, vp, path):
    page.set_viewport_size(vp)
    page.goto(path, wait_until="load")
    overflow = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"{path} overflows horizontally by {overflow}px at {vp['width']}px"


@pytest.mark.responsive
@pytest.mark.tc("TC-046", "TC-047", "TC-048")
@pytest.mark.parametrize("vp", VIEWPORTS.values(), ids=VIEWPORTS.keys())
def test_header_visible_on_all_viewports(page, vp):
    page.set_viewport_size(vp)
    page.goto("/")
    expect(page.get_by_role("banner")).to_be_visible()


@pytest.mark.responsive
@pytest.mark.tc("TC-116", "TC-046")
def test_branches_cards_not_clipped_at_375(mobile_page, site):
    mobile_page.goto("/branches", wait_until="networkidle")
    clipped = mobile_page.evaluate("""() => [...document.querySelectorAll('main h2, main a')]
      .filter(e => e.offsetParent !== null)
      .filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > innerWidth + 1)
      .map(e => e.innerText.slice(0, 40))""")
    assert not clipped, f"Clipped at 375px: {clipped}"


@pytest.mark.responsive
@pytest.mark.tc("TC-048")
def test_content_centred_with_readable_width_at_1920(page):
    page.set_viewport_size(VIEWPORTS["large"])
    page.goto("/rooms", wait_until="networkidle")
    box = page.get_by_role("main").locator("h1").bounding_box()
    assert box["x"] > 100, "content hugs the left edge at 1920px (not centred)"
    assert box["width"] < 1700


@pytest.mark.responsive
@pytest.mark.tc("TC-050", "TC-049")
@pytest.mark.parametrize("device", ["Pixel 7", "iPhone 13"])
def test_core_flow_on_emulated_phones(playwright, browser, browser_name, base_url, site, device):
    """Search -> filter -> open room with touch emulation (real devices remain a manual activity)."""
    profile = dict(playwright.devices[device])
    if browser_name == "firefox":
        profile.pop("is_mobile", None)  # Firefox does not support isMobile
    profile.pop("default_browser_type", None)
    ctx = browser.new_context(**profile, base_url=base_url, timezone_id="Africa/Lagos")
    page = ctx.new_page()
    try:
        page.goto(f"/rooms?branchId={site.default_branch.id}&adults=1")
        page.get_by_role("main").get_by_role("button", name="Filter", exact=True).tap()
        drawer = page.get_by_role("dialog", name="Filters")
        expect(drawer).to_be_visible()
        drawer.get_by_role("button", name="Close filters").tap()
        page.get_by_role("link", name="Select room").first.tap()
        expect(page.get_by_role("button", name="Continue to guest details")).to_be_visible(timeout=15000)
    finally:
        ctx.close()
