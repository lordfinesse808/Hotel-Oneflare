"""Room detail page: content, dates, steppers, pricing, breadcrumb, not-found state."""

import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from pages.room_detail_page import RoomDetailPage, naira
from pages.rooms_page import RoomsPage

FUTURE = date.today() + timedelta(days=30)


@pytest.fixture
def hotel_room(page, site) -> RoomDetailPage:
    """Hotel-level room (full content, full tax breakdown)."""
    d = RoomDetailPage(page).open_room(
        site.bookable_room["id"], checkIn=FUTURE, checkOut=FUTURE + timedelta(days=2)
    )
    d.expect_loaded()
    return d


@pytest.fixture
def branch_room(rooms: RoomsPage) -> RoomDetailPage:
    d = rooms.open_first_room()
    d.expect_loaded()
    return d


@pytest.mark.tc("TC-031", "TC-088")
def test_view_details_shows_full_room_info(hotel_room: RoomDetailPage):
    expect(hotel_room.title).not_to_be_empty()
    for label in ("Bed", "Room size", "Guest capacity"):
        assert hotel_room.fact(label), f"'{label}' is empty"
    expect(hotel_room.amenities_heading).to_be_visible()
    expect(hotel_room.house_rules_heading).to_be_visible()
    expect(hotel_room.price_per_night).to_be_visible()
    expect(hotel_room.continue_button).to_be_enabled()


@pytest.mark.tc("TC-031", "TC-088")
@pytest.mark.defect("BUG-030")
def test_branch_room_detail_sections_populated(branch_room: RoomDetailPage):
    assert branch_room.fact("Room size") not in ("", "Not listed"), "room size not listed"
    expect(branch_room.amenities_heading).to_be_visible(timeout=3000)
    expect(branch_room.house_rules_heading).to_be_visible(timeout=3000)


@pytest.mark.tc("TC-031", "TC-001")
@pytest.mark.defect("BUG-001")
def test_room_detail_has_photos(branch_room: RoomDetailPage):
    expect(branch_room.main.locator("img[alt]:not([alt=''])").first).to_be_visible(timeout=3000)


@pytest.mark.tc("TC-090")
def test_branch_room_breadcrumb_and_other_rooms_name_the_branch(branch_room: RoomDetailPage, site):
    branch = site.default_branch.name
    expect(branch_room.breadcrumb.get_by_role("link", name="Rooms")).to_be_visible()
    expect(branch_room.other_rooms_heading).to_have_text(f"Other rooms at {branch}")
    expect(branch_room.main.get_by_text(re.compile(rf"^{re.escape(branch)} · "))).to_be_visible()


@pytest.mark.tc("TC-090")
@pytest.mark.defect("BUG-030")
def test_breadcrumb_includes_branch(branch_room: RoomDetailPage, site):
    expect(branch_room.breadcrumb).to_contain_text(site.default_branch.city)


@pytest.mark.tc("TC-090")
def test_other_room_link_opens_that_room(branch_room: RoomDetailPage):
    link = branch_room.other_room_links.first
    href = link.get_attribute("href")
    link.click()
    expect(branch_room.page).to_have_url(re.compile(re.escape(href.split("?")[0])))


@pytest.mark.tc("TC-090")
@pytest.mark.defect("BUG-003")
def test_other_rooms_has_no_duplicates(branch_room: RoomDetailPage):
    """Benin lists 'Standard Room ₦25,000 / night' twice: same room type shown as separate rooms."""
    expect(branch_room.other_room_links.first).to_be_visible()
    labels = branch_room.other_room_links.all_inner_texts()
    assert len(labels) == len(set(labels)), f"duplicate 'other rooms': {labels}"


@pytest.mark.tc("TC-013")
def test_dates_are_carried_over(page, site):
    rooms = RoomsPage(page).open(
        branch_id=site.default_branch.id, adults=1, checkIn=FUTURE, checkOut=FUTURE + timedelta(days=3)
    )
    detail = rooms.open_first_room()
    detail.expect_loaded()
    expect(detail.check_in).to_have_value(str(FUTURE))
    expect(detail.check_out).to_have_value(str(FUTURE + timedelta(days=3)))


@pytest.mark.tc("TC-092")
def test_search_guest_count_carries_to_detail(page, site):
    lagos = site.branch("Lagos")
    rooms = RoomsPage(page).open(branch_id=lagos.id, adults=2)
    detail = rooms.open_first_room()
    detail.expect_loaded()
    expect(page).to_have_url(re.compile(r"adults=2"))
    assert detail.stepper_value("Adults") == 2


