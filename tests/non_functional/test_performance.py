"""Performance budgets: navigation timing, LCP, CLS, throttled network, skeletons, API latency under load."""

import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from playwright.sync_api import expect

from config.settings import ALLOW_LOAD_TESTS, PERF_DCL_MS, PERF_LCP_MS, PERF_LOAD_MS, PERF_TTFB_MS

PAGES = ["/", "/rooms", "/branches", "/gallery", "/about", "/contact"]

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

CLS_JS = """() => new Promise(resolve => {
  let cls = 0;
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) if (!e.hadRecentInput) cls += e.value;
  }).observe({ type: 'layout-shift', buffered: true });
  setTimeout(() => resolve(cls), 3000);
})"""

# Chrome DevTools "Slow 4G" preset
SLOW_4G = {
    "offline": False,
    "latency": 150,
    "downloadThroughput": 1.6 * 1024 * 1024 / 8,
    "uploadThroughput": 750 * 1024 / 8,
}


def _chromium_only(browser_name):
    if browser_name != "chromium":
        pytest.skip("Uses Chromium-only performance APIs / CDP")


@pytest.mark.perf
@pytest.mark.tc("TC-051")
@pytest.mark.parametrize("path", PAGES)
def test_navigation_timing_within_budget(page, path):
    page.goto(path, wait_until="load")
    t = page.evaluate(NAV_TIMING_JS)
    assert t["ttfb"] <= PERF_TTFB_MS, f"{path} TTFB {t['ttfb']:.0f}ms > {PERF_TTFB_MS}ms"
    assert t["dcl"] <= PERF_DCL_MS, f"{path} DCL {t['dcl']:.0f}ms > {PERF_DCL_MS}ms"
    assert t["load"] <= PERF_LOAD_MS, f"{path} load {t['load']:.0f}ms > {PERF_LOAD_MS}ms"


@pytest.mark.perf
@pytest.mark.tc("TC-051")
@pytest.mark.parametrize("path", ["/", "/rooms"])
def test_largest_contentful_paint_within_budget(page, browser_name, path):
    _chromium_only(browser_name)
    page.goto(path, wait_until="load")
    lcp = page.evaluate(LCP_JS)
    assert lcp is not None, "LCP not reported"
    assert lcp <= PERF_LCP_MS, f"{path} LCP {lcp:.0f}ms > {PERF_LCP_MS}ms"


@pytest.mark.perf
@pytest.mark.tc("TC-051")
@pytest.mark.parametrize("path", ["/", "/rooms"])
def test_lcp_on_slow_4g(page, browser_name, path):
    """Nigeria network profile: Slow 4G must still paint the main content within the LCP budget."""
    _chromium_only(browser_name)
    cdp = page.context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", SLOW_4G)
    page.goto(path, wait_until="load", timeout=60000)
    lcp = page.evaluate(LCP_JS)
    assert lcp is not None and lcp <= PERF_LCP_MS, f"{path} LCP on Slow 4G {lcp}ms > {PERF_LCP_MS}ms"


@pytest.mark.perf
@pytest.mark.tc("TC-051")
def test_offscreen_images_are_lazy_loaded(page):
    page.goto("/gallery", wait_until="load")
    loading = page.locator("main img").evaluate_all("els => els.map(e => e.loading)")
    assert loading.count("lazy") >= len(loading) - 2, f"images not lazy loaded: {loading}"


@pytest.mark.perf
@pytest.mark.tc("TC-053")
@pytest.mark.parametrize(
    "path", ["/", pytest.param("/rooms", marks=pytest.mark.defect("BUG-013", reason="CLS ~0.16 on /rooms"))]
)
def test_cumulative_layout_shift(page, browser_name, path):
    _chromium_only(browser_name)
    page.goto(path, wait_until="load")
    cls = page.evaluate(CLS_JS)
    assert cls <= 0.1, f"{path} CLS {cls:.3f} > 0.1"


@pytest.mark.perf
@pytest.mark.tc("TC-052")
@pytest.mark.parametrize("path", ["/rooms/does-not-exist", "/rooms"])
def test_skeleton_loaders_always_resolve(page, browser_name, path):
    _chromium_only(browser_name)
    cdp = page.context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", SLOW_4G)
    page.goto(path, timeout=60000)
    expect(page.get_by_role("main").get_by_role("heading", level=1)).to_have_text(
        re.compile(r"\S"), timeout=15000
    )


@pytest.mark.perf
@pytest.mark.tc("TC-070")
@pytest.mark.parametrize("path", PAGES)
def test_no_console_errors_or_failed_requests(page, monitor, path):
    page.goto(path, wait_until="networkidle")
    assert not monitor.page_errors, f"JS exceptions: {monitor.page_errors}"
    assert not monitor.console_errors, f"Console errors: {monitor.console_errors}"
    assert not monitor.bad_responses, f"4xx/5xx responses: {monitor.bad_responses}"


@pytest.mark.perf
@pytest.mark.tc("TC-054")
@pytest.mark.skipif(
    not ALLOW_LOAD_TESTS, reason="Load test against shared preview - set ALLOW_LOAD_TESTS=true"
)
def test_rooms_search_p95_under_concurrent_load(api, site):
    """50 concurrent availability searches: p95 < 2 s and no 5xx."""
    url = f"/api/rooms?branchId={site.default_branch.id}&limit=50"

    def one(_):
        start = time.perf_counter()
        r = api.get(url)
        return r.status, (time.perf_counter() - start) * 1000

    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(pool.map(one, range(50)))
    statuses = [s for s, _ in results]
    p95 = statistics.quantiles([d for _, d in results], n=20)[-1]
    assert not [s for s in statuses if s >= 500], f"5xx under load: {statuses}"
    assert p95 < 2000, f"p95 {p95:.0f}ms >= 2000ms"
