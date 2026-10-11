import pytest

from config.settings import PERF_DCL_MS, PERF_LCP_MS, PERF_LOAD_MS, PERF_TTFB_MS

PAGES = ["/", "/rooms", "/gallery", "/about", "/contact"]

NAV_TIMING_JS = """() => {
  const n = performance.getEntriesByType('navigation')[0];
  return { ttfb: n.responseStart, dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd };
}"""

LCP_JS = """() => new Promise(resolve => {
  new PerformanceObserver(list => {
    const e = list.getEntries(); resolve(e[e.length - 1].startTime);
  }).observe({ type: 'largest-contentful-paint', buffered: true });
  setTimeout(() => resolve(null), 5000);   // give up after 5s so the test cannot hang
})"""


@pytest.mark.perf
@pytest.mark.parametrize("path", PAGES)
def test_navigation_timing_within_budget(page, path):
    page.goto(path, wait_until="load")
    t = page.evaluate(NAV_TIMING_JS)
    assert t["ttfb"] <= PERF_TTFB_MS, f"{path} TTFB {t['ttfb']:.0f}ms > {PERF_TTFB_MS}ms"
    assert t["dcl"] <= PERF_DCL_MS, f"{path} DCL {t['dcl']:.0f}ms > {PERF_DCL_MS}ms"
    assert t["load"] <= PERF_LOAD_MS, f"{path} load {t['load']:.0f}ms > {PERF_LOAD_MS}ms"


@pytest.mark.perf
@pytest.mark.parametrize("path", ["/", "/rooms"])
def test_largest_contentful_paint_within_budget(page, browser_name, path):
    if browser_name != "chromium":
        pytest.skip("LCP API is Chromium-only")
    page.goto(path, wait_until="load")
    lcp = page.evaluate(LCP_JS)
    assert lcp is not None, "LCP not reported"
    assert lcp <= PERF_LCP_MS, f"{path} LCP {lcp:.0f}ms > {PERF_LCP_MS}ms"


@pytest.mark.perf
@pytest.mark.parametrize("path", PAGES)
def test_no_console_errors_or_failed_requests(page, monitor, path):
    page.goto(path, wait_until="networkidle")
    assert not monitor.page_errors, f"JS exceptions: {monitor.page_errors}"
    assert not monitor.console_errors, f"Console errors: {monitor.console_errors}"
    assert not monitor.bad_responses, f"4xx/5xx responses: {monitor.bad_responses}"
