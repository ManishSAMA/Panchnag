"""The Panchang section's elements across one sunrise-to-sunrise day.

The app shows the Jain tithi, nakshatra, yoga and Moon Rashi as "current
until T" then "next until T'", every Karana of the day, the Sun's Rashi and
the gata (days since the Sun entered its Rashi, the Sankranti day being 1).
Design: plans/panchang-section-and-pothi.md.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from functools import cache

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from day_elements import (  # noqa: E402
    Gata,
    gata,
    karanas_in_day,
    moon_rashi_pair,
    nakshatra_pair,
    sun_rashis_in_day,
    tithi_pair,
    yoga_pair,
)
from panchang import (  # noqa: E402
    JAIN_TITHI_OFFSET_DAYS,
    get_karana_index_at_jd,
    get_nakshatra_at_jd,
    get_tithi_at_jd,
    get_yoga_at_jd,
)
from panchang_service import generate_location_panchang  # noqa: E402

DELHI = {"lat": 28.6139, "lon": 77.2090}
MINUTE = 1 / 1440
MAKARA = 9


@cache
def _day(local_date: date) -> tuple[float, float]:
    events = generate_location_panchang(local_date, **DELHI)["events"]
    return events["sunrise"]["jd"], events["next_sunrise"]["jd"]


def _sample_dates() -> list[date]:
    return [date(2026, 1, 1) + timedelta(days=d) for d in range(0, 365, 23)]


def _assert_pair_hands_over(pair, *, at, cycle: int) -> None:
    current, following = pair
    assert following.index == current.index % cycle + 1
    assert following.ends_jd > current.ends_jd
    assert at(current.ends_jd - MINUTE) == current.index
    assert at(current.ends_jd + MINUTE) == following.index
    assert at(following.ends_jd - MINUTE) == following.index
    assert at(following.ends_jd + MINUTE) == following.index % cycle + 1


def test_the_tithi_pair_starts_with_the_jain_tithi_and_hands_over_to_the_next():
    for d in _sample_dates():
        sunrise, _ = _day(d)
        reference = sunrise + JAIN_TITHI_OFFSET_DAYS
        pair = tithi_pair(reference)
        assert pair[0].index == get_tithi_at_jd(reference, "Lahiri")
        assert pair[0].ends_jd > reference
        _assert_pair_hands_over(pair, at=lambda jd: get_tithi_at_jd(jd, "Lahiri"), cycle=30)


def test_the_nakshatra_pair_starts_at_sunrise_and_hands_over_to_the_next():
    for d in _sample_dates():
        sunrise, _ = _day(d)
        pair = nakshatra_pair(sunrise)
        assert pair[0].index == get_nakshatra_at_jd(sunrise, "Lahiri")
        _assert_pair_hands_over(pair, at=lambda jd: get_nakshatra_at_jd(jd, "Lahiri"), cycle=27)


def test_the_yoga_pair_starts_at_sunrise_and_hands_over_to_the_next():
    for d in _sample_dates():
        sunrise, _ = _day(d)
        pair = yoga_pair(sunrise)
        assert pair[0].index == get_yoga_at_jd(sunrise, "Lahiri")
        _assert_pair_hands_over(pair, at=lambda jd: get_yoga_at_jd(jd, "Lahiri"), cycle=27)


def test_the_moon_rashi_pair_starts_at_sunrise_and_hands_over_to_the_next_sign():
    from day_elements import moon_rashi_at

    for d in _sample_dates():
        sunrise, _ = _day(d)
        current, following = moon_rashi_pair(sunrise)
        assert current.index == moon_rashi_at(sunrise)
        assert 0 <= current.index <= 11
        assert following.index == (current.index + 1) % 12
        assert moon_rashi_at(current.ends_jd - MINUTE) == current.index
        assert moon_rashi_at(current.ends_jd + MINUTE) == following.index
        assert following.ends_jd - current.ends_jd > 1.8  # 30° at under 16° a day


def test_every_karana_of_the_day_is_listed_in_order_up_to_the_one_holding_at_next_sunrise():
    for d in _sample_dates():
        sunrise, next_sunrise = _day(d)
        karanas = karanas_in_day(sunrise, next_sunrise)
        assert 2 <= len(karanas) <= 4
        assert karanas[0].index == get_karana_index_at_jd(sunrise, "Lahiri")
        for before, after in zip(karanas, karanas[1:]):
            assert after.index == before.index % 60 + 1
            assert before.ends_jd < next_sunrise
            assert get_karana_index_at_jd(before.ends_jd + MINUTE, "Lahiri") == after.index
        assert karanas[-1].ends_jd >= next_sunrise


def test_the_sun_holds_one_rashi_on_an_ordinary_day():
    sunrise, next_sunrise = _day(date(2025, 2, 1))
    (only,) = sun_rashis_in_day(sunrise, next_sunrise)
    assert only.index == MAKARA
    assert only.ends_jd is None


def test_makar_sankranti_2025_shows_dhanu_handing_over_to_makara():
    # Makar Sankranti 2025: 14 January, 09:03 IST (Drik Panchang), after Delhi's sunrise.
    sunrise, next_sunrise = _day(date(2025, 1, 14))
    dhanu, makara = sun_rashis_in_day(sunrise, next_sunrise)
    assert (dhanu.index, makara.index) == (MAKARA - 1, MAKARA)
    assert sunrise < dhanu.ends_jd < next_sunrise
    assert makara.ends_jd is None


def test_the_sankranti_day_is_gata_day_one_and_the_count_then_rises_daily():
    def gata_on(d: date) -> Gata:
        _, next_sunrise = _day(d)
        return gata(next_sunrise, rule="modern", **DELHI)

    assert gata_on(date(2025, 1, 13)).rashi == MAKARA - 1
    assert gata_on(date(2025, 1, 14)) == Gata(rashi=MAKARA, day=1)
    assert gata_on(date(2025, 1, 15)) == Gata(rashi=MAKARA, day=2)
    assert gata_on(date(2025, 2, 1)) == Gata(rashi=MAKARA, day=19)


def test_gata_counts_up_by_one_each_day_and_restarts_at_one_on_a_new_rashi():
    start = date(2026, 3, 1)
    readings = [
        gata(_day(start + timedelta(days=k))[1], rule="modern", **DELHI) for k in range(70)
    ]
    for before, after in zip(readings, readings[1:]):
        if after.rashi == before.rashi:
            assert after.day == before.day + 1
        else:
            assert (after.rashi, after.day) == ((before.rashi + 1) % 12, 1)
    assert all(1 <= r.day <= 32 for r in readings)
