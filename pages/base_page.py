"""BasePage: everything shared by all pages (header, footer, navigation, helpers).
Every other page object inherits from this class (OOP inheritance = no duplicated code)."""

import re
import time

from playwright.sync_api import Locator, Page, expect


class BasePage:
    path = "/"  # each subclass overrides this with its own URL path

    def __init__(self, page: Page):
        self.page = page  # the Playwright Page this object drives
        # Locators are LAZY: nothing is searched until you act on/assert them,
        # so defining them in __init__ is cheap and always uses fresh DOM state.
        self.header = page.get_by_role("banner")  # <header> element
        self.main = page.get_by_role("main")
        self.footer = page.get_by_role("contentinfo")
        self.logo = self.header.get_by_role("link", name="Oneflare Grand Plaza")
        self.sign_in_button = self.header.get_by_role("button", name="Sign in")
        self.book_now_link = self.header.get_by_role("link", name="Book now")
        self.search_box = page.get_by_role("searchbox", name="Search rooms")
        self.menu_toggle = self.header.get_by_role("button", name="Toggle menu")
        self.mobile_menu = page.get_by_role("dialog", name="Navigation menu")
        self.close_menu = self.mobile_menu.get_by_role("button", name="Close menu")
        self.footer_head_office = self.footer.get_by_text(re.compile(r"^Head office"))
        self.footer_legal = self.footer.get_by_text(re.compile(r"^©"))
        self.footer_contact_items = self.footer.get_by_role("list").first.get_by_role("listitem")

    # ---------- navigation ----------
    def open(self, path: str | None = None):
        self.page.goto(path or self.path)  # relative path + base_url from pytest.ini / --base-url
        self.settle()  # Next.js hydrates after load: clicking earlier is silently ignored
        return self  # returning self allows chaining: HomePage(page).open().do_x()

    def settle(self) -> None:
        """Wait until client-side data fetching has finished (Next.js pages render after /api calls)."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:  # noqa: BLE001 - long-polling widgets (maps) may keep the network busy
            pass

    def nav_link(self, name: str) -> Locator:
        # exact=True stops "Rooms" matching e.g. "See rooms at ..."
        return self.header.get_by_role("navigation").get_by_role("link", name=name, exact=True)

    def footer_link(self, name: str) -> Locator:
        return self.footer.get_by_role("link", name=name, exact=True)

    def go_to(self, name: str) -> None:
        self.nav_link(name).click()

    def user_menu(self, name: str) -> Locator:
        # After login the header shows the customer's name/initials instead of "Sign in"
        return self.header.get_by_role("link", name=re.compile(re.escape(name), re.I))

    def is_on_screen(self, locator: Locator) -> bool:
        """Slide-in drawers stay in the DOM when closed, translated off-screen; Playwright still calls
        them 'visible', so check the geometry instead."""
        box = locator.bounding_box()
        width = self.page.viewport_size["width"]
        return bool(box) and box["x"] < width - 1 and box["x"] + box["width"] > 1

    def expect_on_screen(self, locator: Locator, on: bool = True, timeout_s: float = 5.0) -> None:
        deadline = time.monotonic() + timeout_s
        while self.is_on_screen(locator) != on and time.monotonic() < deadline:
            self.page.wait_for_timeout(100)
        assert self.is_on_screen(locator) == on, f"{locator} on_screen != {on}"

    # ---------- shared assertions ----------
    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(re.compile(re.escape(fragment)))

    def expect_header_visible(self) -> None:
        expect(self.header).to_be_visible()
