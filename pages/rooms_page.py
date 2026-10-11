"""Rooms listing: date pickers, branch select, price slider, room-type filters, result cards."""
import re
import time

from playwright.sync_api import Page, expect

from pages.base_page import BasePage

COUNT_RE = re.compile(r"(\d+)\s+room types?")  # captures N from "24 room types at Oneflare"


class RoomsPage(BasePage):
    path = "/rooms"

    def __init__(self, page: Page):
        super().__init__(page)
        self.check_in = page.get_by_role("textbox", name="Check in")
        self.check_out = page.get_by_role("textbox", name="Check out")
        self.price_slider = page.get_by_role("slider")
        self.branch_select = page.get_by_label(re.compile("Branch"))
        self.filters = page.get_by_role("complementary")  # the <aside> filter panel
        self.results_heading = page.get_by_role("heading", name=COUNT_RE)
        self.view_details_links = page.get_by_role("link", name="View details")
        self.select_room_links = page.get_by_role("link", name="Select room")

    # ---------- reading state ----------
    def room_count(self) -> int:
        expect(self.results_heading).to_be_visible()
        return int(COUNT_RE.search(self.results_heading.inner_text()).group(1))

    def wait_for_count(self, predicate, timeout_s: float = 5.0) -> int:
        """Poll until predicate(count) is True (results re-render async after filters)."""
        deadline = time.monotonic() + timeout_s
        count = self.room_count()
        while not predicate(count) and time.monotonic() < deadline:
            self.page.wait_for_timeout(150)  # short poll interval, bounded by the deadline
            count = self.room_count()
        return count

    # ---------- actions ----------
    def set_max_price(self, value: int) -> None:
        self.price_slider.fill(str(value))  # fill() works on <input type=range>

    def slider_bounds(self) -> tuple[int, int]:
        return (int(self.price_slider.get_attribute("min")),
                int(self.price_slider.get_attribute("max")))

    def select_branch(self, value: str) -> None:
        self.branch_select.select_option(value)

    def room_type_checkbox(self, name: str):
        return self.filters.get_by_role("checkbox", name=name)

    def toggle_room_type(self, name: str, on: bool = True) -> None:
        box = self.room_type_checkbox(name)
        box.check() if on else box.uncheck()

    def open_first_room(self):
        from pages.room_detail_page import RoomDetailPage  # local import avoids circular import
        self.view_details_links.first.click()
        return RoomDetailPage(self.page)
