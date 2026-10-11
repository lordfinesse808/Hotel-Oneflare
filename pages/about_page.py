from playwright.sync_api import Page

from pages.base_page import BasePage


class AboutPage(BasePage):
    path = "/about"

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = self.main.get_by_role("heading", level=1)
        self.principles_heading = self.main.get_by_role("heading", name="What we hold ourselves to")
        self.principles = self.main.get_by_role("heading", level=3)
        self.locations_heading = self.main.get_by_role("heading", name="The locations")
        self.location_links = self.main.get_by_role("link").filter(has_text="Oneflare Grand Plaza -")
