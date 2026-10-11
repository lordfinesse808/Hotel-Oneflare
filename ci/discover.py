"""Site discovery: prints ARIA snapshots, links, headers and API calls for key pages/states.
Run in CI (where the site is reachable) to (re)derive selectors after UI changes:
    python ci/discover.py https://hotel-plaza-preview.vercel.app
"""

import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://hotel-plaza-preview.vercel.app").rstrip("/")
BENIN = "a877424b-2eac-4320-87f9-e6114b8a5fa6"
LAGOS = "411e63b9-cea4-4001-95fe-804f990bffb7"
LEKKI = "6c316c2a-7dbe-4ebe-a385-8c10a8193e50"


def section(title):
    print(f"\n{'=' * 20} {title} {'=' * 20}", flush=True)


def snap(page, title, locator="main"):
    section(title)
    print("URL:", page.url)
    try:
        loc = page.locator(locator) if isinstance(locator, str) else locator
        print(loc.first.aria_snapshot(timeout=8000))
    except Exception as e:  # noqa: BLE001 - discovery must keep going
        print("SNAPSHOT FAILED:", str(e)[:300])


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print(f"!! {label} failed: {str(e)[:300]}")


def go(page, path, wait=1500):
    page.goto(BASE + path, wait_until="networkidle")
    page.wait_for_timeout(wait)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, timezone_id="Africa/Lagos")
        ctx.set_default_timeout(8000)
        page = ctx.new_page()
        console = []
        page.on("console", lambda m: console.append(m.text) if m.type == "error" else None)

        # rooms list with 1 adult so cards render
        go(page, f"/rooms?branchId={BENIN}&adults=1")
        snap(page, "ROOMS benin adults=1")
        section("ROOMS inputs benin")
        for el in page.locator("main input, main select").all():
            safe(lambda el=el: print(el.evaluate('e => e.outerHTML.replace(/class="[^"]*"/, \'\')')), "html")
        section("ROOMS card html")
        safe(
            lambda: print(page.locator("main article, main li").first.evaluate("e => e.outerHTML")[:3000]),
            "card",
        )
        safe(
            lambda: print(
                page.get_by_role("link", name="View details").first.evaluate(
                    "e => e.closest('div.rounded-card, article, li, div').parentElement.outerHTML"
                )[:4000]
            ),
            "card2",
        )

        go(page, f"/rooms?branchId={LAGOS}&adults=1")
        snap(page, "ROOMS lagos adults=1")
        go(page, "/rooms")
        safe(lambda: page.get_by_label("Guests").select_option("1"), "guests")
        safe(lambda: page.get_by_role("button", name="Check availability").click(), "check")
        page.wait_for_timeout(2500)
        print("URL after check availability:", page.url)
        safe(lambda: print(page.get_by_role("heading", level=1).inner_text()), "h1")

        # branch room detail
        go(page, f"/rooms/f7a8b3a8-4524-4bd9-91f7-e39794917c3f?branchId={BENIN}", 3000)
        snap(page, "DETAIL branch room")
        safe(lambda: page.get_by_role("button", name="Continue to guest details").click(), "continue")
        page.wait_for_timeout(3000)
        snap(page, "AFTER continue branch room")
        go(page, "/rooms/does-not-exist", 4000)
        snap(page, "DETAIL does-not-exist")

        # booking review edits
        go(page, "/rooms/965c310d-7b91-46b3-b2aa-3053c19ec203?checkIn=2026-12-01&checkOut=2026-12-03", 2500)
        snap(page, "DETAIL with query dates", page.locator("main input"))
        safe(lambda: print([i.input_value() for i in page.locator("main input[type=date]").all()]), "dates")
        page.locator("main input[type=date]").nth(1).fill("2026-11-28")
        page.wait_for_timeout(800)
        snap(page, "DETAIL inverted dates")
        go(page, "/rooms/965c310d-7b91-46b3-b2aa-3053c19ec203", 2500)
        page.get_by_role("button", name="Continue to guest details").click()
        page.wait_for_timeout(2500)
        page.get_by_role("textbox", name="John Doe").fill("<script>alert(1)</script>")
        page.get_by_role("textbox", name="alex.morgan@example.com").fill("ada@")
        page.get_by_role("textbox", name="+234 800 000 0000").fill("abc")
        page.get_by_role("button", name="Review my booking").click()
        page.wait_for_timeout(800)
        snap(page, "BOOKING invalid formats")
        page.get_by_role("textbox", name="John Doe").fill("QA Tester")
        page.get_by_role("textbox", name="alex.morgan@example.com").fill("qa@maildrop.cc")
        page.get_by_role("textbox", name="+234 800 000 0000").fill("+2348012345678")
        page.get_by_role("button", name="Review my booking").click()
        page.wait_for_timeout(800)
        snap(page, "BOOKING without consent")
        page.get_by_role("checkbox").check()
        page.get_by_role("button", name="Review my booking").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Edit details").click()
        page.wait_for_timeout(1000)
        safe(
            lambda: print(
                "after edit values:",
                page.get_by_role("textbox", name="John Doe").input_value(),
                page.get_by_role("checkbox").is_checked(),
            ),
            "values",
        )
        safe(lambda: page.get_by_role("button", name="Review my booking").click(), "review again")
        page.wait_for_timeout(1000)
        safe(lambda: page.get_by_role("button", name="Change room or dates").click(), "change")
        page.wait_for_timeout(2000)
        print("URL after change room:", page.url)
        go(page, "/booking", 2500)
        print("URL direct /booking:", page.url)

        # sign in dialog
        go(page, "/")
        page.get_by_role("banner").get_by_role("button", name="Sign in").click()
        page.wait_for_timeout(1200)
        dialogs = page.get_by_role("dialog")
        print("dialog count", dialogs.count())
        for i in range(dialogs.count()):
            safe(
                lambda i=i: print(
                    i,
                    dialogs.nth(i).is_visible(),
                    dialogs.nth(i).get_attribute("aria-label"),
                    dialogs.nth(i).get_attribute("aria-labelledby"),
                ),
                "dlg",
            )
        snap(page, "SIGN IN dialog", page.locator("[role=dialog]:visible, dialog[open]"))
        safe(
            lambda: (
                page.locator("[role=dialog]:visible, dialog[open]")
                .first.get_by_role("button", name="Continue")
                .click()
            ),
            "empty continue",
        )
        page.wait_for_timeout(800)
        snap(page, "SIGN IN empty submit", page.locator("[role=dialog]:visible, dialog[open]"))
        safe(lambda: page.locator("input[name=identifier]").fill("abc"), "id")
        safe(lambda: page.locator("input[name=password]").fill("wrongpass1"), "pw")
        safe(
            lambda: (
                page.locator("[role=dialog]:visible, dialog[open]")
                .first.get_by_role("button", name="Continue")
                .click()
            ),
            "bad login",
        )
        page.wait_for_timeout(2500)
        snap(page, "SIGN IN bad creds", page.locator("[role=dialog]:visible, dialog[open]"))
        safe(lambda: page.get_by_role("button", name="Forgot password?").click(), "forgot")
        page.wait_for_timeout(800)
        snap(page, "FORGOT password", page.locator("[role=dialog]:visible, dialog[open]"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        print("dialog visible after Esc:", page.locator("[role=dialog]:visible, dialog[open]").count())
        go(page, "/")
        page.get_by_role("banner").get_by_role("button", name="Sign in").click()
        page.wait_for_timeout(800)
        safe(lambda: page.get_by_role("button", name="Create an account").click(), "create")
        page.wait_for_timeout(800)
        snap(page, "CREATE ACCOUNT", page.locator("[role=dialog]:visible, dialog[open]"))
        section("CREATE inputs")
        for el in page.locator("[role=dialog]:visible input, dialog[open] input").all():
            safe(lambda el=el: print(el.evaluate('e => e.outerHTML.replace(/class="[^"]*"/, \'\')')), "html")
        safe(
            lambda: (
                page.locator("[role=dialog]:visible, dialog[open]")
                .first.get_by_role("button", name="Create account")
                .click()
            ),
            "empty create",
        )
        page.wait_for_timeout(800)
        snap(page, "CREATE empty submit", page.locator("[role=dialog]:visible, dialog[open]"))

        # other pages
        for path in ["/manage-booking", "/privacy-policy", "/terms", "/cancellation-policy", "/xyz-not-here"]:
            go(page, path)
            print("TITLE:", page.title())
            snap(page, f"PAGE {path}")
        go(page, f"/contact?branch={LEKKI}")
        snap(page, "CONTACT ?branch=lekki")
        safe(lambda: page.get_by_role("button", name="Send message").click(), "send empty")
        page.wait_for_timeout(800)
        snap(page, "CONTACT empty submit")
        go(page, "/")
        page.get_by_role("searchbox", name="Search rooms").fill("Deluxe")
        page.wait_for_timeout(1200)
        snap(page, "SEARCH typed Deluxe", "body")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        print("URL after search enter:", page.url)
        snap(page, "SEARCH after enter")

        go(page, "/gallery")
        safe(lambda: page.get_by_role("img", name="Suite bathroom").click(force=True), "img click")
        page.wait_for_timeout(1000)
        snap(page, "GALLERY lightbox", page.locator("[role=dialog]:visible, dialog[open]"))
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        snap(page, "GALLERY lightbox next", page.locator("[role=dialog]:visible, dialog[open]"))
        page.keyboard.press("Escape")
        go(page, "/gallery")
        safe(
            lambda: page.locator("main select").select_option(label="Oneflare Grand Plaza - Lekki Branch"),
            "loc",
        )
        page.wait_for_timeout(1000)
        snap(page, "GALLERY lekki")

        # head meta
        for path in ["/", "/rooms", "/contact"]:
            go(page, path, 500)
            print(
                path,
                page.evaluate("""() => ({title: document.title,
              desc: document.querySelector('meta[name=description]')?.content,
              og: [...document.querySelectorAll('meta[property^="og:"]')].map(m => m.getAttribute('property')),
              h1: [...document.querySelectorAll('h1')].map(h => h.innerText)})"""),
            )
        print("CONSOLE ERRORS:", console[:20])

        rr = page.request.post(BASE + "/api/booking/quote", data={"roomId": "bad", "checkIn": "2020-01-01"})
        print("QUOTE bad ->", rr.status, rr.text()[:400])
        rr = page.request.get(BASE + "/api/rooms?branchId=" + BENIN)
        print("ROOMS benin ->", rr.status, rr.text()[:2500])

        m = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
        mp = m.new_page()
        mp.goto(BASE + "/branches", wait_until="networkidle")
        print("mobile overflow /branches:", mp.evaluate("document.documentElement.scrollWidth - innerWidth"))
        browser.close()


if __name__ == "__main__":
    main()
