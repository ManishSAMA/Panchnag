"""Location resolution behaviour.

`geocode_city` is memoised. A memoised function that hands back a mutable
object shares one instance with every caller, so a caller that adjusts the
result -- overriding a coordinate, tagging it with a display label -- silently
rewrites what every later caller receives. These tests pin the caller-isolation
contract.
"""

import location_service
from location_service import geocode_city


def _stub_nominatim(monkeypatch, rows):
    calls = {"n": 0}

    def fake_get(path, params):
        calls["n"] += 1
        return rows

    monkeypatch.setattr(location_service, "_nominatim_get", fake_get)
    return calls


_AHMEDABAD = [{"display_name": "Ahmedabad, Gujarat, India", "lat": "23.0225", "lon": "72.5714"}]


def test_geocode_city_memoises_repeat_lookups(monkeypatch):
    geocode_city.cache_clear()
    calls = _stub_nominatim(monkeypatch, _AHMEDABAD)

    first = geocode_city("Ahmedabad")
    second = geocode_city("Ahmedabad")

    assert first == second
    assert calls["n"] == 1, "a repeat lookup must not re-hit the geocoder"


def test_mutating_a_geocode_result_cannot_corrupt_the_cache(monkeypatch):
    geocode_city.cache_clear()
    _stub_nominatim(monkeypatch, _AHMEDABAD)

    first = geocode_city("Ahmedabad")
    first["lat"] = 0.0
    first["display_name"] = "clobbered"

    second = geocode_city("Ahmedabad")

    assert second["lat"] == 23.0225
    assert second["display_name"] == "Ahmedabad, Gujarat, India"
