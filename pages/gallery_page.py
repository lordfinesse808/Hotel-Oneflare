from playwright.sync_api import Page

from pages.base_page import BasePage


class GalleryPage(BasePage):
    path = "/gallery"

    def __init__(self, page: Page):
        super().__init__(page)
        self.intro = page.get_by_text("Every room, and")
        self.branch_filter = page.get_by_role("combobox")

    def category(self, name: str):
        return self.page.get_by_role("button", name=name)  # e.g. Bathrooms, Restaurant, Swimming Pool

    def image(self, alt: str):
        return self.page.get_by_role("img", name=alt)
