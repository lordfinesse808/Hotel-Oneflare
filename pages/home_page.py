from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.search_widget import SearchWidget


class HomePage(BasePage):
    path = "/"

    def __init__(self, page):
        super().__init__(page)
        self.hero_heading = self.main.get_by_role("heading", level=1)
        self.hero_text = self.main.get_by_role("heading", name="Space to work, and to stop working")
        self.explore_rooms_link = self.main.get_by_role("link", name="Explore rooms")
        self.search = SearchWidget(page)
        # sections
        self.locations_heading = self.main.get_by_role("heading", name="Find us where you need us.")
        self.location_cards = (
            self.main.get_by_role("link").filter(has=page.locator("p")).filter(has_text="Road")
        )
        self.free_rooms_heading = self.main.get_by_role("heading", name="Free for your dates")
        self.free_rooms_caption = self.main.get_by_text("Live at ")
        self.see_all_rooms = self.main.get_by_role("link", name="See all rooms")
        self.gallery_heading = self.main.get_by_role("heading", name="The rest of the house")
        self.amenities_heading = self.main.get_by_role("heading", name="Included, not extra.")
        self.view_details_links = self.main.get_by_role("link", name="View details")
        self.price_per_night = self.main.get_by_text(" / night")

    def expect_loaded(self) -> None:
        expect(self.hero_heading).to_be_visible()
        expect(self.search.check_availability).to_be_visible()

    def explore_rooms(self) -> None:
        self.explore_rooms_link.click()

    def section_after(self, heading) -> "object":
        """The section element that contains a given heading."""
        return self.main.locator("section").filter(has=heading).first
