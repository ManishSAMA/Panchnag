"""Sidereal-mode isolation across threads.

Every longitude lookup is two calls -- `set_sid_mode()` then `calc_ut()` --
which reads like a race: Flask serves requests on threads and
`/api/generate-db` runs generation on another, so a second thread changing the
mode in between would make the first read its longitude under someone else's
ayanamsa and return a plausible, silently wrong answer.

Measured, it does not happen. A deterministic interleave (thread A sets
Lahiri, thread B sets Raman, thread A then calls `calc_ut`) returns Lahiri's
value, and 45,000 contended lookups across three ayanamsas at a 1-microsecond
switch interval produced zero cross-talk. pyswisseph keeps the mode isolated.

These tests pin that guarantee rather than describe a defect: the isolation is
a property of the extension module, not of this codebase, so a pyswisseph
upgrade could silently remove it. Should that happen, the fix is a module-level
lock around the set-then-calc pair in `astronomy.get_planetary_longitude`.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import swisseph as swe

from astronomy import get_planetary_longitude


JD = 2461000.5  # arbitrary fixed instant; any epoch exercises the same path
_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


def test_interleaved_mode_change_does_not_leak_into_another_thread():
    """The tightest possible interleave: mode changed between set and calc."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    lahiri = swe.calc_ut(JD, swe.SUN, _FLAGS)[0][0]
    swe.set_sid_mode(swe.SIDM_RAMAN, 0, 0)
    raman = swe.calc_ut(JD, swe.SUN, _FLAGS)[0][0]
    assert abs(lahiri - raman) > 1.0, "ayanamsas must differ enough to detect a leak"

    mode_set, attacker_done = threading.Event(), threading.Event()
    observed = {}

    def victim():
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        mode_set.set()
        attacker_done.wait(timeout=5)
        observed["lon"] = swe.calc_ut(JD, swe.SUN, _FLAGS)[0][0]

    def attacker():
        mode_set.wait(timeout=5)
        swe.set_sid_mode(swe.SIDM_RAMAN, 0, 0)
        attacker_done.set()

    threads = [threading.Thread(target=victim), threading.Thread(target=attacker)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert abs(observed["lon"] - lahiri) < 1e-9, (
        "a concurrent set_sid_mode leaked into this thread's calc_ut -- "
        "add a lock around the set-then-calc pair in get_planetary_longitude"
    )


def test_contended_lookups_under_different_ayanamsas_stay_correct():
    """Sustained contention across all three supported ayanamsas."""
    expected = {
        (ayanamsa, body): get_planetary_longitude(JD, body, ayanamsa)
        for ayanamsa in ("Lahiri", "Raman", "Krishnamurti")
        for body in ("Sun", "Moon")
    }
    assert expected[("Lahiri", "Sun")] != expected[("Raman", "Sun")]

    def check(case):
        ayanamsa, body = case
        return case, get_planetary_longitude(JD, body, ayanamsa)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, list(expected) * 150))

    wrong = [
        (case, got, expected[case])
        for case, got in results
        if abs(got - expected[case]) > 1e-9
    ]

    assert not wrong, (
        f"{len(wrong)} of {len(results)} contended lookups returned another "
        f"thread's ayanamsa; first: {wrong[0]}"
    )
