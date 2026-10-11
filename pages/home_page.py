from playwright.sync_api import expect

from pages.base_page import BasePage


class HomePage(BasePage):
    path = "/"

    def __init__(self, page):
        super().__init__(page)
        self.explore_rooms_link = page.get_by_role("link", name="Explore rooms")
        self.branch_link = page.get_by_role("link", name="Benin City 34 Sapele Road")
        self.hero_text = page.get_by_text("Space to work, and to stop working")

    def expect_loaded(self) -> None:
        expect(self.branch_link).to_be_visible()

    def explore_rooms(self) -> None:
        self.explore_rooms_link.click()
