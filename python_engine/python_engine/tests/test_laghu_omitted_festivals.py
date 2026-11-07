"""The Laghu booklet leaves out two festivals the rest of the app keeps.

User directive 2026-10-30: drop श्री पार्श्वनाथ जयंती and जिन मूर्ति स्थापना दिवस
from the booklet only. Both fall early in 2027 (2 Jan; 11 Feb, the Magha Shukla
Panchami shared with Kundakunda Jayanti and Vasant Panchami).
"""

from __future__ import annotations

from functools import cache

from jain_observances.festival_service import generate_jain_festivals
from laghu_panchang import build_laghu_year

DELHI = {"lat": 28.6139, "lon": 77.2090}


@cache
def _booklet_events() -> str:
    halves = build_laghu_year(year=2027, tz_name="Asia/Kolkata", profile="all", months=(1, 2), **DELHI)
    return " ".join(day.events for half in halves for day in half.days)


def test_the_booklet_drops_parshvanath_jayanti_and_jin_murti_sthapana():
    events = _booklet_events()

    assert "पार्श्वनाथ जयंती" not in events
    assert "मूर्ति स्थापना" not in events


def test_the_festivals_sharing_their_day_stay_in_the_booklet():
    events = _booklet_events()

    assert "आचार्य कुंदकुंद स्वामी जन्म जयंती" in events
    assert "वसन्त पंचमी" in events


def test_the_app_calendar_still_has_both():
    ids = {f["id"] for f in generate_jain_festivals(2027, DELHI["lat"], DELHI["lon"], "Lahiri", "all")["festivals"]}

    assert {"parshvanath_jayanti", "jina_murti_sthapna_2027"} <= ids
