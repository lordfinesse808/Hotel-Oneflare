from playwright.sync_api import Page

from pages.base_page import BasePage


class GalleryPage(BasePage):
    path = "/gallery"

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = self.main.get_by_role("heading", level=1)
        self.intro = self.main.get_by_text("Photographs from")
        self.location_filter = self.main.get_by_role("combobox")
        # Gallery photos; the CTA background image has an empty alt and is excluded.
        self.photos = self.main.locator("img[alt]:not([alt=''])")

    def category(self, name: str):
        return self.main.get_by_role("button", name=name, exact=True)

    def image(self, alt: str):
        return self.main.get_by_role("img", name=alt, exact=True)

    def photo_alts(self) -> list[str]:
        return [a for a in self.photos.evaluate_all("els => els.map(e => e.alt)")]
