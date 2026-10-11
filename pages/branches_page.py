import re

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class BranchesPage(BasePage):
    path = "/branches"

    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = self.main.get_by_role("heading", level=1)
        self.branch_headings = self.main.get_by_role("heading", level=2).filter(
            has_text="Oneflare Grand Plaza -"
        )
        self.see_rooms_links = self.main.get_by_role("link", name=re.compile(r"^See rooms at "))
        self.contact_links = self.main.get_by_role("link", name="Contact this branch")

    def card(self, branch_name: str) -> Locator:
        """The smallest element that holds the branch heading AND its 'Contact this branch' link."""
        heading = self.page.get_by_role("heading", name=branch_name, exact=True)  # relative to each div
        return (
            self.main.locator("div, article, section, li")
            .filter(has=heading)
            .filter(has=self.page.get_by_role("link", name="Contact this branch"))
            .last
        )

    def see_rooms(self, branch_name: str) -> Locator:
        return self.main.get_by_role("link", name=f"See rooms at {branch_name}")
