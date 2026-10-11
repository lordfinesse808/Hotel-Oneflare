"""Booking wizard: guest details validation, consent, review step, edit links, confirmation."""

import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from pages.booking_page import BookingPage
from pages.room_detail_page import RoomDetailPage
from pages.rooms_page import RoomsPage
from utils.data_factory import GuestData

FUTURE = date.today() + timedelta(days=45)


def _start(page, room_id: str, **params) -> BookingPage:
    detail = RoomDetailPage(page).open_room(
        room_id, checkIn=FUTURE, checkOut=FUTURE + timedelta(days=2), **params
    )
    detail.expect_loaded()
    booking = detail.continue_to_guest_details()
    booking.expect_loaded()
    return booking


@pytest.fixture
def guest_step(page, site) -> BookingPage:
    """Hotel-level room -> guest-details step."""
    return _start(page, site.bookable_room["id"])


@pytest.fixture
def branch_guest_step(rooms: RoomsPage) -> BookingPage:
    """Default branch -> first room via 'Select room' -> guest-details step."""
    rooms.select_room_links.first.click()
    detail = RoomDetailPage(rooms.page)
    detail.expect_loaded()
    booking = detail.continue_to_guest_details()
    booking.expect_loaded()
    return booking


@pytest.mark.smoke
@pytest.mark.tc("TC-013", "TC-049")
def test_select_room_opens_booking_step(branch_guest_step: BookingPage):
    expect(branch_guest_step.heading).to_be_visible()
    expect(branch_guest_step.total).to_be_visible()


@pytest.mark.smoke
@pytest.mark.tc("TC-013")
def test_reach_guest_details_step(guest_step: BookingPage):
    expect(guest_step.heading).to_be_visible()
    expect(guest_step.total).to_be_visible()


@pytest.mark.tc("TC-093")
def test_step_indicator(guest_step: BookingPage):
    expect(guest_step.steps.first).to_be_visible()
    guest_step.go_to_review(GuestData())
    expect(guest_step.main).to_contain_text(re.compile(r"Your stay\s*Details\s*3\s*Review & book"))


@pytest.mark.tc("TC-032")
def test_mandatory_guest_fields_validated(guest_step: BookingPage):
    guest_step.review_button.click()
    for err in (
        guest_step.name_error,
        guest_step.email_error,
        guest_step.phone_error,
        guest_step.consent_error,
    ):
        expect(err).to_be_visible()
    expect(guest_step.review_heading).to_have_count(0)


@pytest.mark.tc("TC-033")
def test_email_and_phone_format_validation(guest_step: BookingPage):
    guest_step.guest_name.fill("Ada Obi")
    guest_step.guest_email.fill("ada@")
    guest_step.guest_phone.fill("abc")
    guest_step.review_button.click()
    expect(guest_step.email_error).to_be_visible()
    expect(guest_step.phone_error).to_be_visible()


@pytest.mark.tc("TC-033")
@pytest.mark.parametrize(
    "phone", ["+2348012345678", "08012345678", "08112345678", "07012345678", "09012345678"]
)
def test_nigerian_phone_formats_accepted(guest_step: BookingPage, phone):
    guest_step.guest_phone.fill(phone)
    guest_step.review_button.click()
    expect(guest_step.phone_error).to_have_count(0)


@pytest.mark.tc("TC-094")
def test_consent_is_required(guest_step: BookingPage):
    guest_step.fill_guest(GuestData())
    guest_step.review_button.click()
    expect(guest_step.consent_error).to_be_visible()
    expect(guest_step.review_heading).to_have_count(0)


@pytest.mark.tc("TC-094", "TC-069")
def test_consent_privacy_link_works(page, guest_step: BookingPage):
    href = guest_step.privacy_link.get_attribute("href")
    assert page.request.get(href).status == 200


