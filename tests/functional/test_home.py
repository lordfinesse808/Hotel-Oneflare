"""Home page: hero, search widget, locations, 'Free for your dates', gallery and amenities sections."""

import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from pages.home_page import HomePage
from pages.rooms_page import RoomsPage

PLACEHOLDER_COPY = re.compile(r"whatever amount|lorem ipsum|placeholder|TODO|Live changing", re.I)


@pytest.mark.tc("TC-083")
def test_hero_copy_image_and_cta(home: HomePage):
    expect(home.hero_heading).to_have_text("Space to work, and to stop working")
    hero = home.hero_heading.locator("xpath=..")
    expect(hero).not_to_contain_text(PLACEHOLDER_COPY)
    home.explore_rooms()
    home.expect_url_contains("/rooms")


@pytest.mark.smoke
@pytest.mark.tc("TC-084")
def test_home_search_submits_branch_dates_and_guests(page, home: HomePage, site):
    owerri = site.branch("Owerri")
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=2)
    home.search.search(branch_id=owerri.id, check_in=check_in, check_out=check_out, adults=3)
    expect(page).to_have_url(
        re.compile(rf"/rooms\?.*branchId={owerri.id}.*checkIn={check_in}.*checkOut={check_out}.*adults=3")
    )
    rooms = RoomsPage(page)
    expect(rooms.branch_select).to_have_value(owerri.id)
    expect(rooms.check_in).to_have_value(str(check_in))
    expect(rooms.check_out).to_have_value(str(check_out))
    expect(rooms.guests).to_have_value("3")


@pytest.mark.tc("TC-016")
def test_locations_section_lists_every_branch(home: HomePage, site):
    expect(home.locations_heading).to_be_visible()
    for b in site.branches:
        expect(home.main.get_by_role("link", name=f"{b.city} {b.address}")).to_be_visible()


@pytest.mark.tc("TC-016")
def test_gallery_section_shows_images(home: HomePage):
    expect(home.gallery_heading).to_be_visible()
    section = home.gallery_heading.locator("xpath=ancestor::*[count(.//img) >= 3][1]")
    expect(section.get_by_role("img").first).to_be_visible()


@pytest.mark.tc("TC-016", "TC-085")
def test_amenities_section_lists_amenities(home: HomePage):
    expect(home.amenities_heading).to_be_visible()
    section = home.amenities_heading.locator("xpath=ancestor::*[count(.//p) >= 4][1]")
    titles = section.locator("p").all_inner_texts()
    assert len(titles) >= 6, f"Only {len(titles)} amenity lines: {titles}"  # was 1 ('Free WIFI') in BUG-010


@pytest.mark.tc("TC-016")
def test_free_for_your_dates_shows_room_cards(home: HomePage):
    expect(home.free_rooms_heading).to_be_visible()
    expect(home.view_details_links.first).to_be_visible()


@pytest.mark.tc("TC-082")
def test_free_for_your_dates_matches_selected_branch(page, home: HomePage, site):
    """Home cards must be the default branch's rooms at the same prices as /rooms (BUG-029)."""
    branch = site.default_branch
    expect(home.free_rooms_caption).to_contain_text(branch.name)
    home_prices = {int(p.replace(",", "")) for p in re.findall(r"₦([\d,]+) / night", home.main.inner_text())}
    rooms = RoomsPage(page).open(branch_id=branch.id, adults=1)
    list_prices = {int(p.replace(",", "")) for p in re.findall(r"₦([\d,]+) / night", rooms.main.inner_text())}
    assert home_prices and home_prices <= list_prices, f"home {home_prices} vs /rooms {list_prices}"


@pytest.mark.tc("TC-005", "TC-082")
@pytest.mark.defect("BUG-003")
def test_free_for_your_dates_has_no_duplicate_cards(home: HomePage):
    expect(home.view_details_links.first).to_be_visible()
    cards = []
    for link in home.view_details_links.all():
        cards.append(
            link.evaluate(
                "a => { let n = a; while (n.parentElement && !/\\/ night/.test(n.innerText)) n = n.parentElement;"
                " return n.innerText.replace(/\\d+ rooms? left/, '').trim(); }"
            )
        )
    dupes = {c.splitlines()[0] for c in cards if cards.count(c) > 1}
    assert not dupes, f"Identical room cards repeated on Home: {dupes}"
