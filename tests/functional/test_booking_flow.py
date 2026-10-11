import pytest
from playwright.sync_api import expect

from config.settings import ALLOW_BOOKING_SUBMIT
from pages.rooms_page import RoomsPage
from utils.data_factory import GuestData


@pytest.fixture
def guest_step(auth_page):
    """Logged-in user -> rooms -> first room -> guest-details step."""
    detail = RoomsPage(auth_page).open().open_first_room()
    detail.expect_loaded()
    booking = detail.continue_to_guest_details()
    booking.expect_loaded()
    return booking


@pytest.mark.smoke
def test_reach_guest_details_step(guest_step):
    expect(guest_step.heading).to_be_visible()
    expect(guest_step.total).to_be_visible()


def test_guest_details_can_be_filled(guest_step):
    guest = GuestData()
    guest_step.fill_guest(guest)
    expect(guest_step.guest_name).to_have_value(guest.full_name)
    expect(guest_step.guest_email).to_have_value(guest.email)


def test_consent_checkbox_can_be_ticked(guest_step):
    guest_step.accept_consent()
    expect(guest_step.consent).to_be_checked()


def test_back_to_room_returns_to_detail_page(guest_step):
    guest_step.back_to_room.click()
    expect(guest_step.page).to_have_url(r"**/rooms/**")


@pytest.mark.skipif(not ALLOW_BOOKING_SUBMIT,
                    reason="Creates a real booking. Set ALLOW_BOOKING_SUBMIT=true to enable.")
def test_complete_booking_end_to_end(guest_step):
    # The recording stops before the final step, so the exact button label is unknown.
    # Fill this in after recording the 'Review & book' screen with `playwright codegen`.
    pytest.skip("Record the final confirm step and implement it here.")
