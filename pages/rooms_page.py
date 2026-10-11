"""Rooms listing: search bar, filter panel (room type / bed / amenities / price), result cards."""

import re
import time

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage
from pages.search_widget import SearchWidget

COUNT_RE = re.compile(r"(\d+)\s+room types?\s+at\s+(.+)")  # "5 room types at Oneflare Grand Plaza - ..."


class RoomsPage(BasePage):
    path = "/rooms"

    def __init__(self, page: Page):
        super().__init__(page)
        self.search = SearchWidget(page)
        self.check_in = self.search.check_in
        self.check_out = self.search.check_out
        self.branch_select = self.search.branch
        self.guests = self.search.guests
        self.filters = self.main.get_by_role("complementary").first  # the <aside> filter panel
        self.price_slider = self.main.get_by_role("slider")
        self.clear_filters = self.main.get_by_role("button", name=re.compile("Clear (all )?filters", re.I))
        self.results_heading = self.main.get_by_role("heading", name=COUNT_RE)
        self.empty_state = self.main.get_by_text(re.compile("No rooms match your filters"))
        self.view_details_links = self.main.get_by_role("link", name="View details")
        self.select_room_links = self.main.get_by_role("link", name="Select room")
        # mobile filter drawer
        self.filter_button = self.main.get_by_role("button", name="Filter", exact=True)
        self.filter_drawer = page.get_by_role("dialog", name="Filters")
        self.show_rooms_button = self.filter_drawer.get_by_role("button", name=re.compile(r"^Show \d+ rooms?"))

    # ---------- navigation ----------
    def open(self, branch_id: str | None = None, adults: int | None = None, **params):
        query = {k: v for k, v in {"branchId": branch_id, "adults": adults, **params}.items() if v is not None}
        path = self.path + ("?" + "&".join(f"{k}={v}" for k, v in query.items()) if query else "")
        super().open(path)
        expect(self.results_heading).to_be_visible(timeout=20000)
        return self

    # ---------- reading state ----------
    def room_count(self) -> int:
        expect(self.results_heading).to_be_visible()
        return int(COUNT_RE.search(self.results_heading.inner_text()).group(1))

    def heading_branch(self) -> str:
        return COUNT_RE.search(self.results_heading.inner_text()).group(2).strip()

    def wait_for_count(self, predicate, timeout_s: float = 6.0) -> int:
        """Poll until predicate(count) is True (results re-render async after filters)."""
        deadline = time.monotonic() + timeout_s
        count = self.room_count()
        while not predicate(count) and time.monotonic() < deadline:
            self.page.wait_for_timeout(200)
            count = self.room_count()
        return count

    def card_titles(self) -> list[str]:
        """Room-name links (same href as View details, but the visible room name)."""
        names = []
        for link in self.view_details_links.all():
            href = link.get_attribute("href")
            title = self.main.locator(f'a[href="{href}"]').first.inner_text().strip()
            names.append(title)
        return names

    def card_texts(self) -> list[str]:
        out = []
        for link in self.view_details_links.all():
            out.append(link.evaluate(
                """a => { let n = a; while (n.parentElement && !/\\/ night/.test(n.innerText)) n = n.parentElement;
                          return n.innerText; }"""
            ))
        return out

    # ---------- actions ----------
    def set_max_price(self, value: int) -> None:
        self.price_slider.fill(str(value))  # fill() works on <input type=range>

    def slider_bounds(self) -> tuple[int, int]:
        return (int(float(self.price_slider.get_attribute("min"))), int(float(self.price_slider.get_attribute("max"))))

    def select_branch(self, value: str) -> None:
        self.branch_select.select_option(value)

    def filter_checkbox(self, name: str) -> Locator:
        return self.filters.get_by_role("checkbox", name=name, exact=True)

    def filter_options(self, group: str) -> list[str]:
        """Labels of the checkboxes under a filter heading ('Room type', 'Bed type', 'Amenities')."""
        heading = self.filters.get_by_role("heading", name=group, exact=True)
        return heading.evaluate(
            """h => { const out = []; let n = h.nextElementSibling;
                      while (n && !/^H[1-6]$/.test(n.tagName)) {
                        n.querySelectorAll('label').forEach(l => out.push(l.innerText.trim()));
                        if (n.tagName === 'LABEL') out.push(n.innerText.trim());
                        n = n.nextElementSibling; }
                      return out; }"""
        )

    def toggle(self, name: str, on: bool = True) -> None:
        box = self.filter_checkbox(name)
        if on:
            box.check()
        else:
            box.uncheck()

    def open_first_room(self):
        from pages.room_detail_page import RoomDetailPage  # local import avoids circular import

        self.view_details_links.first.click()
        return RoomDetailPage(self.page)
