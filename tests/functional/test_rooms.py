"""Rooms listing: search bar, branch scoping, cards, filters, price slider, empty states."""

import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from pages.rooms_page import RoomsPage
from utils.site_data import branch_rooms

TEST_DATA_RE = re.compile(r"\btest\s*room\b|testroom\d*|TestType|test bed|testbed|\bstring\b", re.I)


def _capacity(card_text: str) -> int:
    return int(re.search(r"Max (\d+) adults?", card_text).group(1))


# ---------- listing ----------
@pytest.mark.smoke
@pytest.mark.tc("TC-004")
def test_rooms_list_shows_results(rooms: RoomsPage):
    assert rooms.room_count() > 0
    expect(rooms.view_details_links.first).to_be_visible()


@pytest.mark.tc("TC-004")
def test_heading_count_equals_room_types_shown(rooms: RoomsPage):
    titles = rooms.card_titles()
    assert rooms.room_count() == len(titles) == len(set(titles)), (
        f"heading={rooms.room_count()} cards={titles}"
    )


@pytest.mark.tc("TC-005")
def test_no_duplicate_identical_room_cards(rooms: RoomsPage):
    texts = [re.sub(r"\d+ rooms? left", "", t).strip() for t in rooms.card_texts()]
    assert len(texts) == len(set(texts)), f"Duplicate cards: {texts}"


@pytest.mark.tc("TC-003")
@pytest.mark.parametrize("city", ["Benin City", "Lagos"])
def test_room_names_have_no_duplicated_word(page, site, city):
    rooms = RoomsPage(page).open(branch_id=site.branch(city).id, adults=1)
    bad = [t for t in rooms.card_titles() if re.search(r"\b(\w+) \1\b", t, re.I)]
    assert not bad, f"Duplicated words in titles: {bad}"


@pytest.mark.tc("TC-003")
@pytest.mark.defect("BUG-002")
def test_room_names_have_no_redundant_room_suffix(page, site):
    """Lagos cards read 'Classic47 Room', 'testroom2 Room', 'TestTypee Room' - type + ' Room' concatenated."""
    rooms = RoomsPage(page).open(branch_id=site.branch("Lagos").id, adults=1)
    api_names = {r["name"] for r in branch_rooms(page.request, site.branch("Lagos").id)}
    bad = [t for t in rooms.card_titles() if t not in api_names]
    assert not bad, f"Card titles that differ from the room names: {bad}"


@pytest.mark.tc("TC-001", "TC-056")
@pytest.mark.defect("BUG-001")
def test_every_room_card_shows_a_photo_with_alt(rooms: RoomsPage):
    for text, link in zip(rooms.card_texts(), rooms.view_details_links.all(), strict=True):
        card = link.locator("xpath=ancestor::*[.//img][1]")
        img = card.locator("img").first
        expect(img, f"no photo on card: {text.splitlines()[0]}").to_be_visible()
        assert (img.get_attribute("alt") or "").strip(), f"empty alt on {text.splitlines()[0]}"


@pytest.mark.tc("TC-002")
def test_layout_survives_blocked_images(page, site):
    page.route(re.compile(r".*\.(jpg|jpeg|png|webp)(\?.*)?$|/_next/image.*"), lambda r: r.abort())
    rooms = RoomsPage(page).open(branch_id=site.default_branch.id, adults=1)
    expect(rooms.view_details_links.first).to_be_visible()
    overflow = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"Layout broke without images (overflow {overflow}px)"


@pytest.mark.tc("TC-006")
def test_rooms_left_label_is_a_positive_inventory_count(rooms: RoomsPage):
    """Full check (label == HMS inventory, decrements after booking) needs back-office access: Blocked."""
    labels = rooms.main.get_by_text(re.compile(r"^\d+ rooms? left$")).all_inner_texts()
    assert labels and all(int(x.split()[0]) >= 1 for x in labels), labels


@pytest.mark.tc("TC-009")
def test_capacity_text_singular_and_plural(page, site):
    rooms = RoomsPage(page).open(branch_id=site.branch("Lagos").id, adults=1)
    text = rooms.main.inner_text()
    assert not re.search(r"\b1 (adults|children)\b", text), "singular count with plural noun"
    assert not re.search(r"\b([2-9]|\d{2,}) (adult|child)\b(?!ren)", text), "plural count with singular noun"


