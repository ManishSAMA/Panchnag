"""The calendar layer reports Purnimanta months by default.

North Indian physical panchangs end the month at Purnima. The app computed
Amanta throughout its display layer, which put month names ~15 days behind the
book: Vaishakh beginning 18 Apr 2026 instead of 2 Apr, Pratham Jyeshtha 17 May
instead of 2 May.

Purnimanta is now the default. `calendar_system="amanta"` restores the previous
reckoning for Gujarati and South Indian use, where Amanta is correct.
"""

import pytest

from app import create_app
from panchang_service import generate_location_panchang


LAT, LON = 26.9124, 75.7873  # Jaipur


@pytest.fixture
def client():
    return create_app().test_client()


def _month(payload):
    return payload["panchang"]["hindu_month"]


# (date, purnimanta month, amanta month) -- purnimanta side from the physical panchang.
_DISPUTED_DAYS = [
    ("2026-04-02", "Vaishakha", "Chaitra"),     # Krishna 1: the reported bug
    ("2026-04-17", "Vaishakha", "Chaitra"),     # Amavasya
    ("2026-04-18", "Vaishakha", "Vaishakha"),   # Shukla 1: systems agree
    ("2026-05-02", "Jyeshtha", "Vaishakha"),    # Krishna 1: Pratham (Adhik) Jyeshtha
    ("2026-06-01", "Jyeshtha", "Jyeshtha"),     # Krishna 1: Nija Jyeshtha
]


@pytest.mark.parametrize("day,purnimanta,amanta", _DISPUTED_DAYS)
def test_daily_panchang_defaults_to_purnimanta(day, purnimanta, amanta):
    result = generate_location_panchang(day, lat=LAT, lon=LON)
    assert _month(result)["name"].removeprefix("Adhika ") == purnimanta


@pytest.mark.parametrize("day,purnimanta,amanta", _DISPUTED_DAYS)
def test_amanta_remains_available_on_request(day, purnimanta, amanta):
    result = generate_location_panchang(day, lat=LAT, lon=LON, calendar_system="amanta")
    assert _month(result)["name"].removeprefix("Adhika ") == amanta


def test_adhika_flag_inverts_with_the_convention():
    """1 Jun 2026 is Nija Jyeshtha in the book and Adhika Jyeshtha under amanta."""
    purnimanta = generate_location_panchang("2026-06-01", lat=LAT, lon=LON)
    amanta = generate_location_panchang(
        "2026-06-01", lat=LAT, lon=LON, calendar_system="amanta"
    )

    assert _month(purnimanta)["is_adhika"] is False
    assert _month(amanta)["is_adhika"] is True


def test_month_index_tracks_the_reported_name():
    """hindu_month_index must not keep pointing at the amanta month."""
    from panchang import HINDU_MONTH_NAMES

    result = generate_location_panchang("2026-04-02", lat=LAT, lon=LON)
    month = _month(result)
    assert HINDU_MONTH_NAMES[month["index"]] == month["name"].removeprefix("Adhika ")


def test_structured_payload_agrees_with_the_panchang_block():
    result = generate_location_panchang("2026-05-02", lat=LAT, lon=LON)
    assert result["structured"]["month"] == _month(result)["name"]


def test_month_overview_defaults_to_purnimanta(client):
    """June 2026 opens in Nija Jyeshtha; the amanta reading calls it Adhika.

    The header names the lunar month of the Gregorian 1st, so it only differs
    between conventions when that day falls in a Krishna paksha -- true for
    June-December 2026. 1 Jun 2026 is Krishna 1 and carries the Adhik-Maas
    inversion, making it the sharpest case.
    """
    payload = client.get(f"/month-overview?year=2026&month=6&lat={LAT}&lon={LON}").get_json()

    assert payload["hindu_month"] == "Jyeshtha"
    assert payload["calendar_system"] == "purnimanta"


def test_month_overview_honours_the_opt_out(client):
    payload = client.get(
        f"/month-overview?year=2026&month=6&lat={LAT}&lon={LON}&calendar_system=amanta"
    ).get_json()

    assert payload["hindu_month"] == "Adhika Jyeshtha"
    assert payload["calendar_system"] == "amanta"


def test_month_overview_header_agrees_with_the_daily_payload(client):
    """The overview header must not drift from the daily endpoint it summarises."""
    for month in (4, 6, 10):
        payload = client.get(
            f"/month-overview?year=2026&month={month}&lat={LAT}&lon={LON}"
        ).get_json()
        daily = generate_location_panchang(f"2026-{month:02d}-01", lat=LAT, lon=LON)
        assert payload["hindu_month"] == _month(daily)["name"], f"month {month}"


def test_generate_panchang_endpoint_honours_the_opt_out(client):
    body = {"date": "2026-04-02", "lat": LAT, "lon": LON}
    default = client.post("/generate-panchang", json=body).get_json()
    amanta = client.post(
        "/generate-panchang", json={**body, "calendar_system": "amanta"}
    ).get_json()

    assert _month(default)["name"] == "Vaishakha"
    assert _month(amanta)["name"] == "Chaitra"


def test_unknown_calendar_system_is_rejected(client):
    response = client.post(
        "/generate-panchang",
        json={"date": "2026-04-02", "lat": LAT, "lon": LON, "calendar_system": "lunisolar"},
    )
    assert response.status_code == 400
    assert "calendar_system" in response.get_json()["error"]
