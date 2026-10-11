import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class AccountPage(BasePage):
    path = "/account"

    def __init__(self, page: Page):
        super().__init__(page)
        # signed out
        self.signed_out_heading = self.main.get_by_role("heading", name="Sign in to view your account")
        self.signed_out_copy = self.main.get_by_text(re.compile("Manage your bookings"))
        self.signed_out_sign_in = self.main.get_by_role("button", name="Sign in")
        self.find_by_reference = self.main.get_by_role("link", name="Find your booking by reference")
        # signed in
        self.heading = self.main.get_by_role("heading", level=1)
        self.breadcrumb = self.main.get_by_role("navigation", name="Breadcrumb")
        self.booking_history = self.main.get_by_text(
            re.compile("Booking history|My bookings|Your bookings", re.I)
        )
        self.sign_out = page.get_by_role("button", name=re.compile("Sign out|Log out", re.I))

    def expect_signed_in(self) -> None:
        expect(self.signed_out_heading).to_have_count(0)
        expect(self.heading).to_be_visible()