@pytest.mark.tc("TC-025")
def test_card_total_equals_nightly_rate_times_nights(page, site):
    check_in = date.today() + timedelta(days=10)
    for nights in (2, 3):
        rooms = RoomsPage(page).open(
            branch_id=site.default_branch.id,
            adults=1,
            checkIn=check_in,
            checkOut=check_in + timedelta(days=nights),
        )
        for text in rooms.card_texts():
            rate = int(re.search(r"₦([\d,]+) / night", text).group(1).replace(",", ""))
            m = re.search(rf"₦([\d,]+) for {nights} nights", text)
            assert m, f"no {nights}-night total on card: {text!r}"
            assert int(m.group(1).replace(",", "")) == rate * nights


# ---------- search bar ----------
@pytest.mark.tc("TC-065", "TC-018")
def test_default_dates_are_today_wat_and_two_nights(page):
    rooms = RoomsPage(page).open()
    today = page.evaluate("() => new Date().toLocaleDateString('en-CA', {timeZone: 'Africa/Lagos'})")
    expect(rooms.check_in).to_have_value(today)
    expect(rooms.check_out).to_have_value(str(date.fromisoformat(today) + timedelta(days=2)))


@pytest.mark.tc("TC-018")
def test_date_fields_are_native_date_pickers(rooms: RoomsPage):
    """Native <input type=date> renders in the visitor's locale, so the format is never ambiguous."""
    expect(rooms.check_in).to_have_attribute("type", "date")
    expect(rooms.check_out).to_have_attribute("type", "date")


@pytest.mark.tc("TC-020", "TC-064")
def test_past_check_in_is_blocked_by_picker(rooms: RoomsPage):
    today = rooms.page.evaluate("() => new Date().toLocaleDateString('en-CA', {timeZone: 'Africa/Lagos'})")
    expect(rooms.check_in).to_have_attribute("min", today)


@pytest.mark.tc("TC-020", "TC-064")
@pytest.mark.defect("BUG-015")
def test_typed_past_check_in_is_rejected(page, site):
    rooms = RoomsPage(page).open(branch_id=site.default_branch.id, adults=1)
    yesterday = date.today() - timedelta(days=1)
    rooms.search.search(check_in=yesterday, check_out=date.today() + timedelta(days=1))
    page.wait_for_timeout(1000)
    assert f"checkIn={yesterday}" not in page.url, "search ran with a past check-in"


@pytest.mark.tc("TC-021", "TC-064")
def test_check_out_picker_min_is_after_check_in(rooms: RoomsPage):
    check_in = date.today() + timedelta(days=5)
    rooms.check_in.fill(str(check_in))
    expect(rooms.check_out).to_have_attribute("min", str(check_in + timedelta(days=1)))


@pytest.mark.tc("TC-021", "TC-064")
@pytest.mark.defect("BUG-014", "BUG-015")
@pytest.mark.parametrize("offset", [-2, 0], ids=["inverted", "same-day"])
def test_check_out_on_or_before_check_in_is_rejected(page, site, offset):
    rooms = RoomsPage(page).open(branch_id=site.default_branch.id, adults=1)
    check_in = date.today() + timedelta(days=5)
    rooms.search.search(check_in=check_in, check_out=check_in + timedelta(days=offset))
    page.wait_for_timeout(1000)
    assert f"checkOut={check_in + timedelta(days=offset)}" not in page.url, "search ran with invalid range"


@pytest.mark.tc("TC-024")
def test_guest_selector_limits(rooms: RoomsPage):
    assert rooms.search.guest_options() == ["1 adult"] + [f"{n} adults" for n in range(2, 7)]


@pytest.mark.tc("TC-007", "TC-008", "TC-024")
@pytest.mark.parametrize("adults", [1, 2, 3])
def test_guest_search_hides_rooms_below_capacity(page, site, adults):
    rooms = RoomsPage(page).open(branch_id=site.branch("Lagos").id, adults=adults)
    caps = [_capacity(t) for t in rooms.card_texts()]
    assert all(c >= adults for c in caps), f"{adults}-adult search listed rooms with capacity {caps}"
    if not caps:
        expect(rooms.empty_state).to_be_visible()


@pytest.mark.tc("TC-008")
def test_room_at_exact_capacity_is_listed(page, site):
    """Equal to max: listed. (Above max: hidden - covered by test_guest_search_hides_rooms_below_capacity.)"""
    rooms = RoomsPage(page).open(branch_id=site.default_branch.id, adults=1)
    assert any(_capacity(t) == 1 for t in rooms.card_texts())


