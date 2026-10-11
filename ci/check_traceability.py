"""Static traceability check (no browser): every collected test must carry @pytest.mark.tc(...) and every
TC id it references must exist in docs/test_cases.csv (exported from the QA workbook).
Prints workbook coverage: which TC-xxx are automated and which are not (with the reason column).

    python ci/check_traceability.py            # exit 1 if a test is untagged or references an unknown TC
    python ci/check_traceability.py --list     # also print the uncovered workbook cases
"""

import csv
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


class _Grab:
    def __init__(self):
        self.items = []

    def pytest_collection_finish(self, session):
        self.items = session.items


def main() -> int:
    os.chdir(ROOT)
    grab = _Grab()
    rc = pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", "-o", "addopts=-p utils.traceability"],
                     plugins=[grab])
    if rc != 0:
        print("collection failed")
        return 1

    with open(ROOT / "docs" / "test_cases.csv", newline="") as f:
        cases = {r["Test Case ID"]: r for r in csv.DictReader(f)}

    untagged, unknown, covered = [], [], set()
    for item in grab.items:
        ids = [a for m in item.iter_markers("tc") for a in m.args]
        if not ids:
            untagged.append(item.nodeid)
        for tc in ids:
            (covered.add(tc) if tc in cases else unknown.append(f"{item.nodeid} -> {tc}"))

    missing = sorted(set(cases) - covered)
    print(f"tests={len(grab.items)} workbook_cases={len(cases)} automated={len(covered)} "
          f"coverage={len(covered) / len(cases) * 100:.1f}%")
    if missing:
        print("Not automated (see README 'Not automated' for why):")
        for tc in missing:
            c = cases[tc]
            print(f"  {tc} [{c['Type']}] {c['Title']} - automation candidate: {c['Automation Candidate']}")
    for n in untagged:
        print(f"UNTAGGED TEST: {n}")
    for n in unknown:
        print(f"UNKNOWN TC ID: {n}")

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"### Workbook coverage\n\n{len(covered)}/{len(cases)} test cases automated "
                    f"({len(covered) / len(cases) * 100:.1f}%) by {len(grab.items)} tests\n\n")
    return 1 if (untagged or unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
