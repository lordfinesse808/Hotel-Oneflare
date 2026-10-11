import pytest
from playwright.sync_api import expect

from pages.about_page import AboutPage
from pages.contact_page import ContactPage
from pages.gallery_page import GalleryPage
from pages.home_page import HomePage


@pytest.mark.smoke
def test_home_page_loads(home: HomePage):
    home.expect_loaded()
    expect(home.hero_text).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("link,fragment", [
    ("Rooms", "/rooms"), ("Gallery", "/gallery"),
    ("About", "/about"), ("Contact", "/contact"),
])
def test_header_navigation(home: HomePage, link, fragment):
    home.go_to(link)
    home.expect_url_contains(fragment)


def test_explore_rooms_cta(home: HomePage):
    home.explore_rooms()
    home.expect_url_contains("/rooms")


def test_header_and_footer_present_on_every_page(page):
    for pg in (HomePage, GalleryPage, AboutPage, ContactPage):
        obj = pg(page).open()
        obj.expect_header_visible()
        expect(obj.footer_head_office.first).to_be_visible()


def test_search_box_starts_empty(home: HomePage):
    expect(home.search_box).to_be_empty()


def test_about_page_content(page):
    about = AboutPage(page).open()
    expect(about.about_text).to_be_visible()
    expect(about.locations).to_be_visible()


def test_contact_page_content(page):
    contact = ContactPage(page).open()
    expect(contact.intro).to_be_visible()