@pytest.mark.tc("TC-022")
@pytest.mark.parametrize("city", ["Benin City", "Ikeja", "Lekki", "Owerri"])
def test_search_returns_rooms_for_chosen_branch_only(page, site, city):
    branch = site.branch(city)
    rooms = RoomsPage(page).open(branch_id=branch.id, adults=1)
    assert rooms.heading_branch() == branch.name
    for text in rooms.card_texts():
        assert city in text, f"card not from {city}: {text!r}"


@pytest.mark.tc("TC-022", "TC-076")
@pytest.mark.defect("BUG-025")
def test_lagos_lists_only_lagos_rooms(page, site):
    lagos = site.branch("Lagos")
    rooms = RoomsPage(page).open(branch_id=lagos.id, adults=1)
    foreign = [t.splitlines()[0] for t in rooms.card_texts() if "Lagos" not in t]
    assert not foreign, f"Lagos list contains rooms of other/unknown branches: {foreign}"


@pytest.mark.tc("TC-076", "TC-077")
@pytest.mark.defect("BUG-025")
def test_no_test_records_on_public_listing(page, site):
    for b in site.branches:
        text = RoomsPage(page).open(branch_id=b.id, adults=1).main.inner_text()
        assert not TEST_DATA_RE.search(text), f"test data on {b.city}: {TEST_DATA_RE.findall(text)}"


@pytest.mark.tc("TC-023")
def test_no_availability_message_when_nothing_fits(page, site):
    """No sold-out dataset exists in preview, so the 'nothing available' state is produced with 6 adults."""
    rooms = RoomsPage(page).open(branch_id=site.default_branch.id, adults=6)
    assert rooms.room_count() == 0
    expect(rooms.empty_state).to_be_visible()


@pytest.mark.tc("TC-108")
@pytest.mark.defect("BUG-032")
def test_branch_choice_persists_across_pages(page, site):
    lagos = site.branch("Lagos")
    rooms = RoomsPage(page).open()
    rooms.select_branch(lagos.id)
    rooms.search.check_availability.click()
    expect(page).to_have_url(re.compile(lagos.id))
    page.goto("/")
    rooms.go_to("Rooms")
    expect(rooms.branch_select).to_have_value(lagos.id)


# ---------- filters ----------
@pytest.mark.tc("TC-026")
def test_room_type_filter_and_untick_restores(rooms: RoomsPage):
    original = rooms.room_count()
    rooms.toggle("Deluxe Room", on=True)
    assert rooms.wait_for_count(lambda c: c < original) >= 1
    assert all("Deluxe" in t for t in rooms.card_titles())
    rooms.toggle("Deluxe Room", on=False)
    assert rooms.wait_for_count(lambda c: c == original) == original


@pytest.mark.tc("TC-027")
@pytest.mark.parametrize("bed", ["King", "Queen"])
def test_bed_type_filter(rooms: RoomsPage, bed):
    rooms.toggle(bed, on=True)
    count = rooms.wait_for_count(lambda c: c > 0)
    assert count > 0, f"{bed} filter returned 0 rooms"
    assert all(re.search(rf"\b{bed}\b", t) for t in rooms.card_texts())


@pytest.mark.tc("TC-028")
def test_amenities_filter_uses_and_logic(page, site):
    rooms = RoomsPage(page).open(branch_id=site.branch("Lagos").id, adults=1)
    rooms.toggle("Mini fridge", on=True)
    one = rooms.wait_for_count(lambda c: True)
    rooms.toggle("Work desk", on=True)
    both = rooms.wait_for_count(lambda c: c <= one)
    assert both <= one, "adding a second amenity must narrow (AND), not widen (OR) the results"


@pytest.mark.tc("TC-079")
def test_filter_options_come_from_branch_inventory(rooms: RoomsPage):
    titles = set(rooms.card_titles())
    options = rooms.filter_options("Room type")
    assert set(options) == titles, f"options {options} vs listed rooms {titles}"
    for opt in options:
        rooms.toggle(opt, on=True)
        assert rooms.wait_for_count(lambda c: c > 0) > 0, f"'{opt}' returns 0 results"
        rooms.toggle(opt, on=False)


