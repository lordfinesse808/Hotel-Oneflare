"""Site discovery: prints ARIA snapshots, links, headers and API calls for every key page/state.
Run in CI (where the site is reachable) to (re)derive selectors after UI changes:
    python ci/discover.py https://hotel-plaza-preview.vercel.app
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://hotel-plaza-preview.vercel.app").rstrip("/")


def section(title):
    print(f"\n{'=' * 20} {title} {'=' * 20}", flush=True)


def snap(page, title, locator="body"):
    section(title)
    print("URL:", page.url)
    try:
        print(page.locator(locator).first.aria_snapshot(timeout=10000))
    except Exception as e:  # noqa: BLE001 - discovery must keep going
        print("SNAPSHOT FAILED:", e)


def safe(fn, label):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"!! {label} failed: {str(e)[:400]}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, timezone_id="Africa/Lagos")
        page = ctx.new_page()
        api = []
        page.on("response", lambda r: api.append(f"{r.status} {r.request.method} {r.url}") if "/api/" in r.url else None)

        for path in ["/", "/rooms", "/branches", "/gallery", "/about", "/contact", "/account", "/booking"]:
            api.clear()
            page.goto(BASE + path, wait_until="networkidle")
            page.wait_for_timeout(1500)
            snap(page, f"PAGE {path}")
            print("TITLE:", page.title())
            print("API:", json.dumps(sorted(set(api)), indent=0))

        r = page.request.get(BASE + "/")
        section("HEADERS /")
        print(json.dumps(r.headers, indent=1))
        for path in ["/robots.txt", "/sitemap.xml", "/privacy-policy", "/terms", "/cancellation-policy", "/staff",
                     "/xyz-not-here", "/api/unknown", "/api/settings", "/api/branches", "/api/customization",
                     "/api/auth/me"]:
            rr = page.request.get(BASE + path)
            print(f"GET {path} -> {rr.status} {rr.headers.get('content-type')} :: {rr.text()[:300]!r}")
        rr = page.request.get(BASE + "/api/rooms")
        print("GET /api/rooms ->", rr.status, rr.text()[:1500])

        # rooms page details
        page.goto(BASE + "/rooms", wait_until="networkidle")
        section("ROOMS inputs")
        for el in page.locator("input, select, button").all()[:80]:
            safe(lambda el=el: print(el.evaluate(
                "e => e.outerHTML.slice(0, 300)")), "outerHTML")
        section("ROOMS select options")
        for s in page.locator("select").all():
            safe(lambda s=s: print(s.evaluate("e => [...e.options].map(o => o.value + ' | ' + o.text)")), "options")
        section("ROOMS links")
        for a in page.locator("a").all()[:120]:
            safe(lambda a=a: print(a.get_attribute("href"), "|", a.inner_text()[:80].replace("\n", " ")), "link")

        # room detail
        safe(lambda: page.get_by_role("link", name="View details").first.click(), "view details")
        page.wait_for_timeout(4000)
        snap(page, "ROOM DETAIL (View details)", "main")
        safe(lambda: page.goto(BASE + "/rooms", wait_until="networkidle"), "back")
        safe(lambda: page.get_by_role("link", name="Select room").first.click(), "select room")
        page.wait_for_timeout(5000)
        snap(page, "AFTER Select room", "main")

        # find a bookable (hotel-level) room via home page 'Free for your dates'
        page.goto(BASE + "/", wait_until="networkidle")
        section("HOME links")
        for a in page.locator("a").all()[:150]:
            safe(lambda a=a: print(a.get_attribute("href"), "|", a.inner_text()[:80].replace("\n", " ")), "link")
        page.goto(BASE + "/rooms/965c310d-7b91-46b3-b2aa-3053c19ec203", wait_until="networkidle")
        page.wait_for_timeout(3000)
        snap(page, "ROOM DETAIL hotel-level 965c...", "main")
        section("DETAIL inputs")
        for el in page.locator("input, select, button").all()[:60]:
            safe(lambda el=el: print(el.evaluate("e => e.outerHTML.slice(0, 300)")), "outerHTML")
        safe(lambda: page.get_by_role("button", name="Continue to guest details").click(), "continue")
        page.wait_for_timeout(4000)
        snap(page, "BOOKING guest details", "main")
        section("BOOKING inputs")
        for el in page.locator("input, select, button, textarea").all()[:60]:
            safe(lambda el=el: print(el.evaluate("e => e.outerHTML.slice(0, 300)")), "outerHTML")
        # empty submit to see validation
        safe(lambda: page.get_by_role("button", name="Review my booking").click(), "review empty")
        page.wait_for_timeout(1000)
        snap(page, "BOOKING after empty submit", "main")
        safe(lambda: page.get_by_role("textbox", name="John Doe").fill("QA Tester"), "name")
        safe(lambda: page.get_by_role("textbox", name="+234 800 000").fill("+2348012345678"), "phone")
        safe(lambda: page.get_by_role("textbox", name="alex.morgan@example.com").fill("qa@maildrop.cc"), "email")
        safe(lambda: page.get_by_role("checkbox").first.check(), "consent")
        safe(lambda: page.get_by_role("button", name="Review my booking").click(), "review")
        page.wait_for_timeout(3000)
        snap(page, "BOOKING review", "main")

        # sign-in modal
        page.goto(BASE + "/", wait_until="networkidle")
        safe(lambda: page.get_by_role("button", name="Sign in").click(), "sign in")
        page.wait_for_timeout(1000)
        snap(page, "SIGN IN modal", "[role=dialog]")
        safe(lambda: page.get_by_role("dialog").get_by_role("button", name="Next").click(), "next")
        page.wait_for_timeout(1000)
        snap(page, "SIGN IN after Next", "[role=dialog]")
        section("DIALOG inputs")
        for el in page.locator("[role=dialog] input, [role=dialog] button").all()[:40]:
            safe(lambda el=el: print(el.evaluate("e => e.outerHTML.slice(0, 300)")), "outerHTML")
        safe(lambda: page.get_by_role("dialog").get_by_role("button", name="Continue").click(), "continue empty")
        page.wait_for_timeout(1000)
        snap(page, "SIGN IN after empty Continue", "[role=dialog]")
        page.goto(BASE + "/", wait_until="networkidle")
        safe(lambda: page.get_by_role("button", name="Sign in").click(), "sign in 2")
        safe(lambda: page.get_by_role("dialog").get_by_role("button", name="Create an account").click(), "create")
        page.wait_for_timeout(1000)
        snap(page, "CREATE ACCOUNT", "[role=dialog]")

        # branches / contact interactions
        page.goto(BASE + "/branches", wait_until="networkidle")
        section("BRANCHES links")
        for a in page.locator("a").all()[:120]:
            safe(lambda a=a: print(a.get_attribute("href"), "|", a.inner_text()[:80].replace("\n", " ")), "link")
        page.goto(BASE + "/gallery", wait_until="networkidle")
        section("GALLERY imgs")
        for i in page.locator("main img").all()[:60]:
            safe(lambda i=i: print(i.get_attribute("alt"), "|", i.get_attribute("src")), "img")
        safe(lambda: page.locator("main img").first.click(), "lightbox")
        page.wait_for_timeout(800)
        snap(page, "GALLERY lightbox")

        # mobile
        m = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
        mp = m.new_page()
        mp.goto(BASE + "/rooms", wait_until="networkidle")
        snap(mp, "MOBILE rooms header", "header")
        safe(lambda: mp.get_by_role("button", name="Toggle menu").click(), "menu")
        mp.wait_for_timeout(800)
        snap(mp, "MOBILE menu open")
        browser.close()


if __name__ == "__main__":
    main()
