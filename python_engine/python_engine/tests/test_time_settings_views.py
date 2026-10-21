"""Month overview, choghadiya, muhurta and festival endpoints honour the time settings."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from app import app
from yoga_service import detect_all_yogas_for_day
from astronomy import get_sunrise, local_date_anchor_jd

NJ = {"lat": 40 + 50 / 60, "lon": -(74 + 6 / 60)}
NEW_YORK = "America/New_York"


def _hm(text: str) -> int:
    hours, minutes = map(int, text[:5].split(":"))
    return hours * 60 + minutes


@pytest.fixture()
def client():
    return app.test_client()


def test_month_overview_follows_the_clock(client):
    def first_day(clock: str) -> dict:
        response = client.get("/month-overview", query_string={"year": 2027, "month": 7, **NJ, "clock": clock})
        assert response.status_code == 200
        return response.get_json()["days"][0]

    assert _hm(first_day("daylight")["sunrise_time"]) - _hm(first_day("standard")["sunrise_time"]) == 60


def test_month_overview_rejects_an_unknown_clock(client):
    response = client.get("/month-overview", query_string={"year": 2027, "month": 7, **NJ, "clock": "summer"})

    assert response.status_code == 400


def _choghadiya(client, **settings) -> dict:
    response = client.post("/choghadiya", json={"date": "2027-07-01", **NJ, **settings})
    assert response.status_code == 200
    return response.get_json()


def test_choghadiya_follows_the_clock_and_the_rule(client):
    standard = _choghadiya(client, clock="standard")
    daylight = _choghadiya(client, clock="daylight")
    traditional = _choghadiya(client, clock="standard", sunrise="traditional")

    assert _hm(daylight["sunrise"]) - _hm(standard["sunrise"]) == 60
    assert _hm(daylight["slots"][0]["start_time"]) - _hm(standard["slots"][0]["start_time"]) == 60
    assert 2 <= _hm(traditional["sunrise"]) - _hm(standard["sunrise"]) <= 8


def _july_yogas(clock: str) -> dict:
    day = date(2027, 7, 1)
    sunrise = get_sunrise(local_date_anchor_jd(day, NEW_YORK, clock="standard"), NJ["lat"], NJ["lon"])
    next_sunrise = get_sunrise(local_date_anchor_jd(date(2027, 7, 2), NEW_YORK, clock="standard"), NJ["lat"], NJ["lon"])
    return detect_all_yogas_for_day(
        date_obj=day, sunrise_jd=sunrise, next_sunrise_jd=next_sunrise, tz_name=NEW_YORK, clock=clock,
    )


def test_yoga_times_follow_the_clock():
    standard = _july_yogas("standard")["aanandadi_yogas"][0]
    daylight = _july_yogas("daylight")["aanandadi_yogas"][0]

    assert _hm(daylight["start_time"]) - _hm(standard["start_time"]) == 60
    assert daylight["start_local"].endswith("-04:00") and standard["start_local"].endswith("-05:00")


def test_the_muhurta_endpoint_follows_the_clock(client):
    def first_yoga(clock: str) -> dict:
        response = client.post("/dainika-muhurta", json={"date": "2027-07-01", **NJ, "clock": clock})
        assert response.status_code == 200
        return response.get_json()["aanandadi_yogas"][0]

    assert _hm(first_yoga("daylight")["start_time"]) - _hm(first_yoga("standard")["start_time"]) == 60


def test_the_muhurta_export_accepts_the_settings(client):
    response = client.post("/dainika-muhurta-export", json={
        "year": 2027, "month": 2, **NJ, "clock": "daylight", "sunrise": "traditional",
    })

    assert response.status_code == 200


@pytest.mark.parametrize("endpoint", ["/generate-jain-festivals", "/generate-jain-festival-exports"])
def test_festival_endpoints_pass_the_sunrise_rule(client, endpoint):
    with patch("jain_observances.festival_service.generate_jain_festivals", return_value={"festivals": []}) as service:
        client.post(endpoint, json={"year": 2027, **NJ, "sunrise": "traditional", "format": "json"})

    assert service.call_args.kwargs["sunrise_rule"] == "traditional"