@pytest.mark.tc("TC-029")
def test_incompatible_filters_show_empty_state(page, site):
    rooms = RoomsPage(page).open(branch_id=site.branch("Lagos").id, adults=1)
    rooms.toggle("Presidential", on=True)
    low, _ = rooms.slider_bounds()
    rooms.set_max_price(low)
    assert rooms.wait_for_count(lambda c: c == 0) == 0
    expect(rooms.empty_state).to_be_visible()


@pytest.mark.tc("TC-015")
def test_price_slider_filters_and_updates_count(rooms: RoomsPage):
    low, high = rooms.slider_bounds()
    at_high = rooms.room_count()
    rooms.set_max_price(low)
    at_low = rooms.wait_for_count(lambda c: c < at_high)
    assert 0 < at_low < at_high
    prices = [int(re.search(r"₦([\d,]+) / night", t).group(1).replace(",", "")) for t in rooms.card_texts()]
    assert all(p <= low for p in prices), prices


@pytest.mark.tc("TC-015")
@pytest.mark.defect("BUG-009")
def test_clear_filters_control_restores_all_rooms(rooms: RoomsPage):
    original = rooms.room_count()
    rooms.set_max_price(rooms.slider_bounds()[0])
    rooms.wait_for_count(lambda c: c < original)
    rooms.clear_filters.click(timeout=3000)
    assert rooms.wait_for_count(lambda c: c == original) == original


@pytest.mark.tc("TC-078")
def test_price_slider_range_matches_room_prices(page, site):
    for city in ("Benin City", "Lagos"):
        rooms = RoomsPage(page).open(branch_id=site.branch(city).id, adults=1)
        low, high = rooms.slider_bounds()
        prices = [
            int(re.search(r"₦([\d,]+) / night", t).group(1).replace(",", "")) for t in rooms.card_texts()
        ]
        assert low <= min(prices) and high >= max(prices), f"{city}: slider {low}-{high} vs prices {prices}"
        assert rooms.price_slider.input_value() == str(high) or int(rooms.price_slider.input_value()) >= max(
            prices
        )


@pytest.mark.tc("TC-030")
def test_amenities_list_scrolls_and_last_item_selectable(page, site):
    rooms = RoomsPage(page).open(branch_id=site.branch("Lagos").id, adults=1)
    options = rooms.filter_options("Amenities")
    last = rooms.filter_checkbox(options[-1])
    last.scroll_into_view_if_needed()
    last.check()
    expect(last).to_be_checked()


@pytest.mark.tc("TC-081")
@pytest.mark.defect(reason="workbook TC-081 Fail, no bug logged: filters not kept in URL/state")
def test_filters_survive_reload(rooms: RoomsPage):
    low, _ = rooms.slider_bounds()
    rooms.set_max_price(low)
    filtered = rooms.wait_for_count(lambda c: True)
    rooms.page.reload()
    assert rooms.wait_for_count(lambda c: c == filtered) == filtered, "filters lost on reload"


@pytest.mark.mobile
@pytest.mark.tc("TC-080")
def test_mobile_filter_drawer(mobile_page, site):
    rooms = RoomsPage(mobile_page).open(branch_id=site.default_branch.id, adults=1)
    original = rooms.room_count()
    rooms.filter_button.click()
    rooms.expect_on_screen(rooms.filter_drawer, on=True)
    rooms.filter_drawer.get_by_role("checkbox", name="Deluxe Room").check()
    expect(rooms.show_rooms_button).to_have_text(re.compile(r"Show 1 rooms?$"))
    rooms.show_rooms_button.click()
    rooms.expect_on_screen(rooms.filter_drawer, on=False)
    assert rooms.wait_for_count(lambda c: c < original) == 1


@pytest.mark.mobile
@pytest.mark.tc("TC-080", "TC-009")
@pytest.mark.defect(reason="drawer button reads 'Show 1 rooms' (plural with 1)")
def test_mobile_filter_button_singular(mobile_page, site):
    rooms = RoomsPage(mobile_page).open(branch_id=site.default_branch.id, adults=1)
    rooms.filter_button.click()
    rooms.filter_drawer.get_by_role("checkbox", name="Deluxe Room").check()
    expect(rooms.show_rooms_button).to_have_text("Show 1 room")


@pytest.mark.smoke
@pytest.mark.tc("TC-031", "TC-049")
def test_view_details_opens_room_page_with_dates(rooms: RoomsPage):
    detail = rooms.open_first_room()
    detail.expect_loaded()
    expect(detail.page).to_have_url(re.compile(r"checkIn=.*checkOut="))
