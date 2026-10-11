import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from config.settings import BRANCH_IDS
from pages.rooms_page import RoomsPage


@pytest.mark.smoke
def test_rooms_list_shows_results(rooms: RoomsPage):
    assert rooms.room_count() > 0
    expect(rooms.view_details_links.first).to_be_visible()


def test_default_dates_are_today_and_two_nights(rooms: RoomsPage):
    today = date.today()
    expect(rooms.check_in).to_have_value(today.isoformat())
    expect(rooms.check_out).to_have_value((today + timedelta(days=2)).isoformat())


def test_lower_max_price_never_increases_results(rooms: RoomsPage):
    low, high = rooms.slider_bounds()
    rooms.set_max_price(high)
    at_high = rooms.wait_for_count(lambda c: True)
    rooms.set_max_price(low)
    at_low = rooms.wait_for_count(lambda c: c <= at_high)
    assert at_low <= at_high


@pytest.mark.parametrize("branch", list(BRANCH_IDS.values()))
def test_branch_select_updates_heading(rooms: RoomsPage, branch):
    rooms.select_branch(branch)
    expect(rooms.results_heading).to_contain_text("room types")


def test_filter_toggle_restores_original_count(rooms: RoomsPage):
    """Recording showed 24 -> filter -> back to 24 after un-ticking."""
    rooms.select_branch(BRANCH_IDS["option_b"])
    original = rooms.room_count()
    rooms.toggle_room_type("Standard Room", on=True)
    rooms.toggle_room_type("Standard Room", on=False)
    assert rooms.wait_for_count(lambda c: c == original) == original


@pytest.mark.xfail(reason="Observed in recording: ticking 'Standard Room' returned 0 room types "
                          "although a Standard Room exists. Verify vs bug sheet.", strict=False)
def test_standard_room_filter_returns_results(rooms: RoomsPage):
    rooms.select_branch(BRANCH_IDS["option_b"])
    rooms.toggle_room_type("Standard Room", on=True)
    assert rooms.wait_for_count(lambda c: c > 0) > 0


@pytest.mark.xfail(reason="Observed in recording: 'King bed' filter returned 0 room types.", strict=False)
def test_king_bed_filter_returns_results(rooms: RoomsPage):
    rooms.select_branch(BRANCH_IDS["option_b"])
    rooms.room_type_checkbox("King bed").check()
    assert rooms.wait_for_count(lambda c: c > 0) > 0


@pytest.mark.xfail(reason="Observed: heading showed 24 then 25 room types for the same branch "
                          "across visits. Confirm whether data or a defect.", strict=False)
def test_room_count_is_stable_between_visits(page):
    first = RoomsPage(page).open()
    first.select_branch(BRANCH_IDS["option_b"])
    n1 = first.room_count()
    second = RoomsPage(page).open()
    second.select_branch(BRANCH_IDS["option_b"])
    assert second.room_count() == n1


@pytest.mark.smoke
def test_view_details_opens_room_page(rooms: RoomsPage):
    detail = rooms.open_first_room()
    detail.expect_loaded()
    expect(detail.page).to_have_url(re.compile(r"checkIn=.*checkOut="))
