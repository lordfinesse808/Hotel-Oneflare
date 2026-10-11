"""Sign-in modal, registration form validation, forgot password, brute-force protection."""

import re
import uuid

import pytest
from playwright.sync_api import expect

from pages.auth_modal import AuthModal
from pages.home_page import HomePage
from utils.data_factory import UserData


@pytest.fixture
def modal(page) -> AuthModal:
    HomePage(page).open()
    return AuthModal(page)


@pytest.mark.smoke
@pytest.mark.tc("TC-100")
def test_sign_in_dialog_opens_with_role_choice(modal: AuthModal):
    modal.open_sign_in()
    expect(modal.customer_role).to_be_visible()
    expect(modal.agent_role).to_be_visible()
    expect(modal.create_account_button).to_be_visible()


@pytest.mark.tc("TC-100")
def test_customer_role_then_next_opens_sign_in_form(modal: AuthModal):
    modal.open_customer_form()
    expect(modal.identifier).to_be_visible()
    expect(modal.login_password).to_have_attribute("type", "password")


@pytest.mark.tc("TC-100")
@pytest.mark.parametrize("how", ["close-button", "escape"])
def test_dialog_closes(modal: AuthModal, how):
    modal.open_sign_in()
    if how == "escape":
        modal.page.keyboard.press("Escape")
    else:
        modal.close_button.click()
    expect(modal.dialog).to_be_hidden()
    expect(modal.sign_in_button).to_be_visible()


@pytest.mark.tc("TC-100", "TC-055")
@pytest.mark.a11y
def test_focus_returns_to_trigger_after_close(modal: AuthModal):
    modal.open_sign_in()
    modal.page.keyboard.press("Escape")
    expect(modal.dialog).to_be_hidden()
    expect(modal.sign_in_button).to_be_focused()


@pytest.mark.tc("TC-101")
def test_sign_in_mandatory_field_validation(modal: AuthModal):
    calls = []
    modal.page.on("request", lambda r: calls.append(r.url) if "/api/auth/login" in r.url else None)
    modal.open_customer_form()
    modal.continue_button.click()
    expect(modal.required_errors).to_have_count(2)
    assert not calls, "empty form must not call the login API"


@pytest.mark.tc("TC-120", "TC-101")
def test_sign_in_identifier_format_checked_client_side(modal: AuthModal):
    calls = []
    modal.page.on("request", lambda r: calls.append(r.url) if "/api/auth/login" in r.url else None)
    modal.open_customer_form()
    modal.identifier.fill("abc")
    modal.login_password.fill("whatever-password-1")
    modal.continue_button.click()
    expect(modal.identifier_error).to_be_visible()
    assert not calls, "invalid identifier was sent to /api/auth/login"


@pytest.mark.tc("TC-040")
def test_invalid_credentials_show_generic_error(modal: AuthModal):
    modal.open_customer_form()
    modal.identifier.fill(f"nobody-{uuid.uuid4().hex[:8]}@maildrop.cc")
    modal.login_password.fill("wrong-password-123")
    modal.continue_button.click()
    expect(modal.invalid_credentials).to_be_visible(timeout=15000)
    # no account enumeration: wording must not reveal whether the email exists
    expect(modal.dialog).not_to_contain_text(re.compile(r"no account|not registered|does not exist", re.I))


@pytest.mark.needs_account
@pytest.mark.tc("TC-040")
def test_wrong_password_for_real_account_is_generic(modal: AuthModal):
    from config.settings import TEST_EMAIL

    modal.open_customer_form()
    modal.identifier.fill(TEST_EMAIL)
    modal.login_password.fill("definitely-wrong-password-1")
    modal.continue_button.click()
    expect(modal.invalid_credentials).to_be_visible(timeout=15000)


