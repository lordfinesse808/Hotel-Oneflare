import pytest
from playwright.sync_api import expect

from pages.home_page import HomePage


@pytest.mark.smoke
def test_logged_in_header_shows_user(auth_page, auth_state):
    home = HomePage(auth_page).open()
    expect(home.user_menu(auth_state["user"].first_name)).to_be_visible()
    expect(home.sign_in_button).to_have_count(0)


def test_booking_history_reachable(auth_page, auth_state, account):
    HomePage(auth_page).open().user_menu(auth_state["user"].first_name).click()
    expect(account.breadcrumb).to_be_visible()
    account.open_booking_history()


def test_book_another_stay_goes_to_rooms(auth_page, auth_state, account):
    HomePage(auth_page).open().user_menu(auth_state["user"].first_name).click()
    account.open_booking_history()
    account.book_another_stay.click()
    account.expect_url_contains("/rooms")
