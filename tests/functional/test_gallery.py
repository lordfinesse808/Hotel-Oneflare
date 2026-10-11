"""Gallery: category filter, location filter, lightbox, content accuracy."""

import re

import pytest
from playwright.sync_api import expect

from pages.gallery_page import GalleryPage


@pytest.fixture
def gallery(page) -> GalleryPage:
    g = GalleryPage(page).open()
    expect(g.photos.first).to_be_visible()
    return g


@pytest.mark.tc("TC-109")
def test_gallery_loads(gallery: GalleryPage):
    expect(gallery.heading).to_be_visible()
    expect(gallery.location_filter).to_be_visible()
    assert gallery.photos.count() >= 4


@pytest.mark.tc("TC-109")
@pytest.mark.parametrize(
    "category,alt",
    [("Gym", "Fitness studio"), ("Restaurant", "The dining room"), ("Swimming Pool", "The pool courtyard")],
)
def test_category_filter_and_all_restores(gallery: GalleryPage, category, alt):
    total = gallery.photos.count()
    gallery.category(category).click()
    expect(gallery.image(alt)).to_be_visible()
    expect(gallery.photos).not_to_have_count(total)
    gallery.category("All").click()
    expect(gallery.photos).to_have_count(total)


@pytest.mark.tc("TC-110")
def test_location_filter_shows_photos_or_message(gallery: GalleryPage, site):
    for b in site.branches:
        gallery.location_filter.select_option(label=b.name)
        no_photos = gallery.main.get_by_text("No photos match this filter yet.")
        expect(gallery.photos.first.or_(no_photos)).to_be_visible()


@pytest.mark.tc("TC-110")
@pytest.mark.defect("BUG-034")
def test_every_branch_has_photos(gallery: GalleryPage, site):
    empty = []
    for b in site.branches:
        gallery.location_filter.select_option(label=b.name)
        gallery.page.wait_for_timeout(500)
        if gallery.photos.count() == 0:
            empty.append(b.city)
    assert not empty, f"No photos for: {empty}"


@pytest.mark.tc("TC-111")
@pytest.mark.defect(reason="regression: clicking a photo no longer opens a lightbox (workbook: Pass)")
def test_photo_lightbox_opens_navigates_and_closes(gallery: GalleryPage):
    gallery.photos.first.click(force=True)
    box = gallery.page.get_by_role("dialog").filter(has=gallery.page.get_by_role("img"))
    expect(box).to_be_visible(timeout=5000)
    first_alt = box.get_by_role("img").first.get_attribute("alt")
    gallery.page.keyboard.press("ArrowRight")
    expect(box.get_by_role("img").first).not_to_have_attribute("alt", first_alt)
    gallery.page.keyboard.press("Escape")
    expect(box).to_be_hidden()


@pytest.mark.tc("TC-112")
def test_gallery_intro_counts_match_branches(gallery: GalleryPage, site):
    expect(gallery.intro).to_contain_text(f"{len(site.branches)} houses")


@pytest.mark.tc("TC-112")
@pytest.mark.defect("BUG-035")
def test_no_duplicate_photos_and_room_photos_link_to_rates(gallery: GalleryPage):
    srcs = gallery.photos.evaluate_all("els => els.map(e => e.currentSrc || e.src)")
    assert len(srcs) == len(set(srcs)), "duplicate photos"
    room_photo = gallery.image("Deluxe Room")
    holder = room_photo.locator("xpath=ancestor::*[.//a or .//p][2]")
    expect(holder).to_contain_text(re.compile(r"₦[\d,]+"), timeout=2000)