@pytest.mark.tc("TC-089")
def test_steppers_respect_capacity(hotel_room: RoomDetailPage, site):
    cap = site.bookable_room["capacity"]
    if cap["adults"] == 1:
        expect(hotel_room.stepper("Adults", "Increase")).to_be_disabled()
    expect(hotel_room.stepper("Adults", "Decrease")).to_be_disabled()  # never below 1 adult
    expect(hotel_room.stepper("Children", "Decrease")).to_be_disabled()  # never below 0 children
    if cap["children"] == 0:
        expect(hotel_room.stepper("Children", "Increase")).to_be_disabled()


@pytest.mark.tc("TC-062")
def test_check_out_picker_min_is_day_after_check_in(hotel_room: RoomDetailPage):
    expect(hotel_room.check_out).to_have_attribute("min", str(FUTURE + timedelta(days=1)))


@pytest.mark.tc("TC-062")
@pytest.mark.defect("BUG-014")
@pytest.mark.parametrize("offset", [-5, 0], ids=["before", "same-day"])
def test_continue_blocked_when_check_out_not_after_check_in(hotel_room: RoomDetailPage, offset):
    hotel_room.check_out.fill(str(FUTURE + timedelta(days=offset)))
    hotel_room.page.wait_for_timeout(500)
    expect(hotel_room.continue_button).to_be_disabled(timeout=2000)


@pytest.mark.tc("TC-063")
def test_stay_limit_is_enforced_by_picker(hotel_room: RoomDetailPage):
    max_out = hotel_room.check_out.get_attribute("max")
    assert max_out, "no maximum check-out date"
    assert (date.fromisoformat(max_out) - FUTURE).days <= 92


@pytest.mark.tc("TC-063")
@pytest.mark.defect("BUG-014")
def test_past_dates_from_url_are_rejected(page, site):
    detail = RoomDetailPage(page).open_room(
        site.bookable_room["id"], checkIn="2020-01-01", checkOut="2020-01-03"
    )
    detail.expect_loaded()
    detail.continue_button.click()
    page.wait_for_timeout(1500)
    assert "/booking" not in page.url, "past stay accepted and taken to /booking"


@pytest.mark.tc("TC-025", "TC-030")
def test_total_equals_nights_times_rate_plus_listed_charges(hotel_room: RoomDetailPage, site):
    block = hotel_room.price_block_text()
    nights = int(re.search(r"Room · (\d+) nights?", block).group(1))
    room_total = naira(re.search(r"Room · \d+ nights?\s*(₦[\d,]+)", block).group(1))
    assert room_total == nights * site.bookable_room["price"]
    amounts = [int(a.replace(",", "")) for a in re.findall(r"₦([\d,]+)", block)]
    total = hotel_room.total_amount()
    charges = amounts[: amounts.index(total)] if total in amounts else amounts[:-1]
    assert abs(sum(charges) - total) <= len(charges), f"lines {charges} do not add up to {total}"


@pytest.mark.tc("TC-068")
@pytest.mark.defect("BUG-019")
def test_fifth_night_free_offer_applied(page, site):
    page.goto("/")
    if not page.get_by_text(re.compile(r"fifth night", re.I)).count():
        pytest.skip("'fifth night on us' offer is no longer advertised on Home")
    detail = RoomDetailPage(page).open_room(
        site.bookable_room["id"], checkIn=FUTURE, checkOut=FUTURE + timedelta(days=5)
    )
    room_total = naira(re.search(r"Room · 5 nights\s*(₦[\d,]+)", detail.price_block_text()).group(1))
    assert room_total == 4 * site.bookable_room["price"]


@pytest.mark.tc("TC-097")
def test_unpaid_pay_at_hotel_notice(hotel_room: RoomDetailPage):
    expect(hotel_room.unpaid_notice).to_be_visible()


@pytest.mark.tc("TC-122")
def test_currency_format(hotel_room: RoomDetailPage):
    amounts = re.findall(r"₦[\d,.]+", hotel_room.main.inner_text())
    assert amounts
    bad = [a for a in amounts if not re.fullmatch(r"₦\d{1,3}(,\d{3})*", a)]
    assert not bad, f"non N#,##0 amounts: {bad}"


@pytest.mark.tc("TC-091", "TC-052")
def test_invalid_room_id_shows_not_found(page):
    detail = RoomDetailPage(page).open("/rooms/does-not-exist")
    expect(detail.not_found).to_be_visible(timeout=15000)
    expect(detail.back_to_rooms).to_be_visible()


@pytest.mark.tc("TC-091", "TC-060")
@pytest.mark.defect("BUG-037")
def test_invalid_room_id_returns_http_404(page):
    resp = page.goto("/rooms/does-not-exist")
    assert resp.status == 404


@pytest.mark.tc("TC-013")
def test_back_to_rooms_via_nav(branch_room: RoomDetailPage):
    branch_room.go_to("Rooms")
    branch_room.expect_url_contains("/rooms")
