import pytest
from axe_playwright_python.sync_playwright import Axe

PAGES = ["/", "/rooms", "/gallery", "/about", "/contact"]
BLOCKING = {"critical", "serious"}  # gate: these impacts fail the build


@pytest.mark.a11y
@pytest.mark.parametrize("path", PAGES)
def test_no_critical_or_serious_axe_violations(page, path):
    page.goto(path, wait_until="networkidle")
    result = Axe().run(page)  # injects axe-core and scans the whole document
    blocking = [v for v in result.response["violations"] if v["impact"] in BLOCKING]
    summary = "\n".join(f"- [{v['impact']}] {v['id']}: {v['help']} ({len(v['nodes'])} nodes)" for v in blocking)
    assert not blocking, f"{path} has blocking a11y violations:\n{summary}"


@pytest.mark.a11y
def test_registration_dialog_is_keyboard_reachable(page):
    page.goto("/")
    page.get_by_role("button", name="Sign in").focus()
    page.keyboard.press("Enter")  # keyboard-only activation
    assert page.get_by_role("dialog").is_visible()
    page.keyboard.press("Escape")  # dialogs should close with Esc
    page.get_by_role("dialog").wait_for(state="hidden")