@pytest.mark.security
@pytest.mark.tc("TC-102")
@pytest.mark.defect("BUG-041")
def test_brute_force_is_throttled(modal: AuthModal):
    """6 wrong passwords for one (non-existent) identifier must trigger a delay, CAPTCHA or lockout."""
    statuses = []
    modal.page.on("response", lambda r: statuses.append(r.status) if "/api/auth/login" in r.url else None)
    modal.open_customer_form()
    modal.identifier.fill(f"bruteforce-{uuid.uuid4().hex[:8]}@maildrop.cc")
    for i in range(7):
        modal.login_password.fill(f"wrong-password-{i:03d}")
        modal.continue_button.click()
        modal.page.wait_for_timeout(700)
    throttled = (
        any(s == 429 for s in statuses)
        or modal.dialog.get_by_text(re.compile(r"too many|try again later|locked|captcha", re.I)).count() > 0
    )
    assert throttled, f"7 failed logins, no throttling (statuses {statuses})"


@pytest.mark.tc("TC-103")
def test_registration_form_fields(modal: AuthModal):
    modal.open_registration_form()
    for field in (modal.full_name, modal.email, modal.phone, modal.password, modal.confirm_password):
        expect(field).to_be_visible()
    expect(modal.country_code).to_contain_text("+234")


@pytest.mark.tc("TC-103")
def test_empty_registration_is_blocked_with_field_errors(modal: AuthModal):
    modal.open_registration_form()
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()
    for msg in ("Enter your full name", "Enter a valid email", "At least 12 characters"):
        expect(modal.dialog.get_by_text(msg)).to_be_visible()


@pytest.mark.tc("TC-103")
@pytest.mark.defect(
    reason="phone error reads 'Invalid input: expected string, received undefined' (raw schema text)"
)
def test_empty_phone_error_is_human_readable(modal: AuthModal):
    modal.open_registration_form()
    modal.submit.click()
    expect(modal.dialog.get_by_text(re.compile(r"expected string|received undefined"))).to_have_count(0)


@pytest.mark.tc("TC-103")
def test_password_visibility_toggle(modal: AuthModal):
    modal.open_registration_form()
    modal.password.fill("Abc!12345678")
    modal.toggle_password.click()
    expect(modal.password).to_have_attribute("type", "text")  # revealed
    modal.toggle_password.click()
    expect(modal.password).to_have_attribute("type", "password")  # hidden again


@pytest.mark.tc("TC-103")
def test_short_password_rejected(modal: AuthModal):
    user = UserData.new()
    modal.open_registration_form()
    modal.fill_registration(user)
    modal.password.fill("Short1!")
    modal.confirm_password.fill("Short1!")
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()
    expect(modal.dialog.get_by_text("At least 12 characters")).to_be_visible()


@pytest.mark.tc("TC-103")
def test_mismatched_passwords_block_registration(modal: AuthModal):
    user = UserData.new()
    modal.open_registration_form()
    modal.fill_registration(user, confirm=user.password + "x")
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()  # still on the form
    expect(modal.dialog).to_be_visible()


@pytest.mark.tc("TC-103")
def test_invalid_email_blocks_registration(modal: AuthModal):
    user = UserData.new()
    modal.open_registration_form()
    modal.fill_registration(user)
    modal.email.fill("not-an-email")
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()
    expect(modal.dialog.get_by_text("Enter a valid email")).to_be_visible()


@pytest.mark.live_write
@pytest.mark.tc("TC-103")
def test_register_new_customer(modal: AuthModal):
    user = UserData.new()
    modal.register(user)
    expect(modal.sign_in_button).to_have_count(0)  # Sign in disappears once logged in


@pytest.mark.tc("TC-104")
def test_forgot_password_form(modal: AuthModal):
    modal.open_customer_form()
    modal.forgot_password.click()
    expect(modal.reset_heading).to_be_visible()
    expect(modal.send_reset_code).to_be_visible()
    modal.back_to_sign_in.click()
    expect(modal.signin_heading).to_be_visible()


@pytest.mark.live_write
@pytest.mark.tc("TC-104")
def test_forgot_password_unknown_email_is_generic(modal: AuthModal):
    modal.open_customer_form()
    modal.forgot_password.click()
    modal.reset_email.fill(f"nobody-{uuid.uuid4().hex[:8]}@maildrop.cc")
    modal.send_reset_code.click()
    expect(modal.dialog).not_to_contain_text(re.compile(r"no account|not registered|does not exist", re.I))
