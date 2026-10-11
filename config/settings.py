"""Central configuration. Every value can be overridden by an environment variable,
so CI and local runs use the same code with different inputs."""
import os

# Default action timeout (click/fill/etc.) in milliseconds.
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "10000"))

# Credentials for accounts the suite CREATES. Never reuse a real password here.
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Str0ng!Pass#2026")
TEST_PHONE = os.getenv("TEST_PHONE", "+2348012345678")

# The recording ends before the final "confirm booking" step. Submitting creates
# real bookings on the preview site, so it is OFF unless explicitly enabled.
ALLOW_BOOKING_SUBMIT = os.getenv("ALLOW_BOOKING_SUBMIT", "false").lower() == "true"

# Performance budgets (milliseconds). Tune after you have a baseline.
PERF_TTFB_MS = int(os.getenv("PERF_TTFB_MS", "800"))
PERF_DCL_MS = int(os.getenv("PERF_DCL_MS", "3000"))
PERF_LOAD_MS = int(os.getenv("PERF_LOAD_MS", "5000"))
PERF_LCP_MS = int(os.getenv("PERF_LCP_MS", "4000"))

# Branch <select> option values captured in your codegen recording.
# They are DB ids, so they may change per environment - treat as test data.
BRANCH_IDS = {
    "option_a": "6f90d0d0-9cd4-44f9-b864-466ccbba7a22",
    "option_b": "411e63b9-cea4-4001-95fe-804f990bffb7",
}
