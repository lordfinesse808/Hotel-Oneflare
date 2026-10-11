"""Booking wizard: 1 Your stay > 2 Details > 3 Review & book > 4 Confirmed (all on /booking)."""

import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.data_factory import GuestData


class BookingPage(BasePage):
    path = "/booking"

    def __init__(self, page: Page):
        super().__init__(page)
        self.steps = self.main.get_by_text(re.compile(r"Your stay.*Details.*Review & book.*Confirmed"))
        # step 2 - guest details
        self.heading = self.main.get_by_role("heading", name="Who is staying?")
        self.guest_name = self.main.get_by_role("textbox", name="John Doe")
        self.guest_email = self.main.get_by_role("textbox", name="alex.morgan@example.com")
        self.guest_phone = self.main.get_by_role("textbox", name="+234 800 000 0000")
        self.notes = self.main.get_by_role("textbox", name=re.compile("Late arrival"))
        self.consent = self.main.get_by_role("checkbox", name=re.compile("I agree to this hotel holding"))
        self.privacy_link = self.main.get_by_role("link", name="privacy policy")
        self.back_to_room = self.main.get_by_role("button", name="Back to the room")
        self.review_button = self.main.get_by_role("button", name="Review my booking")
        self.name_error = self.main.get_by_text("Enter the guest's full name")
        self.email_error = self.main.get_by_text("Enter a valid email")
        self.phone_error = self.main.get_by_text("Enter a valid phone number")
        self.consent_error = self.main.get_by_text("You must agree before continuing")
        self.name_format_error = self.main.get_by_text(
            re.compile(r"(only )?letters|valid (full )?name", re.I)
        )
        # step 3 - review
        self.review_heading = self.main.get_by_role("heading", name="Check it over")
        self.change_room = self.main.get_by_role("button", name="Change room or dates")
        self.edit_details = self.main.get_by_role("button", name="Edit details")
        self.back_to_details = self.main.get_by_role("button", name="Back to guest details")
        self.confirm_button = self.main.get_by_role("button", name="Confirm booking")
        self.unpaid_review_note = self.main.get_by_text(re.compile("This booking is unpaid"))
        # step 4
        self.confirmed_heading = self.main.get_by_role("heading", name=re.compile("confirmed|booked", re.I))
        self.reference = self.main.get_by_text(re.compile(r"HMS-\d{4}-\d+"))
        # sidebar summary
        self.total = self.main.get_by_text(re.compile(r"Total\s*₦[\d,]+")).last

    def expect_loaded(self) -> None:
        expect(self.heading).to_be_visible(timeout=15000)

    def fill_guest(self, guest: GuestData) -> "BookingPage":
        self.guest_name.fill(guest.full_name)
        self.guest_email.fill(guest.email)
        self.guest_phone.fill(guest.phone)
        self.notes.fill(guest.notes)
        return self

    def accept_consent(self) -> "BookingPage":
        self.consent.check()
        return self

    def go_to_review(self, guest: GuestData) -> "BookingPage":
        self.fill_guest(guest).accept_consent()
        self.review_button.click()
        expect(self.review_heading).to_be_visible(timeout=15000)
        return self

    def total_amounts(self) -> list[int]:
        """Every 'Total ₦x' figure on the page (review panel + sidebar)."""
        texts = self.main.get_by_text(re.compile(r"Total\s*₦[\d,]+")).all_inner_texts()
        return [int(m.replace(",", "")) for t in texts for m in re.findall(r"Total\s*₦([\d,]+)", t)]
