"""Guest-details step of the booking wizard (Your stay > Details > Review & book > Confirmed)."""
import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.data_factory import GuestData


class BookingPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Who is staying?")
        self.guest_name = page.get_by_role("textbox", name="John Doe")
        self.guest_phone = page.get_by_role("textbox", name="+234 800 000")
        self.guest_email = page.get_by_role("textbox", name="alex.morgan@example.com")
        self.notes = page.get_by_role("textbox", name=re.compile("Late arrival"))
        self.consent = page.get_by_role("checkbox", name=re.compile("I agree to this hotel holding"))
        self.back_to_room = page.get_by_role("button", name="Back to the room")
        self.total = page.get_by_text(re.compile(r"Total\s*₦")).first
        self.review_step = page.get_by_text("Review & book")

    def expect_loaded(self) -> None:
        expect(self.heading).to_be_visible()

    def fill_guest(self, guest: GuestData) -> "BookingPage":
        self.guest_name.fill(guest.full_name)
        self.guest_phone.fill(guest.phone)
        self.guest_email.fill(guest.email)
        self.notes.fill(guest.notes)
        return self

    def accept_consent(self) -> "BookingPage":
        self.consent.check()
        return self
