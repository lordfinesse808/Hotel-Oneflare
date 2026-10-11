from playwright.sync_api import Page

from pages.base_page import BasePage


class ContactPage(BasePage):
    path = "/contact"

    def __init__(self, page: Page):
        super().__init__(page)
        self.intro = page.locator("section").filter(has_text="Talk to us first").first
