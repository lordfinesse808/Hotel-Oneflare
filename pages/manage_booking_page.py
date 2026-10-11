import re

from playwright.sync_api import Page

from pages.base_page import BasePage


class ManageBookingPage(BasePage):
    path = "/manage-booking"

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = self.main.get_by_role("heading", name="Find your booking")
        self.reference = self.main.get_by_role("textbox", name=re.compile(r"HMS-\d{4}"))
        self.email = self.main.get_by_role("textbox", name="johndoe@gmail.com")
        self.find_button = self.main.get_by_role("button", name="Find my booking")
        self.sign_in_link = self.main.get_by_role("link", name="Sign in to your account")
        self.not_found = self.main.get_by_text(
            re.compile(r"(couldn't|could not|can't|no booking).*(find|found|match)|not found", re.I)
        )
        self.required = self.main.get_by_text(
            re.compile("Required|Enter (a|your) (valid )?(booking )?reference", re.I)
        )
