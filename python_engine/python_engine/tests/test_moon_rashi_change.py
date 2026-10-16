"""The Moon's sign change within a solar day (sunrise to next sunrise).

The Laghu Panchang's चन्द्र राशि प्रवेश column prints the sign at sunrise, or the
new sign and its entry time when the Moon crosses a 30-degree boundary before
the next sunrise. These are invariants, not ephemeris goldens.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from astronomy import get_planetary_longitude, get_sunrise, local_time_to_jd
from panchang import find_moon_rashi_change

DELHI = {"lat": 28.6139, "lon": 77.2090, "tz": 5.5}
ONE_MINUTE = 1.0 / 1440.0


def _sunrise(day: date) -> float:
    midnight = local_time_to_jd(day.year, day.month, day.day, 0.0, DELHI["tz"])
    return get_sunrise(midnight, DELHI["lat"], DELHI["lon"])


def _rashi(jd: float) -> int:
    return int(get_planetary_longitude(jd, "Moon", "Lahiri") / 30.0) % 12


def _solar_days(start: date, count: int) -> list[tuple[float, float]]:
    days = [start + timedelta(days=offset) for offset in range(count + 1)]
    sunrises = [_sunrise(day) for day in days]
    return list(zip(sunrises, sunrises[1:]))


SOLAR_DAYS = _solar_days(date(2027, 1, 1), 31)


@pytest.mark.parametrize("sunrise_jd, next_sunrise_jd", SOLAR_DAYS)
def test_sunrise_rashi_is_the_moons_sign_at_sunrise(sunrise_jd, next_sunrise_jd):
    rashi_at_sunrise, _, _ = find_moon_rashi_change(sunrise_jd, next_sunrise_jd, "Lahiri")

    assert rashi_at_sunrise == _rashi(sunrise_jd)


@pytest.mark.parametrize("sunrise_jd, next_sunrise_jd", SOLAR_DAYS)
def test_a_reported_entry_falls_inside_the_day_on_the_sign_boundary(sunrise_jd, next_sunrise_jd):
    rashi_at_sunrise, new_rashi, entry_jd = find_moon_rashi_change(
        sunrise_jd, next_sunrise_jd, "Lahiri"
    )
    if entry_jd is None:
        assert new_rashi is None
        assert _rashi(next_sunrise_jd) == rashi_at_sunrise
        return

    assert sunrise_jd < entry_jd <= next_sunrise_jd
    assert new_rashi == (rashi_at_sunrise + 1) % 12
    assert _rashi(entry_jd - ONE_MINUTE) == rashi_at_sunrise
    assert _rashi(entry_jd + ONE_MINUTE) == new_rashi


def test_the_moon_changes_sign_on_some_days_and_not_on_others():
    entries = [
        find_moon_rashi_change(sunrise_jd, next_sunrise_jd, "Lahiri")[2]
        for sunrise_jd, next_sunrise_jd in SOLAR_DAYS
    ]

    # The Moon spends about 2.5 days per sign, so a month has roughly 13 entries.
    assert 10 <= sum(entry is not None for entry in entries) <= 15
