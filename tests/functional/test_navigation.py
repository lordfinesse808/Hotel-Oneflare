"""Global header, footer, mobile menu, header search, policy pages and error pages."""

import re
from datetime import date

import pytest
from playwright.sync_api import expect

from pages.about_page import AboutPage
from pages.base_page import BasePage
from pages.branches_page import BranchesPage
from pages.contact_page import ContactPage
from pages.gallery_page import GalleryPage
from pages.home_page import HomePage
from pages.rooms_page import RoomsPage

HEADER_LINKS = [
    ("Home", "/"),
    ("Rooms", "/rooms"),
    ("Branches", "/branches"),
    ("Gallery", "/gallery"),
    ("About", "/about"),
    ("Contact", "/contact"),
]
FOOTER_LINKS = [
    "Home",
    "Rooms",
    "Gallery",
    "About us",
    "Contact",
    "Book now",
    "Privacy policy",
    "Terms & conditions",
    "Cancellation policy",
    "Manage a booking",
]
POLICY_PAGES = [
    ("/privacy-policy", "Privacy policy"),
    ("/terms", "Terms & conditions"),
    ("/cancellation-policy", "Cancellation policy"),
]


@pytest.mark.smoke
@pytest.mark.tc("TC-016", "TC-083")
def test_home_page_loads(home: HomePage):
    home.expect_loaded()
    expect(home.hero_text).to_be_visible()


@pytest.mark.smoke
@pytest.mark.tc("TC-043")
@pytest.mark.parametrize("link,path", HEADER_LINKS, ids=[n for n, _ in HEADER_LINKS])
def test_header_navigation(home: HomePage, link, path):
    home.go_to(link)
    expect(home.page).to_have_url(re.compile(re.escape(path) + r"(\?.*)?$"))
    expect(home.main).to_be_visible()


@pytest.mark.tc("TC-043")
@pytest.mark.parametrize("name", FOOTER_LINKS)
def test_footer_links_resolve_without_404(page, home: HomePage, name):
    href = home.footer_link(name).get_attribute("href")
    resp = page.request.get(href)
    assert resp.status == 200, f"Footer link '{name}' ({href}) returned HTTP {resp.status}"


@pytest.mark.tc("TC-043")
def test_logo_returns_home(page):
    gallery = GalleryPage(page).open()
    gallery.logo.click()
    expect(page).to_have_url(re.compile(r"/$"))


@pytest.mark.tc("TC-043")
def test_header_and_footer_present_on_every_page(page):
    for pg in (HomePage, BranchesPage, GalleryPage, AboutPage, ContactPage):
        obj = pg(page).open()
        obj.expect_header_visible()
        expect(obj.footer_head_office).to_be_visible()


@pytest.mark.tc("TC-010")
def test_footer_head_office_has_address(home: HomePage):
    expect(home.footer_head_office).to_have_text(re.compile(r"Head office\s*·\s*\S.{5,}"))


@pytest.mark.tc("TC-010")
@pytest.mark.defect("BUG-006")
def test_footer_branch_contacts_have_phone_and_email(home: HomePage):
    expect(home.footer_contact_items).to_have_count(5)
    for item in home.footer_contact_items.all():
        text = item.inner_text()
        assert re.search(r"\+?\d[\d\s]{6,}", text), f"No phone in footer entry: {text!r}"
        assert "@" in text, f"No email in footer entry: {text!r}"


@pytest.mark.tc("TC-019")
def test_footer_branch_list_complete_and_matches_contact_tabs(page, site):
    home = HomePage(page).open()
    expect(home.footer_contact_items).to_have_count(len(site.branches))
    footer_cities = [i.inner_text().splitlines()[0].strip() for i in home.footer_contact_items.all()]
    contact = ContactPage(page).open()
    for city in footer_cities:
        expect(contact.branch_tab(city)).to_be_visible()


@pytest.mark.tc("TC-087")
def test_footer_legal_line(home: HomePage):
    expect(home.footer_legal).to_have_text(re.compile(rf"© {date.today().year} .+ Limited\. RC \d+\."))


@pytest.mark.tc("TC-017")
@pytest.mark.security
def test_footer_does_not_advertise_staff_console(home: HomePage):
    expect(home.footer.get_by_role("link", name=re.compile("staff|HMS console", re.I))).to_have_count(0)


