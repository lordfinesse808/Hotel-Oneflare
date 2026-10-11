"""Quality gate: reads a pytest JUnit XML file and exits 1 if thresholds are broken.
CI treats a non-zero exit code as a failed job, which blocks the merge."""
import argparse
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("junit")                                   # path to junit.xml
    p.add_argument("--min-pass-rate", type=float, default=100.0)  # % of executed tests that must pass
    p.add_argument("--min-tests", type=int, default=1)        # guards against an empty/mis-collected suite
    p.add_argument("--max-duration", type=float, default=1e9) # seconds, total wall time of tests
    a = p.parse_args()

    root = ET.parse(a.junit).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    tests = sum(int(s.get("tests", 0)) for s in suites)
    failed = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)  # includes xfail outcomes
    duration = sum(float(s.get("time", 0)) for s in suites)
    executed = tests - skipped
    rate = 100.0 if executed == 0 else (executed - failed) / executed * 100

    print(f"tests={tests} executed={executed} skipped/xfail={skipped} failed={failed} "
          f"pass_rate={rate:.1f}% duration={duration:.0f}s")

    problems = []
    if tests < a.min_tests:
        problems.append(f"only {tests} tests ran (< {a.min_tests})")
    if rate < a.min_pass_rate:
        problems.append(f"pass rate {rate:.1f}% < {a.min_pass_rate}%")
    if duration > a.max_duration:
        problems.append(f"duration {duration:.0f}s > {a.max_duration:.0f}s")

    for msg in problems:
        print(f"QUALITY GATE FAILED: {msg}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
