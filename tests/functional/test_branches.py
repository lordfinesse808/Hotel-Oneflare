"""Branches page: cards, deep links to Rooms and Contact, naming consistency."""

import re

import pytest
from playwright.sync_api import expect

from pages.about_page import AboutPage
from pages.branches_page import BranchesPage
from pages.contact_page import ContactPage
from pages.home_page import HomePage
from pages.rooms_page import RoomsPage

NAME_RE = re.compile(r"^Oneflare Grand Plaza - [A-Z][\w ]+ Branch$")
ADDRESS_RE = re.compile(r"^\d+[A-Za-z]?(–\d+)? [A-Z][\w .'-]{2,60}$")


@pytest.fixture
def branches(page) -> BranchesPage:
    return BranchesPage(page).open()


@pytest.mark.tc("TC-071")
def test_every_branch_has_a_card_with_rooms_and_price(branches: BranchesPage, site):
    expect(branches.branch_headings).to_have_count(len(site.branches))
    for b in site.branches:
        card = branches.card(b.name)
        expect(card).to_contain_text(b.address)
        expect(card).to_contain_text(re.compile(r"[1-9]\d* available"))
        expect(card).to_contain_text(re.compile(r"₦[1-9][\d,]* / night"))


@pytest.mark.tc("TC-071")
@pytest.mark.defect("BUG-022")
def test_branch_cards_show_contacts_hours_and_photo(branches: BranchesPage, site):
    for b in site.branches:
        card = branches.card(b.name)
        text = card.inner_text()
        assert re.search(r"\+?\d[\d\s]{6,}", text) and "@" in text, f"{b.city}: no phone/email"
        expect(card.locator("img[alt]:not([alt=''])").first).to_be_visible(timeout=2000)


@pytest.mark.tc("TC-072")
@pytest.mark.parametrize("city", ["Benin City", "Ikeja", "Lagos", "Lekki", "Owerri"])
def test_see_rooms_opens_rooms_for_that_branch(page, branches: BranchesPage, site, city):
    b = site.branch(city)
    branches.see_rooms(b.name).click()
    expect(page).to_have_url(re.compile(rf"/rooms\?branchId={b.id}"))
    rooms = RoomsPage(page)
    expect(rooms.results_heading).to_contain_text(b.name)


@pytest.mark.tc("TC-073")
@pytest.mark.parametrize("city", ["Lekki", "Owerri"])
def test_contact_this_branch_selects_that_branch(page, branches: BranchesPage, site, city):
    b = site.branch(city)
    branches.card(b.name).get_by_role("link", name="Contact this branch").click()
    contact = ContactPage(page)
    expect(contact.routing).to_contain_text(b.name)
    expect(contact.main).to_contain_text(b.address)


@pytest.mark.tc("TC-074", "TC-075")
def test_branch_names_and_addresses_valid(site):
    for b in site.branches:
        assert NAME_RE.match(b.name), f"irregular branch name: {b.name!r}"
        assert ADDRESS_RE.match(b.address), f"malformed address: {b.address!r}"


@pytest.mark.tc("TC-074")
def test_branch_names_consistent_across_pages(page, site):
    pages = {
        "branches": BranchesPage(page).open().main.inner_text(),
        "about": AboutPage(page).open().main.inner_text(),
        "rooms selector": " ".join(RoomsPage(page).open().search.branch_options()),
    }
    home = HomePage(page).open()
    pages["home"] = home.main.inner_text()
    for b in site.branches:
        for where, text in pages.items():
            needle = b.address if where == "home" else b.name
            assert needle in text, f"{b.name}: '{needle}' missing on {where}"


@pytest.mark.tc("TC-075")
def test_lagos_branch_naming(site):
    lagos = site.branch("Lagos")
    assert lagos.name == "Oneflare Grand Plaza - Lagos Branch"
    assert not re.match(r"^\d+ \d+ ", lagos.address), f"double house number: {lagos.address}"
