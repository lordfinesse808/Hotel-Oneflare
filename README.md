# Oneflare Grand Plaza - Playwright (Python) QA Suite

Automated regression suite for <https://hotel-plaza-preview.vercel.app>, built from the QA workbook
*Oneflare_Bug_Reports_and_Test_Cases_WebSite_v3.xlsx* (123 test cases, 51 bugs).
Every workbook test case is linked to at least one automated test (`@pytest.mark.tc("TC-xxx")`).

## Setup
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    playwright install --with-deps chromium        # add firefox webkit for cross-browser runs
    cp .env.example .env                           # then fill TEST_EMAIL / TEST_PASSWORD

## Run
    pytest -m smoke                                # critical path (gate 2)
    pytest tests/functional -n 4                   # functional regression (gate 3)
    pytest tests/non_functional                    # perf, a11y, responsive, security, SEO (gate 4)
    pytest --browser firefox --headed              # other browser, visible
    pytest --base-url https://other-env            # other environment
    pytest --known-defects=fail                    # retest run: open bugs fail instead of xfail
    ALLOW_LIVE_WRITES=true pytest -m live_write    # creates real accounts/bookings/messages
    ALLOW_LOAD_TESTS=true pytest -k concurrent     # 50-request load test (TC-054)
    python ci/check_traceability.py                # workbook coverage, no browser needed
    python ci/discover.py                          # dump ARIA snapshots to re-derive selectors

Reports land in `reports/`: `report.html`, `junit.xml`, `traceability.csv|md`, and traces/videos/screenshots
of failures in `reports/artifacts/` (open a trace with `playwright show-trace <trace.zip>`).

## Structure
    pages/                 Page Objects (locators + actions, no business assertions)
      base_page.py         header, footer, mobile menu, navigation helpers (inherited by all pages)
      search_widget.py     Branch / dates / guests search bar shared by Home and Rooms
      home, rooms, room_detail, booking, auth_modal, account, manage_booking,
      branches, gallery, about, contact
    tests/functional/      user-facing behaviour (auto-marked `functional`)
    tests/non_functional/  performance, accessibility, responsive, security, SEO (auto-marked)
    conftest.py            fixtures: live API data, page objects, mobile context, signed-in session
    config/settings.py     env-overridable settings, flags and budgets (.env locally, secrets in CI)
    utils/site_data.py     branches/rooms read from the public API - no hard-coded DB ids
    utils/traceability.py  pytest plugin: tc/defect/live_write/needs_account markers + traceability report
    ci/quality_gate.py     pass-rate / min-tests / duration gate over junit.xml (+ job summary)
    ci/check_traceability.py  every test tagged, every TC id valid, coverage of the workbook
    ci/discover.py         live-site ARIA discovery used to build and maintain selectors
    docs/test_cases.csv    workbook test cases (source of truth for traceability)
    .github/workflows/     ci.yml (pipeline), discover.yml (selector maintenance)

## How workbook status maps to the suite
| Workbook | Suite |
|---|---|
| Pass | normal test, must pass |
| Fail (open bug) | `@pytest.mark.defect("BUG-xxx")` -> non-strict **xfail**; an **XPASS** means "looks fixed - retest" |
| Blocked (live data) | `@pytest.mark.live_write` -> skipped unless `ALLOW_LIVE_WRITES=true` |
| Needs an account | `@pytest.mark.needs_account` -> uses `TEST_EMAIL` / `TEST_PASSWORD` |
| Skipped / N/A | explicit `pytest.skip` with the workbook reason, so it stays visible in reports |

## CI/CD pipeline (`.github/workflows/ci.yml`)
Triggers: pull requests, pushes to `main`/`cl/**`/`feature/**`/`fix/**`, nightly 05:00 UTC, manual dispatch
(choose environment, `known_defects`, `allow_live_writes`), and every successful **deployment_status**
(Vercel preview builds are tested at their own URL).

| Gate | Job | Rule |
|---|---|---|
| 1 Static | `lint` | ruff lint + format clean; collection succeeds; every test linked to a valid TC |
| 2 Smoke | `smoke` | 100% pass, >= 8 tests (chromium) |
| 3 Regression | `regression` x chromium/firefox/webkit | >= 95% pass, >= 60 tests, <= 25 min each |
| 4 Non-functional | `non-functional` | 100% of enforced checks (perf budgets, axe critical/serious = 0, layout, headers) |
| Report | `report` | merges all reports, publishes workbook traceability to the run summary |
| Verdict | `quality-gate` | the single required status check for branch protection |

Hygiene: one automatic rerun maximum (`--reruns 1`); xfail = known defect, tracked not hidden.

### Repository settings to finish the setup
1. **Secrets** (Settings > Secrets and variables > Actions): `TEST_EMAIL`, `TEST_PASSWORD` for the customer
   test account. Without them the signed-in tests are reported as skipped.
2. **Variables** (optional): `BASE_URL`, `PERF_TTFB_MS`, `PERF_DCL_MS`, `PERF_LOAD_MS`, `PERF_LCP_MS`, `TEST_PHONE`.
3. **Branch protection** on `main`: require the `quality-gate` check.
4. **Vercel**: keep the GitHub integration on so deployments post `deployment_status` events.
