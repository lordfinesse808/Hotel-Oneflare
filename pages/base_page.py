"""BasePage: everything shared by all pages (header, footer, navigation, helpers).
Every other page object inherits from this class (OOP inheritance = no duplicated code)."""
import re

from playwright.sync_api import Locator, Page, expect


class BasePage:
    path = "/"  # each subclass overrides this with its own URL path

    def __init__(self, page: Page):
        self.page = page  # the Playwright Page this object drives
        # Locators are LAZY: nothing is searched until you act on/assert them,
        # so defining them in __init__ is cheap and always uses fresh DOM state.
        self.header = page.get_by_role("banner")  # <header> element
        self.sign_in_button = page.get_by_role("button", name="Sign in")
        self.book_now_link = self.header.get_by_role("link", name="Book now")
        self.search_box = page.get_by_role("searchbox", name="Search")
        self.footer_head_office = page.get_by_text("Head office")

    # ---------- navigation ----------
    def open(self):
        self.page.goto(self.path)  # relative path + base_url from pytest.ini
        self.page.wait_for_load_state("domcontentloaded")
        return self  # returning self allows chaining: HomePage(page).open().do_x()

    def nav_link(self, name: str) -> Locator:
        # exact=True stops "Rooms" matching e.g. "Browse rooms"
        return self.header.get_by_role("link", name=name, exact=True)

    def go_to(self, name: str) -> None:
        self.nav_link(name).click()

    def user_menu(self, first_name: str) -> Locator:
        # After login the header link reads e.g. "JG John" (initials + first name)
        return self.header.get_by_role("link", name=re.compile(re.escape(first_name)))

    # ---------- shared assertions ----------
    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(re.compile(re.escape(fragment)))

    def expect_header_visible(self) -> None:
        expect(self.header).to_be_visible()
