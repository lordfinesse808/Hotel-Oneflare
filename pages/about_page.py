from playwright.sync_api import Page

from pages.base_page import BasePage


class AboutPage(BasePage):
    path = "/about"

    def __init__(self, page: Page):
        super().__init__(page)
        self.about_text = page.get_by_text("About Oneflare Grand").first
        self.locations = page.get_by_text("The locations").first
