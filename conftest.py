"""Shared fixtures. pytest discovers this file automatically - no imports needed in tests."""
from dataclasses import dataclass, field

import pytest

from config.settings import DEFAULT_TIMEOUT_MS
from pages.account_page import AccountPage
from pages.auth_modal import AuthModal
from pages.home_page import HomePage
from pages.rooms_page import RoomsPage
from utils.data_factory import UserData


# ---------- browser/context defaults ----------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend (not replace) pytest-playwright's defaults for every browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-NG",
        "timezone_id": "Africa/Lagos",  # keeps 'today' stable: date pickers default to today
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


# ---------- page-object fixtures ----------
@pytest.fixture
def home(page) -> HomePage:
    return HomePage(page).open()


@pytest.fixture
def rooms(page) -> RoomsPage:
    return RoomsPage(page).open()


# ---------- authentication ----------
@pytest.fixture(scope="session")
def auth_state(browser, browser_context_args, tmp_path_factory):
    """Register ONE user through the UI per session, save cookies/localStorage to a file.
    Later tests reuse that file => logged in instantly, no repeated sign-up (fast + stable)."""
    user = UserData.new("Sess")
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    HomePage(page).open()
    AuthModal(page).register(user)
    state_file = tmp_path_factory.mktemp("auth") / "state.json"
    context.storage_state(path=str(state_file))
    context.close()
    return {"path": str(state_file), "user": user}


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
