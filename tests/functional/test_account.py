"""Account area (signed out and signed in), manage-a-booking lookup, sign out."""

import re

import pytest
from playwright.sync_api import expect

from pages.account_page import AccountPage
from pages.contact_page import ContactPage
from pages.home_page import HomePage
from pages.manage_booking_page import ManageBookingPage


# ---------- signed out ----------
@pytest.mark.tc("TC-105")
def test_signed_out_account_page_prompts_sign_in(page):
    account = AccountPage(page).open()
    expect(account.signed_out_heading).to_be_visible()
    expect(account.signed_out_sign_in).to_be_visible()


@pytest.mark.tc("TC-105", "TC-043")
def test_customer_account_copy_has_no_agent_wording(page):
    account = AccountPage(page).open()
    expect(account.main).not_to_contain_text(re.compile("commission", re.I))


@pytest.mark.tc("TC-041", "TC-114")
def test_manage_booking_lookup_form(page):
    manage = ManageBookingPage(page).open()
    expect(manage.heading).to_be_visible()
    expect(manage.reference).to_be_visible()
    expect(manage.email).to_be_visible()
    expect(manage.find_button).to_be_visible()


@pytest.mark.tc("TC-041")
def test_manage_booking_requires_fields(page):
    manage = ManageBookingPage(page).open()
    manage.find_button.click()
    expect(manage.heading).to_be_visible()
    expect(page).to_have_url(re.compile(r"/manage-booking"))


@pytest.mark.tc("TC-041")
def test_manage_booking_wrong_reference_shows_not_found(page):
    manage = ManageBookingPage(page).open()
    manage.reference.fill("HMS-2026-999999")
    manage.email.fill("nobody-qa@maildrop.cc")
    manage.find_button.click()
    expect(manage.not_found).to_be_visible(timeout=15000)


@pytest.mark.tc("TC-114")
def test_contact_reference_link_opens_lookup(page):
    contact = ContactPage(page).open()
    contact.lookup_link.click()
    expect(ManageBookingPage(page).heading).to_be_visible()


@pytest.mark.tc("TC-041")
def test_footer_manage_a_booking_opens_lookup(page):
    home = HomePage(page).open()
    home.footer_link("Manage a booking").click()
    expect(ManageBookingPage(page).heading).to_be_visible()


# ---------- signed in (needs TEST_EMAIL / TEST_PASSWORD) ----------
@pytest.mark.smoke
@pytest.mark.needs_account
@pytest.mark.tc("TC-040")
def test_valid_sign_in_shows_customer_in_header(auth_page):
    home = HomePage(auth_page).open()
    expect(home.sign_in_button).to_have_count(0)


@pytest.mark.needs_account
@pytest.mark.tc("TC-105")
def test_signed_in_account_page_shows_profile(auth_page, auth_state):
    account = AccountPage(auth_page).open()
    account.expect_signed_in()
    expect(account.main).not_to_contain_text(re.compile("commission", re.I))


@pytest.mark.needs_account
@pytest.mark.tc("TC-107")
@pytest.mark.security
def test_sign_out_clears_session(auth_page):
    account = AccountPage(auth_page).open()
    account.expect_signed_in()
    account.sign_out.first.click()
    expect(account.header.get_by_role("button", name="Sign in")).to_be_visible(timeout=15000)
    me = auth_page.request.get("/api/auth/me").json()
    assert me.get("data") is None, f"/api/auth/me still returns a session: {me}"
    auth_page.go_back()
    AccountPage(auth_page).open()
    expect(AccountPage(auth_page).signed_out_heading).to_be_visible()


@pytest.mark.tc("TC-106")
def test_agent_role_features():
    pytest.skip("Blocked: no agent account in the preview environment (workbook TC-106)")


@pytest.mark.live_write
@pytest.mark.tc("TC-042")
def test_cancel_booking_follows_policy():
    pytest.skip("Blocked: needs an existing booking to cancel and a published cancellation policy (TC-042)")
