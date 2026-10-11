"""Quality gate: reads one or more pytest JUnit XML files and exits 1 if thresholds are broken.
CI treats a non-zero exit code as a failed job, which blocks the merge.

Known defects (tests marked @pytest.mark.defect) are reported as xfail and do not count against the
pass rate; they are listed separately so they stay visible. When running in GitHub Actions the
summary is also written to the job summary page ($GITHUB_STEP_SUMMARY)."""

import argparse
import os
import sys
import xml.etree.ElementTree as ET


def collect(paths):
    stats = dict(tests=0, failed=0, skipped=0, xfail=0, duration=0.0)
    failures = []
    for path in paths:
        root = ET.parse(path).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        for s in suites:
            stats["tests"] += int(s.get("tests", 0))
            stats["failed"] += int(s.get("failures", 0)) + int(s.get("errors", 0))
            stats["skipped"] += int(s.get("skipped", 0))  # includes xfail outcomes
            stats["duration"] += float(s.get("time", 0))
            for case in s.iter("testcase"):
                sk = case.find("skipped")
                if sk is not None and sk.get("type") == "pytest.xfail":
                    stats["xfail"] += 1
                if case.find("failure") is not None or case.find("error") is not None:
                    failures.append(f"{case.get('classname')}::{case.get('name')}")
    return stats, failures


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("junit", nargs="+")  # path(s) to junit.xml
    p.add_argument("--min-pass-rate", type=float, default=100.0)  # % of executed tests that must pass
    p.add_argument("--min-tests", type=int, default=1)  # guards against an empty/mis-collected suite
    p.add_argument("--max-duration", type=float, default=1e9)  # seconds, total wall time of tests
    p.add_argument("--name", default="Quality gate")
    a = p.parse_args()

    st, failures = collect(a.junit)
    executed = st["tests"] - st["skipped"]
    rate = 100.0 if executed == 0 else (executed - st["failed"]) / executed * 100

    line = (
        f"tests={st['tests']} executed={executed} skipped={st['skipped'] - st['xfail']} "
        f"known_defects(xfail)={st['xfail']} failed={st['failed']} pass_rate={rate:.1f}% "
        f"duration={st['duration']:.0f}s"
    )
    print(line)

    problems = []
    if st["tests"] < a.min_tests:
        problems.append(f"only {st['tests']} tests ran (< {a.min_tests})")
    if rate < a.min_pass_rate:
        problems.append(f"pass rate {rate:.1f}% < {a.min_pass_rate}%")
    if st["duration"] > a.max_duration:
        problems.append(f"duration {st['duration']:.0f}s > {a.max_duration:.0f}s")

    for msg in problems:
        print(f"QUALITY GATE FAILED: {msg}")

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"### {a.name}: {'FAILED' if problems else 'PASSED'}\n\n`{line}`\n\n")
            f.write(f"Thresholds: pass rate >= {a.min_pass_rate}%, tests >= {a.min_tests}\n\n")
            for msg in problems:
                f.write(f"- :x: {msg}\n")
            if failures:
                f.write("\n<details><summary>Failed tests</summary>\n\n")
                f.write("\n".join(f"- `{t}`" for t in failures[:100]) + "\n\n</details>\n\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
