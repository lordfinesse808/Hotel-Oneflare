import pytest
from playwright.sync_api import expect

from config.settings import BRANCH_IDS
from pages.gallery_page import GalleryPage


@pytest.fixture
def gallery(page) -> GalleryPage:
    return GalleryPage(page).open()


def test_gallery_loads(gallery):
    expect(gallery.intro).to_be_visible()
    expect(gallery.branch_filter).to_be_visible()


@pytest.mark.parametrize("branch", list(BRANCH_IDS.values()))
def test_branch_filter_changes_without_error(gallery, branch):
    gallery.branch_filter.select_option(branch)
    expect(gallery.branch_filter).to_have_value(branch)


def test_category_filters(gallery):
    gallery.branch_filter.select_option("all")
    gallery.category("Restaurant").click()
    expect(gallery.image("The dining room")).to_be_visible()
    gallery.category("Swimming Pool").click()
    expect(gallery.image("The pool courtyard")).to_be_visible()
