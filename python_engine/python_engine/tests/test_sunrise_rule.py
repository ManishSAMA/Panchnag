"""The sunrise rule: modern (upper limb, refraction) or traditional (disc centre, no refraction).

Traditional printed panchangs time sunrise by the centre of the Sun's disc with
no atmospheric refraction, a few minutes after the modern upper-limb rule. Two
references used by the user follow it:
  * PanchangReport_2654.pdf -- New Jersey, 40°50'N 74°06'W, 2027, EST all year.
  * "laghu panchang 2027 12ver (2) naman.pdf" -- the Delhi laghu booklet.
"""

from __future__ import annotations

from datetime import date

import pytest

from astronomy import get_sunrise, get_sunset, local_time_to_jd

NEW_JERSEY = (40 + 50 / 60, -(74 + 6 / 60), -5.0)
DELHI = (28.6139, 77.2090, 5.5)
SYDNEY = (-33.8688, 151.2093, 10.0)
ONE_MINUTE = 1.0 / 1440.0


def _midnight(day: date, tz_offset: float) -> float:
    return local_time_to_jd(day.year, day.month, day.day, 0.0, tz_offset)


def _clock(jd: float, day: date, tz_offset: float) -> float:
    """Local clock hours of jd after day's midnight."""
    return (jd - _midnight(day, tz_offset)) * 24.0


PLACES_AND_MONTHS = [
    (place, date(2027, month, 15)) for place in (NEW_JERSEY, DELHI, SYDNEY) for month in range(1, 13)
]


@pytest.mark.parametrize("place, day", PLACES_AND_MONTHS)
def test_traditional_sunrise_is_later_and_sunset_earlier_than_modern(place, day):
    lat, lon, tz = place
    midnight = _midnight(day, tz)

    assert get_sunrise(midnight, lat, lon, rule="traditional") > get_sunrise(midnight, lat, lon, rule="modern")
    assert get_sunset(midnight, lat, lon, rule="traditional") < get_sunset(midnight, lat, lon, rule="modern")


@pytest.mark.parametrize("place, day", PLACES_AND_MONTHS)
def test_the_two_rules_differ_by_minutes_not_hours(place, day):
    lat, lon, tz = place
    midnight = _midnight(day, tz)

    gap = get_sunrise(midnight, lat, lon, rule="traditional") - get_sunrise(midnight, lat, lon, rule="modern")

    assert 2 * ONE_MINUTE < gap < 10 * ONE_MINUTE


def test_the_default_rule_is_modern():
    lat, lon, tz = DELHI
    midnight = _midnight(date(2027, 1, 1), tz)

    assert get_sunrise(midnight, lat, lon) == get_sunrise(midnight, lat, lon, rule="modern")


def test_the_cache_never_hands_one_rules_answer_to_the_other():
    lat, lon, tz = NEW_JERSEY
    midnight = _midnight(date(2027, 3, 31), tz)

    modern = get_sunrise(midnight, lat, lon, rule="modern")
    traditional = get_sunrise(midnight, lat, lon, rule="traditional")

    assert modern != traditional
    assert get_sunrise(midnight, lat, lon, rule="modern") == modern


@pytest.mark.parametrize(
    "place, day, event, expected_clock",
    [
        (NEW_JERSEY, date(2027, 3, 31), "rise", (5, 46)),   # PanchangReport_2654.pdf, March: 05:46
        (NEW_JERSEY, date(2027, 1, 1), "rise", (7, 25)),    # PanchangReport_2654.pdf, January: 07:25
        (DELHI, date(2027, 1, 1), "rise", (7, 19)),         # laghu booklet, 1-15 Jan header: 07:19
        (DELHI, date(2027, 1, 1), "set", (17, 31)),         # laghu booklet, 1-15 Jan header: 17:31
    ],
)
def test_traditional_rule_matches_the_printed_references_within_a_minute(place, day, event, expected_clock):
    lat, lon, tz = place
    finder = get_sunrise if event == "rise" else get_sunset

    hours = _clock(finder(_midnight(day, tz), lat, lon, rule="traditional"), day, tz)

    assert abs(hours * 60 - (expected_clock[0] * 60 + expected_clock[1])) <= 1.5


def test_an_unknown_rule_is_rejected():
    lat, lon, tz = DELHI
    with pytest.raises(ValueError, match="sunrise rule"):
        get_sunrise(_midnight(date(2027, 1, 1), tz), lat, lon, rule="vedic")
