"""The range exports (CSV / Excel / JSON) honour the clock and sunrise settings.

Before this, every export used one UTC offset sampled on 1 January: standard
time in the north only by accident, and summer time all year in the south.
"""

from __future__ import annotations

from datetime import date

import pytest

from export import apply_element_continuity_formatting
from main import run_generation
from range_generation_service import export_timezone

NEW_JERSEY = (40 + 50 / 60, -(74 + 6 / 60), "America/New_York")
JANUARY, JULY = (2027, 1, 15), (2027, 7, 1)


def _rows(*, clock: str, sunrise_rule: str = "modern", dates=(JANUARY, JULY)) -> list[dict]:
    lat, lon, tz_name = NEW_JERSEY
    zone = export_timezone(tz_name, 2027, clock=clock)
    config = {
        "lat": lat, "lon": lon, "tz_name": tz_name, "clock": clock, "sunrise_rule": sunrise_rule,
        "tz_offset": zone["offset_hours"], "tz_label": zone["label"], "ayanamsa": "Lahiri",
    }
    return run_generation(config, list(dates), workers=1)


def _minutes(row: dict, label: str) -> int:
    hours, minutes, _ = map(int, row[f"Sunrise ({label})"].split(":"))
    return hours * 60 + minutes


# ── the export's timezone ────────────────────────────────────────────────

@pytest.mark.parametrize(
    "tz_name, label, offset",
    [("America/New_York", "EST", -5.0), ("Australia/Sydney", "AEST", 10.0), ("Asia/Kolkata", "IST", 5.5)],
)
def test_standard_exports_use_the_zones_standard_offset_north_or_south(tz_name, label, offset):
    assert export_timezone(tz_name, 2027, clock="standard") == {"label": label, "offset_hours": offset}


def test_daylight_exports_label_both_abbreviations():
    assert export_timezone("America/New_York", 2027, clock="daylight")["label"] == "EST/EDT"
    assert export_timezone("Asia/Kolkata", 2027, clock="daylight")["label"] == "IST"


# ── per-day rows ─────────────────────────────────────────────────────────

def test_standard_rows_keep_one_clock_all_year():
    january, july = _rows(clock="standard")

    assert (january["__tz_offset"], july["__tz_offset"]) == (-5.0, -5.0)


def test_daylight_rows_follow_the_wall_clock_in_summer():
    standard_july = _rows(clock="standard")[1]
    daylight_january, daylight_july = _rows(clock="daylight")

    assert (daylight_january["__tz_offset"], daylight_july["__tz_offset"]) == (-5.0, -4.0)
    assert _minutes(daylight_july, "EST/EDT") - _minutes(standard_july, "EST") == 60


def test_the_traditional_rule_moves_the_exported_sunrise_later():
    modern = _rows(clock="standard", sunrise_rule="modern")[0]
    traditional = _rows(clock="standard", sunrise_rule="traditional")[0]

    assert 2 <= _minutes(traditional, "EST") - _minutes(modern, "EST") <= 8


def test_continuity_labels_use_each_rows_own_clock():
    """An element's end time is printed in the clock of the row it ends on."""
    july_end_jd = 2461588.0  # 2027-07-01 12:00 UTC
    rows = [{"Tithi": "Navami", "__Tithi_End_JD": july_end_jd, "__tz_offset": -4.0}]

    [formatted] = apply_element_continuity_formatting(rows, tz_offset=-5.0)

    assert "2027-07-01 08:00" in formatted["Tithi"]


# ── request, endpoint, CLI ───────────────────────────────────────────────

def test_the_range_request_carries_both_settings():
    from request_parsing import parse_range_generation_request

    parsed = parse_range_generation_request(
        {"start_year": 2027, "end_year": 2027, "lat": 40.83, "lon": -74.1, "clock": "daylight", "sunrise": "traditional"}
    )

    assert (parsed.clock, parsed.sunrise_rule) == ("daylight", "traditional")


def test_the_range_endpoint_forwards_both_settings():
    from unittest.mock import patch

    from app import app

    with patch("app.generate_year_range_exports", return_value={"files": []}) as service:
        response = app.test_client().post("/generate-range-panchang", json={
            "start_year": 2027, "end_year": 2027, "lat": 40.83, "lon": -74.1,
            "clock": "daylight", "sunrise": "traditional",
        })

    assert response.status_code == 200
    assert (service.call_args.kwargs["clock"], service.call_args.kwargs["sunrise_rule"]) == ("daylight", "traditional")


def test_the_cli_with_a_zone_name_follows_the_clock_setting(tmp_path):
    import json

    import main as cli

    lat, lon, tz_name = NEW_JERSEY
    cli.main([
        "--start_year", "2027", "--end_year", "2027", "--lat", str(lat), "--lon", str(lon),
        "--tz_name", tz_name, "--clock", "daylight", "--sunrise", "traditional",
        "--format", "json", "--output", str(tmp_path / "nj"),
    ])

    [written] = tmp_path.glob("nj_2027_2027*.json")
    rows = {row["Date"]: row for row in json.loads(written.read_text(encoding="utf-8"))}
    january, july = rows["2027-01-15"], rows["2027-07-01"]
    assert "Sunrise (EST/EDT)" in july
    january_hour = int(january["Sunrise (EST/EDT)"][:2])
    july_hour = int(july["Sunrise (EST/EDT)"][:2])
    assert (january_hour, july_hour) == (7, 5)  # 07:1x EST in January, 05:3x EDT in July
