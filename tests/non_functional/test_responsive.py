import pytest
from playwright.sync_api import expect

VIEWPORTS = {
    "mobile": {"width": 375, "height": 812},
    "tablet": {"width": 768, "height": 1024},
    "desktop": {"width": 1440, "height": 900},
}
PAGES = ["/", "/rooms", "/gallery", "/about", "/contact"]


@pytest.mark.responsive
@pytest.mark.parametrize("vp", VIEWPORTS.values(), ids=VIEWPORTS.keys())
@pytest.mark.parametrize("path", PAGES)
def test_no_horizontal_scroll(page, vp, path):
    page.set_viewport_size(vp)
    page.goto(path, wait_until="load")
    overflow = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"{path} overflows horizontally by {overflow}px at {vp['width']}px"


@pytest.mark.responsive
@pytest.mark.parametrize("vp", VIEWPORTS.values(), ids=VIEWPORTS.keys())
def test_header_visible_on_all_viewports(page, vp):
    page.set_viewport_size(vp)
    page.goto("/")
    expect(page.get_by_role("banner")).to_be_visible()
