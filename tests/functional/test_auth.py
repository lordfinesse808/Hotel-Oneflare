import pytest
from playwright.sync_api import expect

from pages.auth_modal import AuthModal
from pages.home_page import HomePage
from utils.data_factory import UserData


@pytest.fixture
def modal(page):
    HomePage(page).open()
    return AuthModal(page)


@pytest.mark.smoke
def test_sign_in_dialog_opens(modal):
    modal.open_sign_in()
    expect(modal.create_account_button).to_be_visible()


@pytest.mark.smoke
def test_register_new_customer(modal):
    user = UserData.new()
    modal.register(user)
    expect(modal.user_menu(user.first_name)).to_be_visible()
    expect(modal.sign_in_button).to_have_count(0)  # Sign in disappears once logged in


def test_password_visibility_toggle(modal):
    modal.open_registration_form()
    modal.password.fill("Abc!12345")
    modal.toggle_password.click()
    expect(modal.password).to_have_attribute("type", "text")  # revealed
    modal.toggle_password.click()
    expect(modal.password).to_have_attribute("type", "password")  # hidden again


def test_mismatched_passwords_block_registration(modal):
    user = UserData.new()
    modal.open_registration_form()
    modal.fill_registration(user, confirm=user.password + "x")
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()  # still on the form
    expect(modal.user_menu(user.first_name)).to_have_count(0)


def test_empty_form_blocks_registration(modal):
    modal.open_registration_form()
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()


def test_invalid_email_blocks_registration(modal):
    user = UserData.new()
    modal.open_registration_form()
    modal.fill_registration(user)
    modal.email.fill("not-an-email")
    modal.submit.click()
    expect(modal.register_heading).to_be_visible()
    expect(modal.user_menu(user.first_name)).to_have_count(0)
