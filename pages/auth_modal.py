"""The 'Sign in or create an account' dialog (a modal, not a separate page).

Flow: Sign in -> pick role (Customer / Agent) -> Next -> 'Continue as customer' form
      (identifier + password, Forgot password?, Create an account)."""

import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.data_factory import UserData


class AuthModal(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)  # run BasePage.__init__ first so header etc. exist
        self.dialog = page.get_by_role("dialog", name="Sign in or create an account")
        d = self.dialog
        self.close_button = d.get_by_role("button", name="Close", exact=True)
        # step 1 - role
        self.role_heading = d.get_by_text("How would you like to use the platform?")
        self.customer_role = d.get_by_role("button", name=re.compile(r"^Customer"))
        self.agent_role = d.get_by_role("button", name=re.compile(r"^Agent"))
        self.next_button = d.get_by_role("button", name="Next", exact=True)
        # step 2 - sign in
        self.signin_heading = d.get_by_role("heading", name="Continue as customer")
        self.identifier = d.get_by_role("textbox", name="johndoe@gmail.com")
        self.login_password = d.get_by_role("textbox", name="Enter password")
        self.continue_button = d.get_by_role("button", name=re.compile(r"^Continue"))
        self.forgot_password = d.get_by_role("button", name="Forgot password?")
        self.invalid_credentials = d.get_by_text("Invalid credentials")
        self.required_errors = d.get_by_text("Required", exact=True)
        self.identifier_error = d.get_by_text("Enter a valid email or phone number")
        # forgot password
        self.reset_heading = d.get_by_role("heading", name="Reset your password")
        self.reset_email = d.get_by_role("textbox", name="johndoe@gmail.com")
        self.send_reset_code = d.get_by_role("button", name=re.compile("Send reset code"))
        self.back_to_sign_in = d.get_by_role("button", name="Back to sign in")
        # registration
        self.create_account_button = d.get_by_role("button", name="Create an account")
        self.register_heading = d.get_by_role("heading", name="Create a customer account")
        self.full_name = d.get_by_role("textbox", name="John Doe")
        self.email = d.get_by_role("textbox", name="johndoe@gmail.com")
        self.country_code = d.get_by_role("combobox", name="Country code")
        self.phone = d.get_by_role("textbox", name="8012345678")
        self.password = d.get_by_role("textbox", name="Choose a strong password")
        self.confirm_password = d.get_by_role("textbox", name="Confirm password")
        self.toggle_password = d.get_by_role("button", name="Toggle password visibility")
        self.submit = d.get_by_role("button", name="Create account →")

    # ---------- open ----------
    def open_sign_in(self) -> "AuthModal":
        # retry: a click that lands before React hydration does nothing
        for _ in range(5):
            self.sign_in_button.click()
            try:
                self.dialog.wait_for(state="visible", timeout=2000)
                break
            except Exception:  # noqa: BLE001 - not hydrated yet, click again
                continue
        expect(self.dialog).to_be_visible()
        return self

    def open_customer_form(self) -> "AuthModal":
        """Role choice is remembered per browser, so step 1 may be skipped on later visits."""
        self.open_sign_in()
        if self.customer_role.is_visible():
            self.customer_role.click()
            self.next_button.click()
        expect(self.signin_heading).to_be_visible()
        return self

    def open_registration_form(self) -> "AuthModal":
        self.open_sign_in()
        self.create_account_button.click()
        expect(self.register_heading).to_be_visible()
        return self

    # ---------- actions ----------
    def sign_in(self, identifier: str, password: str) -> str:
        """Sign in as a customer and return the name shown in the header."""
        self.open_customer_form()
        self.identifier.fill(identifier)
        self.login_password.fill(password)
        self.continue_button.click()
        expect(self.dialog).to_be_hidden(timeout=20000)
        expect(self.sign_in_button).to_have_count(0)
        return (
            self.header.get_by_role("link", name=re.compile(r"\w"))
            .filter(
                has_not_text=re.compile(
                    r"^(Home|Rooms|Branches|Gallery|About|Contact|Book now|Oneflare Grand Plaza)$"
                )
            )
            .last.inner_text()
        )

    def fill_registration(self, user: UserData, confirm: str | None = None) -> "AuthModal":
        self.full_name.fill(user.full_name)
        self.email.fill(user.email)
        self.phone.fill(re.sub(r"^\+234", "", user.phone))  # country code is a separate select (+234 default)
        self.password.fill(user.password)
        # `confirm` lets a test pass a DIFFERENT value to check mismatch handling
        self.confirm_password.fill(user.password if confirm is None else confirm)
        return self

    def register(self, user: UserData) -> None:
        """Full happy path: open form -> fill -> submit -> wait until logged in."""
        self.open_registration_form()
        self.fill_registration(user)
        self.submit.click()
        expect(self.dialog).to_be_hidden(timeout=20000)
        expect(self.user_menu(user.first_name)).to_be_visible()  # proof of success
