"""Choosing a kalyanak school for the Laghu Panchang (and the festival export).

The three textual traditions -- Vrindavan (1), Uttarapurana (2), Ashadhara (3)
-- disagree on some kalyanak tithis. With a school chosen, a kalyanak attested
only by other schools is left out; festivals no school claims (parvas, vrats)
always stay. "all" keeps everything, as before.

Delhi, February 2027 (from the app's own festival calendar): 16 Feb Ajitnath
diksha is Vrindavan-only, 22 Feb Arnath garbha Uttarapurana-only, 27 Feb
Chandraprabh moksha Ashadhara-only.
"""

from __future__ import annotations

from functools import cache
from unittest.mock import patch

import pytest

import hindi_calendar_pdf
import main as cli
import pdf_generation_service
from app import app
from hindi_calendar_pdf import festivals_for_school
from laghu_panchang import build_laghu_year
from request_parsing import parse_laghu_panchang_request

DELHI = {"lat": 28.6139, "lon": 77.2090}
AJITNATH = "श्री अजितनाथ भगवान दीक्षा कल्याणक"        # 16 Feb, Vrindavan only
ARNATH = "श्री अरनाथ भगवान गर्भ कल्याणक"              # 22 Feb, Uttarapurana only
CHANDRAPRABH = "श्री चंद्रप्रभ भगवान मोक्ष कल्याणक"   # 27 Feb, Ashadhara only


def _festival(name: str, *sources: str) -> dict:
    return {"name": name, "sources": list(sources)}


# ── the filter ───────────────────────────────────────────────────────────

FESTIVALS = [
    _festival("agreed by all", "Vrindavan", "Uttarapurana", "Sanskrit Jin Kalyanaka Mala by Ashadhara"),
    _festival("vrindavan only", "Vrindavan"),
    _festival("ashadhara only", "Sanskrit Jin Kalyanaka Mala by Ashadhara"),
    _festival("paryushan"),
]


def _names(festivals: list[dict]) -> list[str]:
    return [festival["name"] for festival in festivals]


def test_all_schools_keeps_every_festival():
    assert festivals_for_school(FESTIVALS, "all") == FESTIVALS


def test_a_school_keeps_its_own_and_unclaimed_festivals_and_drops_the_others():
    assert _names(festivals_for_school(FESTIVALS, "vrindavan")) == ["agreed by all", "vrindavan only", "paryushan"]
    assert _names(festivals_for_school(FESTIVALS, "ashadhara")) == ["agreed by all", "ashadhara only", "paryushan"]
    assert _names(festivals_for_school(FESTIVALS, "uttarapurana")) == ["agreed by all", "paryushan"]


def test_an_unknown_school_is_rejected():
    with pytest.raises(ValueError, match="school"):
        festivals_for_school(FESTIVALS, "jaipur")


# ── the booklet ──────────────────────────────────────────────────────────

@cache
def _february_events(school: str) -> dict[int, str]:
    halves = build_laghu_year(year=2027, months=(2,), tz_name="Asia/Kolkata", school=school, **DELHI)
    return {day.date.day: day.events for half in halves for day in half.days}


def test_all_schools_prints_every_schools_kalyanaks():
    events = _february_events("all")

    assert AJITNATH in events[16] and ARNATH in events[22] and CHANDRAPRABH in events[27]


@pytest.mark.parametrize(
    "school, kept, dropped",
    [
        ("vrindavan", (16, AJITNATH), [(22, ARNATH), (27, CHANDRAPRABH)]),
        ("uttarapurana", (22, ARNATH), [(16, AJITNATH), (27, CHANDRAPRABH)]),
        ("ashadhara", (27, CHANDRAPRABH), [(16, AJITNATH), (22, ARNATH)]),
    ],
)
def test_one_school_prints_only_its_own_kalyanaks(school, kept, dropped):
    events = _february_events(school)

    assert kept[1] in events[kept[0]]
    assert all(name not in events[day] for day, name in dropped)


# ── request, service, endpoint, CLI ──────────────────────────────────────

def test_the_request_defaults_to_all_schools_and_validates():
    assert parse_laghu_panchang_request({"year": 2027, **DELHI}).school == "all"
    assert parse_laghu_panchang_request({"year": 2027, "school": "Ashadhara", **DELHI}).school == "ashadhara"
    with pytest.raises(ValueError, match="school"):
        parse_laghu_panchang_request({"year": 2027, "school": "jaipur", **DELHI})


def _fake_renderer(html_path: str, pdf_path: str, **_options) -> bool:
    from pathlib import Path

    Path(pdf_path).write_bytes(b"%PDF-1.4 stub")
    return True


def test_the_service_builds_for_the_school_and_names_it_in_the_file(tmp_path):
    from tests.test_laghu_panchang_render import make_year

    with patch.object(pdf_generation_service, "build_laghu_year", return_value=make_year(months=(1,))) as build, \
         patch.object(hindi_calendar_pdf, "_html_to_pdf", _fake_renderer):
        result = pdf_generation_service.generate_laghu_panchang_export(
            year=2027, city="Delhi", ayanamsa_name="Lahiri", profile="shwetambar_murtipujak_tapagachchha",
            output_format="pdf", output_dir=str(tmp_path), school="vrindavan", **DELHI,
        )

    assert build.call_args.kwargs["school"] == "vrindavan"
    assert result["school"] == "vrindavan"
    assert result["files"][0]["name"] == "Laghu_Panchang_2027_Delhi_Vrindavan.pdf"
    assert "वृन्दावन" in (tmp_path / "Laghu_Panchang_2027_Delhi_Vrindavan.html").read_text(encoding="utf-8")


def test_the_endpoint_forwards_the_school():
    with patch("app.generate_laghu_panchang_export", return_value={
        "year": 2027, "ayanamsa": "Lahiri", "profile": "p", "school": "ashadhara", "location": {}, "files": [],
    }) as service:
        response = app.test_client().post("/generate-laghu-panchang", json={"year": 2027, "school": "ashadhara", **DELHI})

    assert response.status_code == 200
    assert service.call_args.kwargs["school"] == "ashadhara"
    assert response.get_json()["school"] == "ashadhara"


def test_the_cli_accepts_the_school(tmp_path):
    from tests.test_laghu_panchang_render import make_year

    with patch.object(pdf_generation_service, "build_laghu_year", return_value=make_year(months=(1,))) as build, \
         patch.object(hindi_calendar_pdf, "_html_to_pdf", _fake_renderer):
        cli.main(["laghu", "--year", "2027", "--lat", "28.6139", "--lon", "77.2090",
                  "--school", "uttarapurana", "--output", str(tmp_path)])

    assert build.call_args.kwargs["school"] == "uttarapurana"


# ── the festival export uses the same rule ───────────────────────────────

@pytest.mark.parametrize(
    "source, expected",
    [
        ("all", ["agreed by all", "vrindavan only", "ashadhara only", "paryushan"]),
        ("Vrindavan", ["agreed by all", "vrindavan only", "paryushan"]),
        ("Ashadhara", ["agreed by all", "ashadhara only", "paryushan"]),
    ],
)
def test_the_festival_export_filters_by_school_the_same_way(source, expected):
    import json

    client = app.test_client()
    with patch("jain_observances.festival_service.generate_jain_festivals", return_value={"festivals": FESTIVALS}):
        response = client.post("/generate-jain-festival-exports", json={"year": 2027, **DELHI, "format": "json", "source": source})

    assert response.status_code == 200
    download = client.get(response.get_json()["files"][0]["download_url"])
    assert [row["Name_English"] for row in json.loads(download.data)] == expected