@pytest.mark.tc("TC-120", "TC-057")
@pytest.mark.defect("BUG-047")
@pytest.mark.parametrize(
    "name", ["<script>alert(1)</script>", "12345", "A"], ids=["script", "digits", "one-char"]
)
def test_guest_name_character_validation(guest_step: BookingPage, name):
    guest_step.fill_guest(GuestData(full_name=name)).accept_consent()
    guest_step.review_button.click()
    expect(guest_step.review_heading).to_have_count(0, timeout=3000)


@pytest.mark.tc("TC-057", "TC-120")
@pytest.mark.security
def test_script_in_guest_name_is_rendered_as_text(guest_step: BookingPage):
    fired = []
    guest_step.page.on("dialog", lambda d: (fired.append(d.message), d.dismiss()))
    guest_step.go_to_review(GuestData(full_name="<img src=x onerror=alert(1)>"))
    expect(guest_step.main.get_by_text("<img src=x onerror=alert(1)>")).to_be_visible()
    assert not fired, "script executed from guest name"


@pytest.mark.tc("TC-095", "TC-066")
def test_review_shows_stay_guest_and_price(guest_step: BookingPage):
    guest = GuestData()
    guest_step.go_to_review(guest)
    main = guest_step.main
    expect(main.get_by_text(guest.full_name, exact=True)).to_be_visible()
    expect(main.get_by_text(re.compile(re.escape(guest.email)))).to_be_visible()
    expect(main.get_by_text(re.compile(r"· 2 nights · 1 adult"))).to_be_visible()
    expect(guest_step.confirm_button).to_be_visible()


@pytest.mark.tc("TC-066")
def test_total_identical_on_detail_details_and_review(page, site):
    detail = RoomDetailPage(page).open_room(
        site.bookable_room["id"], checkIn=FUTURE, checkOut=FUTURE + timedelta(days=2)
    )
    detail.expect_loaded()
    on_detail = detail.total_amount()
    booking = detail.continue_to_guest_details()
    booking.expect_loaded()
    on_details = booking.total_amounts()
    booking.go_to_review(GuestData())
    on_review = booking.total_amounts()
    assert set(on_details) == {on_detail} and set(on_review) == {on_detail}, (
        on_detail,
        on_details,
        on_review,
    )


@pytest.mark.tc("TC-066", "TC-095")
@pytest.mark.defect("BUG-017")
def test_branch_room_review_shows_a_price(branch_guest_step: BookingPage):
    branch_guest_step.go_to_review(GuestData())
    expect(branch_guest_step.main.get_by_text(re.compile("Couldn't load a price estimate"))).to_have_count(0)


@pytest.mark.tc("TC-066")
@pytest.mark.defect("BUG-017")
def test_branch_room_total_is_final_not_estimate(branch_guest_step: BookingPage):
    expect(branch_guest_step.main.get_by_text(re.compile(r"\(estimate\)")).first).to_have_count(0)


@pytest.mark.tc("TC-067")
def test_tax_lines_are_guest_facing(guest_step: BookingPage):
    guest_step.go_to_review(GuestData())
    text = guest_step.main.inner_text()
    assert not re.search(r"\bComm\b", text), "internal 'Comm' line shown to guest"


@pytest.mark.tc("TC-067")
def test_tax_amounts_match_their_rates(page, site):
    detail = RoomDetailPage(page).open_room(
        site.bookable_room["id"], checkIn=FUTURE, checkOut=FUTURE + timedelta(days=2)
    )
    detail.expect_loaded()
    block = detail.price_block_text()
    room = int(re.search(r"Room · \d+ nights?\s*₦([\d,]+)", block).group(1).replace(",", ""))
    for name, rate, amount in re.findall(r"([A-Za-z][A-Za-z ]+?) ([\d.]+)%[^₦]*₦([\d,]+)", block):
        expected = room * float(rate) / 100
        assert abs(int(amount.replace(",", "")) - expected) <= 1, (
            f"{name.strip()} {rate}% of {room} != {amount}"
        )


