"""Each range-export row belongs to its own civil day, even when sunrise is early.

The per-day computation used to search for sunrise from 05:30 local time. Where
sunrise comes earlier (Trenton from mid-April to early September in EST, Delhi
around June at ~05:23 IST) it found the NEXT morning's sunrise, and the whole row
-- tithi, nakshatra, yoga, Bhadra -- described the following day. Found by
comparing a Trenton 2027 export (panchang_2027_2027.xlsx) with the Laghu booklet.
"""

from __future__ import annotations

from datetime import date

import pytest

from astronomy import get_sunrise, jd_to_local_time_string, local_time_to_jd
from main import run_generation
from panchang import get_tithi_at_jd

PLACES = {
    "trenton": (40.2203, -74.7658, "America/New_York", -5.0, "EST"),
    "delhi": (28.6139, 77.2090, "Asia/Kolkata", 5.5, "IST"),
}


def _row(place: str, day: date) -> dict:
    lat, lon, tz_name, offset, label = PLACES[place]
    config = {"lat": lat, "lon": lon, "tz_name": tz_name, "clock": "standard", "sunrise_rule": "modern",
              "tz_offset": offset, "tz_label": label, "ayanamsa": "Lahiri"}
    [row] = run_generation(config, [(day.year, day.month, day.day)], workers=1)
    return row


def _true_sunrise(place: str, day: date) -> float:
    lat, lon, _, offset, _ = PLACES[place]
    return get_sunrise(local_time_to_jd(day.year, day.month, day.day, 0.0, offset), lat, lon)


@pytest.mark.parametrize(
    "place, day",
    [("trenton", date(2027, 4, 10)), ("trenton", date(2027, 6, 21)), ("trenton", date(2027, 9, 1)),
     ("delhi", date(2026, 6, 15)), ("trenton", date(2027, 1, 15))],
    ids=["trenton-april", "trenton-solstice", "trenton-september", "delhi-june", "trenton-january"],
)
def test_a_row_uses_that_days_own_sunrise_and_tithi(place, day):
    sunrise = _true_sunrise(place, day)
    offset, label = PLACES[place][3], PLACES[place][4]

    row = _row(place, day)

    assert row[f"Sunrise ({label})"] == jd_to_local_time_string(sunrise, offset)
    assert row["Tithi_No"] == get_tithi_at_jd(sunrise, "Lahiri")
