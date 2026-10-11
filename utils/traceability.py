"""pytest plugin: links tests to the QA workbook (TC-xxx / BUG-xxx) and writes a traceability report.

Markers (registered in pytest.ini):
    @pytest.mark.tc("TC-004", "TC-005")     test covers these workbook test cases
    @pytest.mark.defect("BUG-003")          test asserts EXPECTED behaviour that a known open bug breaks.
                                            It runs as xfail(strict=False) so the pipeline stays green
                                            while the bug is open; an XPASS means "bug looks fixed - retest".
                                            Run with --known-defects=fail to treat them as real failures.
    @pytest.mark.live_write                 creates real records (account/booking/message) - skipped unless
                                            ALLOW_LIVE_WRITES=true (workbook status "Blocked").
    @pytest.mark.needs_account              needs TEST_EMAIL/TEST_PASSWORD of an existing customer.

Output: reports/traceability.csv and reports/traceability.md (one row per test, TC and BUG ids, outcome).
Works with pytest-xdist: ids travel in report.user_properties.
"""
import csv
from collections import defaultdict
from pathlib import Path

import pytest

from config.settings import ALLOW_LIVE_WRITES, TEST_EMAIL, TEST_PASSWORD

REPORT_DIR = Path("reports")


def pytest_addoption(parser):
    parser.addoption(
        "--known-defects",
        choices=("xfail", "fail"),
        default="xfail",
        help="xfail (default): known open bugs are tracked as xfail; fail: treat them as failures (retest run).",
    )


def _ids(item, name):
    out = []
    for m in item.iter_markers(name):
        out.extend(str(a) for a in m.args)
    return sorted(set(out))


def pytest_collection_modifyitems(config, items):
    mode = config.getoption("--known-defects")
    for item in items:
        tcs, bugs = _ids(item, "tc"), _ids(item, "defect")
        item.user_properties.append(("tc", ",".join(tcs)))
        item.user_properties.append(("bugs", ",".join(bugs)))
        if bugs and mode == "xfail":
            item.add_marker(pytest.mark.xfail(reason=f"Known defect {', '.join(bugs)}", strict=False))
        if item.get_closest_marker("live_write") and not ALLOW_LIVE_WRITES:
            item.add_marker(pytest.mark.skip(reason="Creates live records - set ALLOW_LIVE_WRITES=true"))
        if item.get_closest_marker("needs_account") and not (TEST_EMAIL and TEST_PASSWORD):
            item.add_marker(pytest.mark.skip(reason="Set TEST_EMAIL and TEST_PASSWORD for an existing account"))


class _Collector:
    def __init__(self):
        self.rows = {}

    @pytest.hookimpl
    def pytest_runtest_logreport(self, report):
        props = dict(report.user_properties)
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            if hasattr(report, "wasxfail"):
                outcome = "XPASS (bug fixed? retest)" if report.passed else "XFAIL (known defect)"
            else:
                outcome = report.outcome.upper()
            self.rows[report.nodeid] = (props.get("tc", ""), props.get("bugs", ""), outcome)
        elif report.when == "teardown" and report.failed and report.nodeid in self.rows:
            tc, bugs, _ = self.rows[report.nodeid]
            self.rows[report.nodeid] = (tc, bugs, "ERROR (teardown)")

    @pytest.hookimpl
    def pytest_sessionfinish(self, session):
        if hasattr(session.config, "workerinput") or not self.rows:  # only the xdist controller writes
            return
        REPORT_DIR.mkdir(exist_ok=True)
        with open(REPORT_DIR / "traceability.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["test_case_ids", "linked_bugs", "outcome", "test"])
            for nodeid, (tc, bugs, outcome) in sorted(self.rows.items(), key=lambda kv: kv[1][0] or "~"):
                w.writerow([tc, bugs, outcome, nodeid])

        per_tc = defaultdict(list)
        for tc, _bugs, outcome in self.rows.values():
            for t in filter(None, tc.split(",")):
                per_tc[t].append(outcome)
        totals = defaultdict(int)
        for _tc, _bugs, outcome in self.rows.values():
            totals[outcome.split(" ")[0]] += 1
        lines = [
            "# Traceability report",
            "",
            "| Outcome | Tests |",
            "|---|---|",
            *[f"| {k} | {v} |" for k, v in sorted(totals.items())],
            "",
            f"Workbook test cases exercised: **{len(per_tc)}**",
            "",
            "| Test case | Outcomes |",
            "|---|---|",
            *[f"| {t} | {', '.join(sorted(set(o)))} |" for t, o in sorted(per_tc.items())],
        ]
        (REPORT_DIR / "traceability.md").write_text("\n".join(lines) + "\n")


def pytest_configure(config):
    config.pluginmanager.register(_Collector(), "oneflare-traceability-collector")
