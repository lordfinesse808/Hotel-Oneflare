"""Test data read from the site's own public API, so tests never hard-code DB ids that change per environment.

/api/branches  -> branch ids, names, addresses
/api/rooms     -> rooms (branchId == "" for hotel-level rooms, which are the bookable ones today)
"""

from dataclasses import dataclass, field

from playwright.sync_api import APIRequestContext


@dataclass
class Branch:
    id: str
    name: str
    city: str
    address: str
    raw: dict = field(repr=False, default_factory=dict)


@dataclass
class SiteData:
    branches: list[Branch]
    rooms: list[dict]  # unscoped catalogue (GET /api/rooms?limit=50)

    def branch(self, city: str) -> Branch:
        return next(b for b in self.branches if b.city.lower() == city.lower())

    @property
    def default_branch(self) -> Branch:
        return self.branch("Benin City")

    @property
    def hotel_rooms(self) -> list[dict]:
        """Rooms not tied to a branch. These open the full booking flow."""
        return [r for r in self.rooms if not r.get("branchId")]

    @property
    def bookable_room(self) -> dict:
        avail = [r for r in self.hotel_rooms if r.get("isAvailable", True)]
        return min(avail or self.hotel_rooms or self.rooms, key=lambda r: r["capacity"]["adults"])


def _data(resp):
    assert resp.ok, f"{resp.url} -> HTTP {resp.status}"
    body = resp.json()
    return body.get("data", body)


def load_site_data(request: APIRequestContext) -> SiteData:
    branches = [
        Branch(b["id"], b["name"], b.get("city", ""), b.get("address", ""), b)
        for b in _data(request.get("/api/branches"))
    ]
    rooms = _data(request.get("/api/rooms?limit=50"))
    rooms = rooms.get("items", rooms) if isinstance(rooms, dict) else rooms
    return SiteData(branches=branches, rooms=rooms)


def branch_rooms(request: APIRequestContext, branch_id: str) -> list[dict]:
    rooms = _data(request.get(f"/api/rooms?branchId={branch_id}&limit=50"))
    return rooms.get("items", rooms) if isinstance(rooms, dict) else rooms
