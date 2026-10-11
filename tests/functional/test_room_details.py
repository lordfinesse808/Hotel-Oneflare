import pytest
from playwright.sync_api import expect


@pytest.fixture
def detail(rooms):
    d = rooms.open_first_room()
    d.expect_loaded()
    return d


def test_dates_are_carried_over(rooms):
    chosen_in = rooms.check_in.input_value()    # read dates BEFORE leaving the list page
    chosen_out = rooms.check_out.input_value()
    detail = rooms.open_first_room()
    detail.expect_loaded()
    expect(detail.check_in).to_have_value(chosen_in)
    expect(detail.check_out).to_have_value(chosen_out)


def test_price_and_total_visible(detail):
    expect(detail.price_per_night).to_be_visible()
    expect(detail.total).to_be_visible()


def test_unpaid_pay_at_hotel_notice(detail):
    expect(detail.unpaid_notice).to_be_visible()


def test_back_to_rooms_via_nav(detail):
    detail.go_to("Rooms")
    detail.expect_url_contains("/rooms")
