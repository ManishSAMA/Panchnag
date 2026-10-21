"""The mobile app's pre-computed database honours the sunrise rule and records it.

The database stores UTC instants, so the clock setting does not apply to it.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

import db_generator
from db_reader import get_day, get_meta

NJ = {"latitude": 40 + 50 / 60, "longitude": -(74 + 6 / 60), "timezone_str": "America/New_York"}


def _build(tmp_path, monkeypatch, rule: str):
    monkeypatch.setattr(db_generator, "_DATE_START", date(2027, 1, 15))
    monkeypatch.setattr(db_generator, "_DATE_END", date(2027, 1, 16))
    path = str(tmp_path / f"nj_{rule}.db")
    db_generator.generate_panchang_db(
        city_name="New Jersey", city_slug="nj", db_path=path, sunrise_rule=rule, **NJ,
    )
    return path


def test_the_database_records_its_sunrise_rule(tmp_path, monkeypatch):
    path = _build(tmp_path, monkeypatch, "traditional")

    assert get_meta(path)["sunrise_rule"] == "traditional"


def test_the_traditional_database_has_later_sunrises(tmp_path, monkeypatch):
    modern = get_day(_build(tmp_path, monkeypatch, "modern"), "2027-01-15")["sunrise"]
    traditional = get_day(_build(tmp_path, monkeypatch, "traditional"), "2027-01-15")["sunrise"]

    gap_minutes = (datetime.fromisoformat(traditional) - datetime.fromisoformat(modern)).total_seconds() / 60
    assert 2 <= gap_minutes <= 8


def test_the_default_database_uses_the_modern_rule(tmp_path, monkeypatch):
    monkeypatch.setattr(db_generator, "_DATE_START", date(2027, 1, 15))
    monkeypatch.setattr(db_generator, "_DATE_END", date(2027, 1, 15))
    path = str(tmp_path / "default.db")
    db_generator.generate_panchang_db(city_name="New Jersey", city_slug="nj", db_path=path, **NJ)

    assert get_meta(path)["sunrise_rule"] == "modern"


def test_the_generate_db_endpoint_rejects_an_unknown_rule():
    from app import app

    response = app.test_client().post("/api/generate-db", json={
        "city_name": "New Jersey", "city_slug": "nj_bad_rule", "latitude": 40.83, "longitude": -74.1,
        "timezone": "America/New_York", "sunrise": "vedic",
    })

    assert response.status_code == 400
    assert "sunrise" in response.get_json()["error"]
