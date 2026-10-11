"""Central configuration. Every value can be overridden by an environment variable,
so CI and local runs use the same code with different inputs.

Locally, values are read from a `.env` file in the repo root (gitignored, see `.env.example`).
In CI they come from GitHub Actions secrets / variables."""

import os
from pathlib import Path

try:  # python-dotenv is optional at runtime; CI injects real env vars
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:  # pragma: no cover
    pass


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


BASE_URL = os.getenv("BASE_URL", "https://hotel-plaza-preview.vercel.app").rstrip("/")

# Default action timeout (click/fill/etc.) in milliseconds.
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "10000"))

# Existing customer account used for sign-in tests (TC-040, TC-105, TC-107).
# Supplied via the TEST_EMAIL / TEST_PASSWORD secrets - never hard-code real credentials.
TEST_EMAIL = os.getenv("TEST_EMAIL", "")
TEST_PASSWORD = os.getenv("TEST_PASSWORD") or os.getenv("PASSWORD", "")
TEST_PHONE = os.getenv("TEST_PHONE", "+2348012345678")

# Tests that CREATE live records in the shared HMS (accounts, bookings, contact messages)
# are skipped unless explicitly enabled. Mirrors the "Blocked" status in the QA workbook.
ALLOW_LIVE_WRITES = _flag("ALLOW_LIVE_WRITES")
# Backwards-compatible alias used by the original booking test.
ALLOW_BOOKING_SUBMIT = _flag("ALLOW_BOOKING_SUBMIT") or ALLOW_LIVE_WRITES

# Concurrent-load test (TC-054) hits the shared preview with 50 parallel requests - opt-in only.
ALLOW_LOAD_TESTS = _flag("ALLOW_LOAD_TESTS")

# Performance budgets (milliseconds). Tune after you have a baseline.
PERF_TTFB_MS = int(os.getenv("PERF_TTFB_MS", "800"))
PERF_DCL_MS = int(os.getenv("PERF_DCL_MS", "3000"))
PERF_LOAD_MS = int(os.getenv("PERF_LOAD_MS", "5000"))
PERF_LCP_MS = int(os.getenv("PERF_LCP_MS", "4000"))