@pytest.mark.mobile
@pytest.mark.tc("TC-086")
def test_mobile_hamburger_menu(mobile_page):
    base = BasePage(mobile_page).open("/")
    base.expect_on_screen(base.mobile_menu, on=False)
    base.menu_toggle.click()
    base.expect_on_screen(base.mobile_menu, on=True)
    for name, _ in HEADER_LINKS:
        expect(base.mobile_menu.get_by_role("link", name=name, exact=True)).to_be_visible()
    expect(base.mobile_menu.get_by_role("link", name="Book now")).to_be_visible()
    expect(base.mobile_menu.get_by_role("button", name="Sign in")).to_be_visible()
    base.close_menu.click()
    base.expect_on_screen(base.mobile_menu, on=False)


@pytest.mark.mobile
@pytest.mark.tc("TC-086")
def test_mobile_menu_link_navigates(mobile_page):
    base = BasePage(mobile_page).open("/")
    base.menu_toggle.click()
    base.mobile_menu.get_by_role("link", name="Gallery", exact=True).click()
    expect(mobile_page).to_have_url(re.compile(r"/gallery"))


@pytest.mark.tc("TC-044")
def test_search_box_starts_empty(home: HomePage):
    expect(home.search_box).to_be_empty()


@pytest.mark.tc("TC-044")
def test_header_search_returns_relevant_results(page, home: HomePage, site):
    home.search_box.fill("Deluxe")
    home.search_box.press("Enter")
    expect(page).to_have_url(re.compile(r"/rooms\?.*q=Deluxe"))
    # Same query for a party the default branch can host (1 adult): only Deluxe rooms are listed
    rooms = RoomsPage(page).open(branch_id=site.default_branch.id, adults=1, q="Deluxe")
    titles = rooms.card_titles()
    assert titles and all("Deluxe" in t for t in titles), titles


@pytest.mark.tc("TC-044")
@pytest.mark.defect(reason="header search keeps the default 2 adults, so no Benin room ever matches")
def test_header_search_from_home_finds_default_branch_room(page, home: HomePage):
    home.search_box.fill("Deluxe")
    home.search_box.press("Enter")
    expect(page.get_by_role("main").get_by_role("link", name=re.compile("Deluxe")).first).to_be_visible()


@pytest.mark.tc("TC-044")
def test_header_search_no_match_shows_empty_state(page, home: HomePage):
    home.search_box.fill("zzzz")
    home.search_box.press("Enter")
    expect(page).to_have_url(re.compile(r"q=zzzz"))
    expect(page.get_by_role("main").get_by_text(re.compile(r'No rooms match "zzzz"'))).to_be_visible()


@pytest.mark.tc("TC-069")
@pytest.mark.parametrize("path,heading", POLICY_PAGES, ids=[p for p, _ in POLICY_PAGES])
def test_policy_pages_load(page, path, heading):
    resp = page.goto(path)
    assert resp.status == 200
    expect(page.get_by_role("main").get_by_role("heading", level=1)).to_have_text(heading)


@pytest.mark.tc("TC-069")
@pytest.mark.defect("BUG-020")
@pytest.mark.parametrize("path", [p for p, _ in POLICY_PAGES])
def test_policy_pages_publish_full_policy(page, path):
    """Pages exist now but only hold an interim 'hasn't published ... yet' notice."""
    page.goto(path)
    expect(page.get_by_role("main")).not_to_contain_text(re.compile(r"hasn't published", re.I))


@pytest.mark.tc("TC-060")
def test_unknown_url_shows_branded_404(page):
    resp = page.goto("/xyz-not-here")
    assert resp.status == 404
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Page not found")).to_be_visible()
    expect(main.get_by_role("link", name="Back home")).to_have_attribute("href", "/")
    expect(page.get_by_role("banner")).to_be_visible()  # branded: site chrome is kept


@pytest.mark.tc("TC-061")
@pytest.mark.seo
def test_page_titles_are_unique(page):
    titles = {}
    for path in ["/", "/rooms", "/branches", "/gallery", "/about", "/contact", "/manage-booking"]:
        page.goto(path)
        titles[path] = page.title()
    assert all("Oneflare Grand Plaza" in t for t in titles.values()), titles
    assert len(set(titles.values())) == len(titles), f"Duplicate titles: {titles}"


@pytest.mark.tc("TC-061")
@pytest.mark.seo
def test_meta_descriptions_are_unique(page):
    descs = {}
    for path in ["/", "/rooms", "/contact"]:
        page.goto(path)
        descs[path] = page.locator('meta[name="description"]').get_attribute("content")
    assert all(d and len(d) > 20 for d in descs.values()), descs
    assert len(set(descs.values())) == len(descs), f"Duplicate meta descriptions: {descs}"
