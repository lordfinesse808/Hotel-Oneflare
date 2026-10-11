"""Builds unique test data so tests never collide with each other or with old runs."""

import uuid
from dataclasses import dataclass

from config.settings import TEST_PHONE


@dataclass(frozen=True)  # frozen = immutable, so a test cannot accidentally mutate shared data
class UserData:
    full_name: str
    email: str
    phone: str
    password: str

    @property
    def first_name(self) -> str:
        # Header shows initials + first name (e.g. "JG John"), so tests need this.
        return self.full_name.split()[0]

    @classmethod
    def new(cls, first: str = "Qa") -> "UserData":
        token = uuid.uuid4().hex[:10]  # 10 random hex chars => unique email per call
        return cls(
            full_name=f"{first} Tester{token[:4]}",
            email=f"qa-{token}@maildrop.cc",  # maildrop.cc = disposable inbox domain
            phone=TEST_PHONE,
            password=f"Qa!{token}#Aa1",  # 16 chars: the site requires at least 12
        )


@dataclass(frozen=True)
class GuestData:
    full_name: str = "John Dane"
    phone: str = "+2348012345678"
    email: str = "guest-qa@maildrop.cc"
    notes: str = "Automated test booking - please ignore"
