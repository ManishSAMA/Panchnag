"""`get_hindu_month` must answer from the lunar month it already resolved.

The lunar month containing a JD is by definition constant across the whole
interval between two new moons, yet every call re-ran the new-moon bisections
from scratch. In a one-year festival generation that is ~1100 calls resolving
to ~16 distinct months, and it dominated the profile of `/month-overview`
(88% of wall time).

These tests pin both halves of the contract: the answer must not change, and
the expensive search must not repeat once the interval is known.
"""

import panchang
from panchang import get_hindu_month


AYANAMSA = "Lahiri"
# 2026-01-01 .. arbitrary but fixed; any window spanning several lunar months works.
_START_JD = 2461041.5
_WINDOW_DAYS = 90


def test_cached_result_matches_the_uncached_result_every_day():
    """Correctness first: caching must not change a single day's answer."""
    panchang.clear_hindu_month_cache()

    mismatches = []
    for offset in range(_WINDOW_DAYS):
        jd = _START_JD + offset
        cached = get_hindu_month(jd, AYANAMSA)
        panchang.clear_hindu_month_cache()
        uncached = get_hindu_month(jd, AYANAMSA)
        if cached != uncached:
            mismatches.append((jd, cached, uncached))

    assert not mismatches, f"cache changed the answer on {len(mismatches)} day(s): {mismatches[:3]}"


def test_new_moon_search_runs_once_per_lunar_month(monkeypatch):
    """A whole lunar month of lookups must trigger one new-moon search."""
    panchang.clear_hindu_month_cache()

    calls = {"n": 0}
    real = panchang.find_new_moon_before

    def counting(jd, ayanamsa="Lahiri"):
        calls["n"] += 1
        return real(jd, ayanamsa)

    monkeypatch.setattr(panchang, "find_new_moon_before", counting)

    results = [get_hindu_month(_START_JD + offset, AYANAMSA) for offset in range(_WINDOW_DAYS)]

    distinct_months = len(set(results))
    assert distinct_months >= 3, "window should span several lunar months to be meaningful"
    assert calls["n"] <= distinct_months + 1, (
        f"{calls['n']} new-moon searches for {distinct_months} distinct months across "
        f"{_WINDOW_DAYS} days -- the interval cache is not holding"
    )


def test_cache_distinguishes_ayanamsas():
    """Two ayanamsas must not share a cached interval."""
    panchang.clear_hindu_month_cache()

    jd = _START_JD + 200
    lahiri = get_hindu_month(jd, "Lahiri")
    raman = get_hindu_month(jd, "Raman")

    panchang.clear_hindu_month_cache()
    raman_first = get_hindu_month(jd, "Raman")
    lahiri_second = get_hindu_month(jd, "Lahiri")

    assert lahiri == lahiri_second
    assert raman == raman_first


def test_cache_stays_bounded_over_a_long_run():
    """A multi-decade CLI run must not accumulate an unbounded interval list."""
    panchang.clear_hindu_month_cache()

    for offset in range(0, 4000, 25):
        get_hindu_month(_START_JD + offset, AYANAMSA)

    assert panchang.hindu_month_cache_size() <= panchang._HINDU_MONTH_CACHE_MAX
