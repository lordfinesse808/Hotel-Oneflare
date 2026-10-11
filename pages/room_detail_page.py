import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage

MONEY_RE = re.compile(r"₦([\d,]+)")


def naira(text: str) -> int:
    """'₦56,250' -> 56250 (first amount in the string)."""
    return int(MONEY_RE.search(text).group(1).replace(",", ""))


class RoomDetailPage(BasePage):
    path = "/rooms/"  # real URL is /rooms/<uuid>?checkIn=..&checkOut=..&branchId=..

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = self.main.get_by_role("heading", level=1)
        self.not_found = self.main.get_by_role("heading", name="Room not found")
        self.back_to_rooms = self.main.get_by_role("link", name="Back to rooms")
        self.breadcrumb = self.main.get_by_role("navigation", name="Breadcrumb")
        self.check_in = self.main.locator("input[type=date]").nth(0)
        self.check_out = self.main.locator("input[type=date]").nth(1)
        self.price_per_night = self.main.get_by_text(re.compile(r"^₦[\d,]+ per night$"))
        self.total = self.main.get_by_text(re.compile(r"Total\s*₦[\d,]+")).first
        self.unpaid_notice = self.main.get_by_text("This booking is unpaid — pay at the hotel.")
        self.continue_button = self.main.get_by_role("button", name="Continue to guest details")
        self.amenities_heading = self.main.get_by_role("heading", name="What is in the room")
        self.house_rules_heading = self.main.get_by_role("heading", name="House rules")
        self.policy_link = self.main.get_by_role("link", name=re.compile("Read the full policy"))
        self.other_rooms_heading = self.main.get_by_role("heading", name=re.compile(r"^Other rooms"))
        self.validation_error = self.main.get_by_text(
            re.compile(
                r"(check-?out|departure).*(after|later)|at least 1 night|in the past|maximum|cannot", re.I
            )
        )

    def open_room(self, room_id: str, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        return self.open(f"/rooms/{room_id}" + (f"?{query}" if query else ""))

    def expect_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/rooms/[0-9a-f-]{36}"))
        expect(self.continue_button).to_be_visible(timeout=15000)

    def stepper(self, who: str, direction: str):
        """who: 'Adults'|'Children'; direction: 'Increase'|'Decrease'."""
        return self.main.get_by_role("button", name=f"{direction} {who}")

    def stepper_value(self, who: str) -> int:
        """Number shown between the -/+ buttons for 'Adults' or 'Children'."""
        text = self.stepper(who, "Decrease").evaluate("b => b.parentElement.innerText")
        return int(re.search(r"\d+", text).group(0))

    def fact(self, label: str) -> str:
        """Value shown under a fact label such as 'Bed', 'Room size', 'Guest capacity'."""
        return self.main.get_by_text(label, exact=True).first.evaluate(
            "e => (e.nextElementSibling && e.nextElementSibling.innerText || '').trim()"
        )

    def price_block_text(self) -> str:
        return self.total.evaluate(
            "e => { let n = e; while (n.parentElement && !/Room ·/.test(n.innerText)) n = n.parentElement;"
            " return n.innerText; }"
        )

    def total_amount(self) -> int:
        return naira(re.search(r"Total\s*(₦[\d,]+)", self.price_block_text()).group(1))

    def set_dates(self, check_in: str, check_out: str) -> None:
        self.check_in.fill(check_in)
        self.check_out.fill(check_out)

    def continue_to_guest_details(self):
        from pages.booking_page import BookingPage

        self.continue_button.click()
        return BookingPage(self.page)
