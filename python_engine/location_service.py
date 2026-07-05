"""
location_service.py - Geocoding and timezone resolution helpers.

Uses OpenStreetMap Nominatim for lightweight, free geocoding.
"""

from __future__ import annotations

from functools import lru_cache

import requests
from timezonefinder import TimezoneFinder

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "jain-panchang-app/1.0 (local development)"

_TZ_FINDER = TimezoneFinder()


def _nominatim_get(path: str, params: dict) -> list[dict]:
    response = requests.get(
        f"{NOMINATIM_BASE_URL}/{path}",
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def search_locations(query: str, limit: int = 5) -> list[dict]:
    """Return lightweight location suggestions for an autocomplete UI."""
    query = query.strip()
    if not query:
        return []

    data = _nominatim_get(
        "search",
        {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": max(1, min(limit, 10)),
        },
    )
    return [
        {
            "display_name": row["display_name"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        }
        for row in data
    ]


@lru_cache(maxsize=128)
def geocode_city(city_name: str) -> dict:
    """Resolve a city/location string to coordinates."""
    matches = search_locations(city_name, limit=1)
    if not matches:
        raise ValueError(f"No coordinates found for '{city_name}'.")
    return matches[0]


def get_timezone_name(lat: float, lon: float) -> str:
    """Resolve an IANA timezone from coordinates."""
    tz_name = _TZ_FINDER.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        tz_name = _TZ_FINDER.certain_timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError("Could not determine timezone for the given coordinates.")
    return tz_name
