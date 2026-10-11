"""Availability search bar shared by Home and Rooms (Branch / Check in / Check out / Guests)."""

from datetime import date

from playwright.sync_api import Page


class SearchWidget:
    def __init__(self, page: Page):
        self.page = page
        main = page.get_by_role("main")
        self.branch = main.get_by_role("combobox", name="Branch")
        self.check_in = main.get_by_role("textbox", name="Check in")
        self.check_out = main.get_by_role("textbox", name="Check out")
        self.guests = main.get_by_role("combobox", name="Guests")
        self.check_availability = main.get_by_role("button", name="Check availability")

    def set_dates(self, check_in: date | str, check_out: date | str) -> "SearchWidget":
        self.check_in.fill(str(check_in))
        self.check_out.fill(str(check_out))
        return self

    def search(self, branch_id: str | None = None, check_in=None, check_out=None, adults: int | None = None):
        if branch_id:
            self.branch.select_option(branch_id)
        if check_in:
            self.check_in.fill(str(check_in))
        if check_out:
            self.check_out.fill(str(check_out))
        if adults:
            self.guests.select_option(str(adults))
        self.check_availability.click()
        return self

    def guest_options(self) -> list[str]:
        return self.guests.locator("option").all_inner_texts()

    def branch_options(self) -> list[str]:
        return [t.strip() for t in self.branch.locator("option").all_inner_texts()]
