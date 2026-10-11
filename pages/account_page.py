from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class AccountPage(BasePage):
    """Reached by clicking the user link in the header after login."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.breadcrumb = page.get_by_role("navigation", name="Breadcrumb")
        self.booking_history_button = page.get_by_role("button", name="Booking history")
        self.booking_history_heading = page.get_by_role("heading", name="Booking history")
        self.book_another_stay = page.get_by_role("link", name="Book another stay")

    def open_booking_history(self) -> None:
        self.booking_history_button.click()
        expect(self.booking_history_heading).to_be_visible()
