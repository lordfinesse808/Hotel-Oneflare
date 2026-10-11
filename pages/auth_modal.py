"""The 'Sign in or create an account' dialog (it is a modal, not a separate page)."""
from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.data_factory import UserData


class AuthModal(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)  # run BasePage.__init__ first so header etc. exist
        self.dialog = page.get_by_role("dialog", name="Sign in or create an account")
        self.create_account_button = self.dialog.get_by_role("button", name="Create an account")
        self.register_heading = page.get_by_role("heading", name="Create a customer account")
        # Field names come from placeholder text (the accessible name of each textbox)
        self.full_name = page.get_by_role("textbox", name="John Doe")
        self.email = page.get_by_role("textbox", name="johndoe@gmail.com")
        self.phone = page.get_by_role("textbox", name="+")
        self.password = page.get_by_role("textbox", name="Choose a strong password")
        self.confirm_password = page.get_by_role("textbox", name="Confirm password")
        self.toggle_password = page.get_by_role("button", name="Toggle password visibility")
        self.submit = page.get_by_role("button", name="Create account →")

    def open_sign_in(self) -> "AuthModal":
        self.sign_in_button.click()
        expect(self.dialog).to_be_visible()
        return self

    def open_registration_form(self) -> "AuthModal":
        self.open_sign_in()
        self.create_account_button.click()
        expect(self.register_heading).to_be_visible()
        return self

    def fill_registration(self, user: UserData, confirm: str | None = None) -> "AuthModal":
        self.full_name.fill(user.full_name)
        self.email.fill(user.email)
        self.phone.fill(user.phone)
        self.password.fill(user.password)
        # `confirm` lets a test pass a DIFFERENT value to check mismatch handling
        self.confirm_password.fill(user.password if confirm is None else confirm)
        return self

    def register(self, user: UserData) -> None:
        """Full happy path: open form -> fill -> submit -> wait until logged in."""
        self.open_registration_form()
        self.fill_registration(user)
        self.submit.click()
        expect(self.user_menu(user.first_name)).to_be_visible()  # proof of success
