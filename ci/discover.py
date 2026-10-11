"""Site discovery: prints ARIA snapshots of key UI states so page-object selectors can be (re)derived
after UI changes. Run in CI (where the site is reachable):
    python ci/discover.py https://hotel-plaza-preview.vercel.app
"""

import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://hotel-plaza-preview.vercel.app").rstrip("/")
DIALOG = "[role=dialog]:visible"


def section(title):
    print(f"\n{'=' * 20} {title} {'=' * 20}", flush=True)


def snap(page, title, locator="main"):
    section(title)
    print("URL:", page.url)
    try:
        print(page.locator(locator).first.aria_snapshot(timeout=5000))
    except Exception as e:  # noqa: BLE001 - discovery must keep going
        print("SNAPSHOT FAILED:", str(e)[:200])


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print(f"!! {label} failed: {str(e)[:200]}")


def go(page, path, wait=1500):
    page.goto(BASE + path, wait_until="networkidle")
    page.wait_for_timeout(wait)


def sign_in_states(page):
    go(page, "/")
    page.get_by_role("banner").get_by_role("button", name="Sign in").click()
    dlg = page.get_by_role("dialog", name="Sign in or create an account")
    dlg.get_by_role("button", name="Customer").click()
    page.wait_for_timeout(300)
    snap(page, "SIGN IN customer selected", DIALOG)
    dlg.get_by_role("button", name="Next").click()
    page.wait_for_timeout(1000)
    snap(page, "SIGN IN form", DIALOG)
    section("SIGN IN inputs")
    for el in page.locator(f"{DIALOG} input, {DIALOG} button").all():
        safe(
            lambda el=el: print(el.evaluate('e => e.outerHTML.replace(/class="[^"]*"/, \'\').slice(0, 200)')),
            "h",
        )
    buttons = [b for b in dlg.get_by_role("button").all_inner_texts()]
    print("BUTTONS:", buttons)
    submit = dlg.locator("button[type=submit]")
    safe(lambda: submit.click(), "empty submit")
    page.wait_for_timeout(800)
    snap(page, "SIGN IN empty submit", DIALOG)
    safe(lambda: page.locator("input[name=identifier]").fill("abc"), "id")
    safe(lambda: page.locator("input[name=password]").fill("wrongpassword1"), "pw")
    reqs = []
    page.on("request", lambda r: reqs.append(f"{r.method} {r.url}") if "/api/auth" in r.url else None)
    safe(lambda: submit.click(), "abc submit")
    page.wait_for_timeout(2000)
    print("AUTH REQUESTS (identifier=abc):", reqs)
    snap(page, "SIGN IN identifier abc", DIALOG)
    safe(lambda: page.locator("input[name=identifier]").fill("nobody-qa-0001@maildrop.cc"), "id2")
    safe(lambda: submit.click(), "bad creds submit")
    page.wait_for_timeout(2500)
    snap(page, "SIGN IN bad creds", DIALOG)
    safe(lambda: dlg.get_by_role("button", name="Forgot password?").click(), "forgot")
    page.wait_for_timeout(800)
    snap(page, "FORGOT password", DIALOG)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    print(
        "focused after Esc:",
        page.evaluate("document.activeElement && document.activeElement.outerHTML.slice(0,120)"),
    )
    # role is remembered: reopen
    page.get_by_role("banner").get_by_role("button", name="Sign in").click()
    page.wait_for_timeout(800)
    snap(page, "SIGN IN reopened", DIALOG)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, timezone_id="Africa/Lagos")
        ctx.set_default_timeout(6000)
        page = ctx.new_page()
        safe(lambda: sign_in_states(page), "sign in states")

        go(page, "/gallery")
        safe(lambda: page.get_by_role("main").get_by_role("img", name="Suite bathroom").click(), "img click")
        page.wait_for_timeout(1000)
        snap(page, "GALLERY after img click", "body")

        # review step edit links, branch room
        go(
            page,
            "/rooms?branchId=a877424b-2eac-4320-87f9-e6114b8a5fa6&adults=1&checkIn=2026-12-01&checkOut=2026-12-03",
        )
        page.get_by_role("link", name="Select room").first.click()
        page.wait_for_timeout(2500)
        print("URL after Select room:", page.url)
        page.get_by_role("button", name="Continue to guest details").click()
        page.wait_for_timeout(2000)
        page.get_by_role("textbox", name="John Doe").fill("QA Tester")
        page.get_by_role("textbox", name="alex.morgan@example.com").fill("qa@maildrop.cc")
        page.get_by_role("textbox", name="+234 800 000 0000").fill("+2348012345678")
        page.get_by_role("checkbox").check()
        page.get_by_role("button", name="Review my booking").click()
        page.wait_for_timeout(2500)
        snap(page, "REVIEW branch room")
        page.get_by_role("button", name="Back to guest details").click()
        page.wait_for_timeout(1000)
        print(
            "after Back values:",
            [i.input_value() for i in page.locator("main input:not([type=checkbox])").all()],
            page.get_by_role("checkbox").is_checked(),
        )
        page.get_by_role("checkbox").check()
        page.get_by_role("button", name="Review my booking").click()
        page.wait_for_timeout(2000)
        safe(lambda: page.get_by_role("button", name="Change room or dates").click(), "change")
        page.wait_for_timeout(2000)
        print("URL after Change room or dates:", page.url)
        page.go_back()
        page.wait_for_timeout(1500)
        print("URL after browser back:", page.url)

        # 5-night quote and 90+ night limits on the room detail
        go(page, "/rooms/965c310d-7b91-46b3-b2aa-3053c19ec203?checkIn=2026-12-01&checkOut=2026-12-06")
        safe(
            lambda: print(
                "5 nights:",
                page.get_by_role("main")
                .get_by_text("Total")
                .first.evaluate("e => e.parentElement.parentElement.innerText"),
            ),
            "5n",
        )
        safe(
            lambda: print("checkout max:", page.locator("main input[type=date]").nth(1).get_attribute("max")),
            "max",
        )
        go(page, "/rooms/965c310d-7b91-46b3-b2aa-3053c19ec203?checkIn=2020-01-01&checkOut=2020-01-03")
        safe(
            lambda: print(
                "past dates values:", [i.input_value() for i in page.locator("main input[type=date]").all()]
            ),
            "past",
        )
        safe(lambda: page.get_by_role("button", name="Continue to guest details").click(), "continue past")
        page.wait_for_timeout(1500)
        print("URL after continue with past dates:", page.url)
        snap(page, "DETAIL past dates")
        browser.close()


if __name__ == "__main__":
    main()
