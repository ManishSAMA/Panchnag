"""The daily panchang view honours the clock and sunrise settings.

Default clock is "standard" (user decision, 2026-10-16): for a DST location the
daily view now reads standard time all year, as printed panchangs do.
"""

from __future__ import annotations

from unittest.mock import patch

from app import app
from panchang_service import generate_location_panchang

NJ = {"lat": 40 + 50 / 60, "lon": -(74 + 6 / 60)}
JULY = "2027-07-01"


def _day(**settings) -> dict:
    return generate_location_panchang(JULY, **NJ, **settings)


def _minutes(event: dict) -> int:
    hours, minutes, _ = map(int, event["time"].split(":"))
    return hours * 60 + minutes


def test_standard_clock_shows_est_in_summer_and_daylight_shows_edt():
    standard = _day(clock="standard")["events"]["sunrise"]
    daylight = _day(clock="daylight")["events"]["sunrise"]

    assert standard["local"].endswith("-05:00")
    assert daylight["local"].endswith("-04:00")
    assert _minutes(daylight) - _minutes(standard) == 60


def test_every_time_in_the_day_moves_with_the_clock():
    standard = _day(clock="standard")["panchang"]
    daylight = _day(clock="daylight")["panchang"]

    assert _minutes(daylight["nakshatra"]["ends"]) - _minutes(standard["nakshatra"]["ends"]) in (60, 60 - 1440)
    assert daylight["jain_tithi"]["ends"]["local"].endswith("-04:00")
    assert standard["jain_tithi"]["ends"]["local"].endswith("-05:00")


def test_the_default_clock_is_standard():
    assert _day()["events"]["sunrise"] == _day(clock="standard")["events"]["sunrise"]


def test_the_traditional_sunrise_is_later():
    modern = _day(clock="standard", sunrise_rule="modern")["events"]["sunrise"]
    traditional = _day(clock="standard", sunrise_rule="traditional")["events"]["sunrise"]

    assert 2 <= _minutes(traditional) - _minutes(modern) <= 8


def test_the_payload_states_its_settings():
    payload = _day(clock="daylight", sunrise_rule="traditional")

    assert (payload["clock"], payload["sunrise_rule"]) == ("daylight", "traditional")


def test_the_endpoint_forwards_both_settings():
    with patch("app.generate_location_panchang", return_value={"ok": True}) as service:
        response = app.test_client().post("/generate-panchang", json={
            "date": JULY, **NJ, "clock": "daylight", "sunrise": "traditional",
        })

    assert response.status_code == 200
    assert (service.call_args.kwargs["clock"], service.call_args.kwargs["sunrise_rule"]) == ("daylight", "traditional")
