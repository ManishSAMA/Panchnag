"""The English yearly PDF and the Hindi calendar PDF honour the clock and sunrise settings."""

from __future__ import annotations

import re
from unittest.mock import patch

import pytest

import export_pdf
import hindi_calendar_pdf
import pdf_generation_service
from app import app
from request_parsing import parse_hindi_pdf_request, parse_pdf_generation_request

NJ = {"lat": 40 + 50 / 60, "lon": -(74 + 6 / 60)}
NEW_YORK = "America/New_York"


def _minutes_12h(text: str) -> int:
    hours, minutes = map(int, re.match(r"(\d{2}):(\d{2})", text).groups())
    return (hours % 12 + (12 if "सायं" in text else 0)) * 60 + minutes


def _hindi_july_first(**settings) -> dict:
    rows = hindi_calendar_pdf.build_month_rows(
        2027, 7, tz_offset=-5.0, ayanamsa="Lahiri", date_to_fests={}, tz_name=NEW_YORK, **NJ, **settings,
    )
    return rows[0]


def test_hindi_calendar_sunrise_follows_the_clock_in_summer():
    standard = _hindi_july_first(clock="standard")
    daylight = _hindi_july_first(clock="daylight")

    assert _minutes_12h(daylight["sunrise"]) - _minutes_12h(standard["sunrise"]) == 60


def test_hindi_calendar_traditional_sunrise_is_later():
    modern = _hindi_july_first(clock="standard", sunrise_rule="modern")
    traditional = _hindi_july_first(clock="standard", sunrise_rule="traditional")

    assert 2 <= _minutes_12h(traditional["sunrise"]) - _minutes_12h(modern["sunrise"]) <= 8


def _english_rows(**settings) -> dict:
    rows = export_pdf.build_year_rows(2027, tz_offset=-5.0, ayanamsa="Lahiri", tz_name=NEW_YORK, months=(1, 7), **NJ, **settings)
    return {row["Date"]: row for row in rows}


def _sunrise_minutes(row: dict) -> int:
    hours, minutes, _ = map(int, row["Sunrise (PDF)"].split(":"))
    return hours * 60 + minutes


def test_english_pdf_rows_follow_the_clock_and_the_rule():
    standard = _english_rows(clock="standard")
    daylight = _english_rows(clock="daylight")
    traditional = _english_rows(clock="standard", sunrise_rule="traditional")

    assert _sunrise_minutes(daylight["2027-07-01"]) - _sunrise_minutes(standard["2027-07-01"]) == 60
    assert _sunrise_minutes(daylight["2027-01-15"]) == _sunrise_minutes(standard["2027-01-15"])
    assert 2 <= _sunrise_minutes(traditional["2027-01-15"]) - _sunrise_minutes(standard["2027-01-15"]) <= 8


@pytest.mark.parametrize("parser, payload", [
    (parse_pdf_generation_request, {"year": 2027}),
    (parse_hindi_pdf_request, {"start_year": 2027}),
])
def test_both_pdf_requests_carry_the_settings(parser, payload):
    parsed = parser({**payload, **NJ, "clock": "daylight", "sunrise": "traditional"})

    assert (parsed.clock, parsed.sunrise_rule) == ("daylight", "traditional")


def test_the_english_pdf_service_passes_zone_and_settings(tmp_path):
    with patch.object(pdf_generation_service, "generate_pdf_calendar") as render:
        pdf_generation_service.generate_pdf_export(
            year=2027, city=None, ayanamsa_name="Lahiri", output_dir=str(tmp_path),
            clock="daylight", sunrise_rule="traditional", **NJ,
        )

    kwargs = render.call_args.kwargs
    assert (kwargs["tz_name"], kwargs["clock"], kwargs["sunrise_rule"]) == (NEW_YORK, "daylight", "traditional")


def test_the_hindi_pdf_service_passes_zone_and_settings(tmp_path):
    with patch.object(hindi_calendar_pdf, "generate_hindi_pdf_calendar", return_value=str(tmp_path / "x.pdf")) as render:
        pdf_generation_service.generate_hindi_pdf_export(
            start_year=2027, start_month=1, month_count=1, city=None, ayanamsa_name="Lahiri",
            calendar_system="purnimanta", output_dir=str(tmp_path), clock="daylight", sunrise_rule="traditional", **NJ,
        )

    kwargs = render.call_args.kwargs
    assert (kwargs["tz_name"], kwargs["clock"], kwargs["sunrise_rule"]) == (NEW_YORK, "daylight", "traditional")


@pytest.mark.parametrize("endpoint, service, payload, result", [
    ("/generate-pdf-panchang", "app.generate_pdf_export", {"year": 2027},
     {"year": 2027, "ayanamsa": "Lahiri", "location": {}, "file": {"name": "a.pdf", "path": "a.pdf"}}),
    ("/generate-hindi-pdf", "app.generate_hindi_pdf_export", {"start_year": 2027},
     {"ayanamsa": "Lahiri", "location": {}, "file": {"name": "a.pdf", "path": "a.pdf", "format": "pdf"}}),
])
def test_both_pdf_endpoints_forward_the_settings(endpoint, service, payload, result):
    with patch(service, return_value=result) as generate:
        response = app.test_client().post(endpoint, json={**payload, **NJ, "clock": "daylight", "sunrise": "traditional"})

    assert response.status_code == 200
    assert (generate.call_args.kwargs["clock"], generate.call_args.kwargs["sunrise_rule"]) == ("daylight", "traditional")


def test_the_hindi_calendar_cli_accepts_zone_and_settings(tmp_path):
    with patch.object(hindi_calendar_pdf, "generate_hindi_pdf_calendar") as render:
        hindi_calendar_pdf.main([
            "--start-year", "2027", "--months", "1", "--lat", "40.83", "--lon", "-74.1",
            "--tz-name", NEW_YORK, "--clock", "daylight", "--sunrise", "traditional",
            "--out", str(tmp_path / "x.pdf"),
        ])

    kwargs = render.call_args.kwargs
    assert (kwargs["tz_name"], kwargs["clock"], kwargs["sunrise_rule"]) == (NEW_YORK, "daylight", "traditional")
