import re

from playwright.sync_api import Page

from pages.base_page import BasePage


class ContactPage(BasePage):
    path = "/contact"

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = self.main.get_by_role("heading", level=1)
        self.map_frame = self.main.locator("iframe")
        self.info_note = self.main.get_by_text(re.compile("aren't listed for this branch|not listed", re.I))
        self.lookup_link = self.main.get_by_role("link", name="look it up with your reference")
        self.form_heading = self.main.get_by_role("heading", name="Send a message")
        self.routing = self.main.get_by_text(re.compile(r"^Going to "))
        self.name = self.main.get_by_role("textbox", name="John Doe")
        self.email = self.main.get_by_role("textbox", name="johndoe@gmail.com")
        self.phone = self.main.get_by_role("textbox", name="+234 800 000 0000")
        self.subject = self.main.get_by_role("textbox", name="General enquiry")
        self.message = self.main.get_by_role("textbox", name=re.compile("Tell us what you need"))
        self.send = self.main.get_by_role("button", name="Send message")
        self.privacy_link = self.main.get_by_role("link", name="privacy policy")

    def open_for_branch(self, branch_id: str) -> "ContactPage":
        return self.open(f"{self.path}?branch={branch_id}")

    def branch_tab(self, city: str):
        return self.main.get_by_role("button", name=city, exact=True)

    def info_value(self, label: str):
        """Value paragraph that follows a label such as 'Address'/'Phone'/'Email'/'Hours'."""
        return self.main.get_by_text(label, exact=True).locator("xpath=following-sibling::*[1]")
