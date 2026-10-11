"""Accessibility: axe-core scan, keyboard operation, focus visibility, labels, landmarks/headings."""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import expect

PAGES = ["/", "/rooms", "/branches", "/gallery", "/about", "/contact", "/manage-booking"]
# Known axe findings on the live site (open defects): tracked as xfail so new violations still fail.
AXE_DEFECTS = {
    "/": pytest.mark.defect(reason="axe serious: color-contrast below WCAG AA on Home"),
    "/gallery": pytest.mark.defect(
        "BUG-045", reason="axe critical: location <select> has no accessible name"
    ),
}
AXE_PAGES = [pytest.param(p, marks=AXE_DEFECTS[p]) if p in AXE_DEFECTS else p for p in PAGES]
BLOCKING = {"critical", "serious"}  # gate: these impacts fail the build


@pytest.mark.a11y
@pytest.mark.tc("TC-056")
@pytest.mark.parametrize("path", AXE_PAGES)
def test_no_critical_or_serious_axe_violations(page, path):
    page.goto(path, wait_until="networkidle")
    result = Axe().run(page)  # injects axe-core and scans the whole document
    blocking = [v for v in result.response["violations"] if v["impact"] in BLOCKING]
    summary = "\n".join(
        f"- [{v['impact']}] {v['id']}: {v['help']} ({len(v['nodes'])} nodes)" for v in blocking
    )
    assert not blocking, f"{path} has blocking a11y violations:\n{summary}"


@pytest.mark.a11y
@pytest.mark.tc("TC-056")
@pytest.mark.parametrize("path", ["/", "/rooms", "/contact"])
def test_every_form_control_has_an_accessible_name(page, path):
    page.goto(path, wait_until="networkidle")
    unnamed = page.evaluate("""() => [...document.querySelectorAll('main input, main select, main textarea, header input')]
      .filter(e => e.type !== 'hidden' && e.offsetParent !== null)
      .filter(e => !(e.labels && e.labels.length) && !e.getAttribute('aria-label')
                   && !e.getAttribute('aria-labelledby') && !e.getAttribute('placeholder') && !e.title)
      .map(e => e.outerHTML.slice(0, 120))""")
    assert not unnamed, f"Unlabelled controls on {path}: {unnamed}"


@pytest.mark.a11y
@pytest.mark.tc("TC-056")
@pytest.mark.defect("BUG-045")
def test_room_detail_date_inputs_are_labelled(page, site):
    page.goto(f"/rooms/{site.bookable_room['id']}", wait_until="networkidle")
    for el in page.locator("main input[type=date]").all():
        name = el.evaluate(
            "e => (e.labels && e.labels[0] && e.labels[0].innerText) || e.getAttribute('aria-label')"
        )
        assert name, "date input without an accessible name"


@pytest.mark.a11y
@pytest.mark.tc("TC-055", "TC-100")
def test_sign_in_dialog_is_keyboard_operable(page):
    page.goto("/")
    page.get_by_role("banner").get_by_role("button", name="Sign in").focus()
    page.keyboard.press("Enter")  # keyboard-only activation
    dialog = page.get_by_role("dialog", name="Sign in or create an account")
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")  # dialogs should close with Esc
    expect(dialog).to_be_hidden()


@pytest.mark.a11y
@pytest.mark.tc("TC-055")
def test_keyboard_reaches_search_filters_and_select_room(page, site):
    page.goto(f"/rooms?branchId={site.default_branch.id}&adults=1", wait_until="networkidle")
    reached = set()
    for _ in range(80):
        page.keyboard.press("Tab")
        info = page.evaluate(
            "() => { const e = document.activeElement; "
            "return (e.getAttribute('aria-label') || e.innerText || e.name || e.type || '').trim(); }"
        )
        reached.add(info)
        if "Select room" in reached:
            break
    for needed in ("Check availability", "Select room"):
        assert needed in reached, f"'{needed}' not reachable by Tab; reached {sorted(reached)[:30]}"


@pytest.mark.a11y
@pytest.mark.tc("TC-055")
@pytest.mark.defect("BUG-045")
def test_focus_is_visible_on_search_controls(page):
    page.goto("/rooms", wait_until="networkidle")
    for loc in (page.get_by_role("combobox", name="Branch"), page.get_by_role("textbox", name="Check in")):
        loc.focus()
        style = loc.evaluate("""e => { const s = getComputedStyle(e);
            return {outline: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0, shadow: s.boxShadow !== 'none'}; }""")
        assert style["outline"] or style["shadow"], f"no visible focus indicator on {loc}"


@pytest.mark.a11y
@pytest.mark.tc("TC-123")
@pytest.mark.parametrize("path", PAGES)
def test_one_meaningful_h1_and_landmarks(page, path):
    page.goto(path, wait_until="networkidle")
    h1s = page.locator("h1").all_inner_texts()
    assert len(h1s) == 1 and h1s[0].strip(), f"{path}: h1s = {h1s}"
    for role in ("banner", "main", "contentinfo"):
        expect(page.get_by_role(role).first).to_be_attached()
    expect(page.get_by_role("banner").get_by_role("navigation")).to_be_attached()


@pytest.mark.a11y
@pytest.mark.tc("TC-117")
@pytest.mark.defect("BUG-039")
def test_touch_targets_at_least_44px_on_mobile(mobile_page):
    mobile_page.goto("/rooms", wait_until="networkidle")
    small = mobile_page.evaluate("""() => [...document.querySelectorAll('a, button')]
      .filter(e => e.offsetParent !== null)
      .map(e => ({t: (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 30),
                  h: e.getBoundingClientRect().height}))
      .filter(x => x.h > 0 && x.h < 44)""")
    assert not small, f"{len(small)} targets under 44px, e.g. {small[:8]}"
