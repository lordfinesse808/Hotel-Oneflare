import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class RoomDetailPage(BasePage):
    path = "/rooms/"  # real URL is /rooms/<uuid>?checkIn=..&checkOut=..

    def __init__(self, page: Page):
        super().__init__(page)
        self.check_in = page.get_by_role("textbox", name="Check in")
        self.check_out = page.get_by_role("textbox", name="Check out")
        self.price_per_night = page.get_by_text(re.compile(r"₦[\d,]+\s*per night")).first
        self.total = page.get_by_text(re.compile(r"Total\s*₦")).first
        self.unpaid_notice = page.get_by_text("This booking is unpaid — pay at the hotel.")
        self.continue_button = page.get_by_role("button", name="Continue to guest details")
        self.breadcrumb = page.get_by_role("navigation", name="Breadcrumb")

    def expect_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/rooms/[0-9a-f-]{36}"))
        expect(self.continue_button).to_be_visible()

    def continue_to_guest_details(self):
        from pages.booking_page import BookingPage
        self.continue_button.click()
        return BookingPage(self.page)
