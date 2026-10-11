"""Shared fixtures. pytest discovers this file automatically - no imports needed in tests."""

from dataclasses import dataclass, field

import pytest

from config.settings import BASE_URL, DEFAULT_TIMEOUT_MS, TEST_EMAIL, TEST_PASSWORD
from pages.account_page import AccountPage
from pages.auth_modal import AuthModal
from pages.home_page import HomePage
from pages.rooms_page import RoomsPage
from utils.site_data import SiteData, load_site_data

MOBILE = {"viewport": {"width": 375, "height": 812}, "is_mobile": True, "has_touch": True}


# ---------- browser/context defaults ----------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend (not replace) pytest-playwright's defaults for every browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-NG",
        "timezone_id": "Africa/Lagos",  # keeps 'today' stable: date pickers default to today in WAT
    }


@pytest.fixture(autouse=True)  # autouse = applied to every test without being requested
def _default_timeout(page):
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)


# ---------- tagging ----------
def pytest_collection_modifyitems(items):
    """Auto-apply markers from folder names so you never forget to tag a test."""
    for item in items:
        path = str(item.fspath)
        if "/tests/functional/" in path:
            item.add_marker(pytest.mark.functional)
        elif "/tests/non_functional/" in path:
            item.add_marker(pytest.mark.non_functional)


# ---------- test data from the live API ----------
@pytest.fixture(scope="session")
def api(playwright, base_url):
    """Browser-less HTTP client bound to the site under test."""
    ctx = playwright.request.new_context(base_url=(base_url or BASE_URL).rstrip("/"))
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def site(api) -> SiteData:
    return load_site_data(api)


# ---------- page-object fixtures ----------
@pytest.fixture
def home(page) -> HomePage:
    return HomePage(page).open()


@pytest.fixture
def rooms(page, site) -> RoomsPage:
    """Rooms list for the default branch with 1 adult (every branch room holds at least 1)."""
    return RoomsPage(page).open(branch_id=site.default_branch.id, adults=1)


@pytest.fixture
def mobile_page(browser, browser_context_args):
    ctx = browser.new_context(**{**browser_context_args, **MOBILE})
    page = ctx.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    yield page
    ctx.close()


# ---------- authentication ----------
@pytest.fixture(scope="session")
def auth_state(browser, browser_context_args, tmp_path_factory):
    """Sign in ONCE per session with the existing test account (TEST_EMAIL/TEST_PASSWORD) and save
    cookies/localStorage. Later tests reuse that file => logged in instantly (fast + stable)."""
    if not (TEST_EMAIL and TEST_PASSWORD):
        pytest.skip("Set TEST_EMAIL and TEST_PASSWORD (GitHub secrets) to run signed-in tests")
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS * 2)
    HomePage(page).open()
    name = AuthModal(page).sign_in(TEST_EMAIL, TEST_PASSWORD)
    state_file = tmp_path_factory.mktemp("auth") / "state.json"
    context.storage_state(path=str(state_file))
    context.close()
    return {"path": str(state_file), "email": TEST_EMAIL, "display_name": name}


@pytest.fixture
def auth_page(browser, browser_context_args, auth_state):
    """A Page that is already logged in. Each test gets its own isolated context."""
    context = browser.new_context(storage_state=auth_state["path"], **browser_context_args)
    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    yield page  # test runs here
    context.close()  # teardown


@pytest.fixture
def account(auth_page) -> AccountPage:
    return AccountPage(auth_page)


# ---------- runtime monitoring (used by non-functional tests) ----------
@dataclass
class PageMonitor:
    console_errors: list = field(default_factory=list)
    page_errors: list = field(default_factory=list)
    bad_responses: list = field(default_factory=list)


@pytest.fixture
def monitor(page) -> PageMonitor:
    m = PageMonitor()
    page.on("console", lambda msg: m.console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: m.page_errors.append(str(exc)))
    page.on(
        "response",
        lambda r: m.bad_responses.append((r.status, r.url))
        if r.status >= 400 and "favicon" not in r.url
        else None,
    )
    return m