@pytest.mark.tc("TC-095", "TC-062")
@pytest.mark.defect("BUG-049")
def test_edit_details_keeps_everything_incl_consent(guest_step: BookingPage):
    guest = GuestData()
    guest_step.go_to_review(guest)
    guest_step.edit_details.click()
    expect(guest_step.guest_name).to_have_value(guest.full_name)
    expect(guest_step.guest_email).to_have_value(guest.email)
    expect(guest_step.guest_phone).to_have_value(guest.phone)
    expect(guest_step.consent).to_be_checked()


@pytest.mark.tc("TC-095")
def test_back_to_guest_details_keeps_contact_data(guest_step: BookingPage):
    guest = GuestData()
    guest_step.go_to_review(guest)
    guest_step.back_to_details.click()
    expect(guest_step.guest_name).to_have_value(guest.full_name)
    expect(guest_step.guest_email).to_have_value(guest.email)
    expect(guest_step.guest_phone).to_have_value(guest.phone)


@pytest.mark.tc("TC-095", "TC-014", "TC-062")
def test_change_room_or_dates_keeps_dates(guest_step: BookingPage):
    guest_step.go_to_review(GuestData())
    guest_step.change_room.click()
    expect(guest_step.page).to_have_url(
        re.compile(rf"/rooms/.*checkIn={FUTURE}.*checkOut={FUTURE + timedelta(days=2)}")
    )


@pytest.mark.tc("TC-014")
def test_back_to_room_returns_to_detail_page(guest_step: BookingPage):
    guest_step.back_to_room.click()
    expect(guest_step.page).to_have_url(re.compile(r"/rooms/[0-9a-f-]{36}"))


@pytest.mark.tc("TC-014")
def test_browser_back_from_room_preserves_search_state(page, site):
    lekki = site.branch("Lekki")
    rooms = RoomsPage(page).open(
        branch_id=lekki.id, adults=1, checkIn=FUTURE, checkOut=FUTURE + timedelta(days=2)
    )
    rooms.select_room_links.first.click()
    RoomDetailPage(page).expect_loaded()
    page.go_back()
    expect(rooms.branch_select).to_have_value(lekki.id)
    expect(rooms.check_in).to_have_value(str(FUTURE))
    expect(rooms.guests).to_have_value("1")


@pytest.mark.tc("TC-097")
def test_unpaid_messaging_on_review(guest_step: BookingPage):
    guest_step.go_to_review(GuestData())
    expect(guest_step.unpaid_review_note).to_contain_text("no room is held until you confirm")


@pytest.mark.tc("TC-099")
def test_direct_booking_url_without_room_redirects(page):
    page.goto("/booking")
    expect(page).to_have_url(re.compile(r"/rooms"))


@pytest.mark.tc("TC-059")
@pytest.mark.security
def test_no_guest_pii_in_urls(page, site):
    guest = GuestData()
    urls = []
    page.on("request", lambda r: urls.append(r.url))
    booking = _start(page, site.bookable_room["id"])
    booking.go_to_review(guest)
    leaked = [u for u in urls if any(x in u for x in (guest.email, guest.phone.lstrip("+"), "Dane"))]
    assert not leaked, f"PII in URLs: {leaked}"


# ---------- live writes / not automatable here ----------
@pytest.mark.live_write
@pytest.mark.tc("TC-096", "TC-039")
def test_confirm_booking_creates_reservation(guest_step: BookingPage):
    guest_step.go_to_review(GuestData())
    guest_step.confirm_button.click()
    expect(guest_step.reference).to_be_visible(timeout=20000)


@pytest.mark.live_write
@pytest.mark.tc("TC-037")
def test_last_room_cannot_be_double_booked():
    pytest.skip("Needs approval to create two live bookings of the last unit (TC-037)")


@pytest.mark.tc("TC-038")
def test_room_hold_expires():
    pytest.skip("Hold time is not published and idling past it is not practical in CI (TC-038)")


@pytest.mark.tc("TC-034", "TC-035", "TC-036")
def test_online_payment_flows():
    pytest.skip("Not applicable: pay-at-hotel only, no online payment gateway (TC-034..036)")
