# Oneflare Hotels - Playwright (Python) POM Suite

## Setup
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    playwright install --with-deps chromium

## Run
    pytest -m smoke                       # critical path
    pytest tests/functional -n 3          # functional regression
    pytest tests/non_functional           # perf, a11y, responsive, security
    pytest --browser firefox --headed     # other browser, visible
    pytest --base-url https://other-env   # other environment

Reports: `reports/report.html`, `reports/junit.xml`; traces/videos/screenshots of failures in `reports/artifacts/`
(open a trace with `playwright show-trace <trace.zip>`).

## Structure
    pages/          Page Objects (locators + actions, NO assertions about business rules)
    tests/          functional/ and non_functional/ (assertions live here)
    conftest.py     fixtures: page objects, session login via storage_state, console/network monitor
    config/         env-overridable settings + budgets
    ci/quality_gate.py   pass-rate / min-tests / duration gate over junit.xml
    .github/workflows/ci.yml

## CI quality gates (all must be green; mark `quality-gate` as the required check)
| Gate | Rule |
|---|---|
| 1 Static | ruff lint + format clean; test collection succeeds |
| 2 Smoke | 100% pass, >= 8 tests executed (chromium) |
| 3 Regression | >= 95% pass on chromium, firefox, webkit; <= 25 min |
| 4 Non-functional | 100% of enforced checks: perf budgets, axe critical/serious = 0, no horizontal overflow, HTTPS + HSTS |
| Hygiene | 1 automatic rerun max; xfail = known defect, tracked not hidden |

## Known gaps to close
- Final "confirm booking" step is not in the recording -> `test_complete_booking_end_to_end` is skipped.
- `xfail` tests mark defects seen in the recording (0 results for Standard Room / King bed filters, 24 vs 25 room count).
- Selectors are derived from your codegen and have not been run against the live site from this build environment.
- Use `@pytest.mark.tc("TC-001")` to link each test to your workbook's test-case IDs.
