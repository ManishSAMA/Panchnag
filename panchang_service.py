"""
panchang_service.py - Location-aware daily Panchang assembly.

Domain rules implemented here:
1. Udaya Tithi:
   The civil day's primary Tithi is the Tithi prevailing at local sunrise.
2. Sunrise-bound daily Panchang:
   Nakshatra/Yoga/Karana/Vara for the returned daily summary are evaluated
   from the same sunrise reference so the day is internally consistent.
3. Sunrise + 2h45m rule:
   Some domain-specific observances use a post-sunrise reference point
   2 hours 45 minutes after sunrise. That reference is exposed separately
   and never overrides the day's Udaya Tithi label.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from astronomy import (
    get_all_planet_positions,
    get_ayanamsa,
    get_moonrise,
    get_moonset,
    get_planetary_longitude,
    get_rashi_name,
    get_sunrise,
    get_sunset,
    jd_to_iso_local_string,
    jd_to_zoned_datetime,
    local_date_anchor_jd,
)
from location_service import geocode_city, get_timezone_name
from panchang import NAKSHATRA_NAMES, TITHI_NAMES, generate_daily_panchang, get_nakshatra, get_tithi

SPECIAL_RULE_OFFSET = timedelta(hours=2, minutes=45)


def _serialize_event(jd: float, tz_name: str) -> dict:
    local_dt = jd_to_zoned_datetime(jd, tz_name)
    if local_dt is None:
        return {"jd": 0.0, "local": "", "time": ""}
    return {
        "jd": round(jd, 8),
        "local": local_dt.isoformat(timespec="seconds"),
        "time": local_dt.strftime("%H:%M:%S"),
    }


def _element_payload(panchang_data: dict, next_sunrise_jd: float, tz_name: str) -> dict:
    return {
        "tithi": {
            "index": panchang_data["Tithi_Index"],
            "name": panchang_data["Tithi_Name"],
            "ends": _serialize_event(panchang_data["Tithi_End_JD"], tz_name),
            "continues_past_next_sunrise": panchang_data["Tithi_End_JD"] >= next_sunrise_jd,
        },
        "nakshatra": {
            "index": panchang_data["Nakshatra_Index"],
            "name": panchang_data["Nakshatra_Name"],
            "pada": panchang_data["Nakshatra_Pada"],
            "ends": _serialize_event(panchang_data["Nakshatra_End_JD"], tz_name),
            "continues_past_next_sunrise": panchang_data["Nakshatra_End_JD"] >= next_sunrise_jd,
        },
        "yoga": {
            "index": panchang_data["Yoga_Index"],
            "name": panchang_data["Yoga_Name"],
        },
        "karana": {
            "index": panchang_data["Karana_Index"],
            "name": panchang_data["Karana_Name"],
        },
        "vara": {
            "index": panchang_data["Vara_Index"],
            "name": panchang_data["Vara_Name"],
        },
    }


def _special_reference_payload(reference_jd: float, ayanamsa_name: str, tz_name: str) -> dict:
    sun_lon = get_planetary_longitude(reference_jd, "Sun", ayanamsa_name)
    moon_lon = get_planetary_longitude(reference_jd, "Moon", ayanamsa_name)

    tithi_idx = get_tithi(sun_lon, moon_lon)
    nakshatra_idx = get_nakshatra(moon_lon)

    return {
        "rule": "sunrise_plus_2h45m",
        "reference": _serialize_event(reference_jd, tz_name),
        "tithi": {
            "index": tithi_idx,
            "name": TITHI_NAMES[tithi_idx - 1],
        },
        "nakshatra": {
            "index": nakshatra_idx,
            "name": NAKSHATRA_NAMES[nakshatra_idx - 1],
        },
    }


def _coerce_date(input_date: str | date) -> date:
    if isinstance(input_date, date):
        return input_date
    return datetime.strptime(input_date, "%Y-%m-%d").date()


def resolve_location(city: str | None = None, lat: float | None = None, lon: float | None = None) -> dict:
    """Resolve either a city name or manual coordinates to a normalized location payload."""
    if lat is not None and lon is not None:
        return {
            "location": city or "Custom coordinates",
            "lat": float(lat),
            "lon": float(lon),
        }

    if city:
        match = geocode_city(city)
        return {
            "location": match["display_name"],
            "lat": match["lat"],
            "lon": match["lon"],
        }

    raise ValueError("Provide either a city name or both latitude and longitude.")


def generate_location_panchang(
    input_date: str | date,
    *,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    ayanamsa_name: str = "Lahiri",
) -> dict:
    """Generate a daily Panchang JSON payload for a specific local date and location."""
    local_date = _coerce_date(input_date)
    location = resolve_location(city=city, lat=lat, lon=lon)
    tz_name = get_timezone_name(location["lat"], location["lon"])

    day_start_jd = local_date_anchor_jd(local_date, tz_name, hour=0)
    next_day_start_jd = local_date_anchor_jd(local_date + timedelta(days=1), tz_name, hour=0)

    sunrise_jd = get_sunrise(day_start_jd, location["lat"], location["lon"])
    sunset_jd = get_sunset(day_start_jd, location["lat"], location["lon"])
    moonrise_jd = get_moonrise(day_start_jd, location["lat"], location["lon"])
    moonset_jd = get_moonset(day_start_jd, location["lat"], location["lon"])
    next_sunrise_jd = get_sunrise(next_day_start_jd, location["lat"], location["lon"])

    sunrise_dt = jd_to_zoned_datetime(sunrise_jd, tz_name)
    sunset_dt = jd_to_zoned_datetime(sunset_jd, tz_name)
    if sunrise_dt is None or sunset_dt is None:
        raise ValueError("Could not compute sunrise/sunset for the given date and location.")
    if sunrise_dt.date() != local_date:
        raise ValueError("Sunrise calculation did not resolve to the requested local date.")

    sunrise_planets = get_all_planet_positions(sunrise_jd, ayanamsa_name)
    daily_panchang = generate_daily_panchang(
        sunrise_jd,
        ayanamsa_name,
        sun_lon=sunrise_planets["Sun"],
        moon_lon=sunrise_planets["Moon"],
    )

    special_reference_jd = sunrise_jd + (SPECIAL_RULE_OFFSET.total_seconds() / 86400.0)
    ayanamsa_value = get_ayanamsa(sunrise_jd, ayanamsa_name)

    return {
        "location": location["location"],
        "lat": location["lat"],
        "lon": location["lon"],
        "timezone": tz_name,
        "date": local_date.isoformat(),
        "ayanamsa": {
            "name": ayanamsa_name,
            "degrees": round(ayanamsa_value, 6),
        },
        "events": {
            "sunrise": _serialize_event(sunrise_jd, tz_name),
            "sunset": _serialize_event(sunset_jd, tz_name),
            "moonrise": _serialize_event(moonrise_jd, tz_name),
            "moonset": _serialize_event(moonset_jd, tz_name),
            "next_sunrise": _serialize_event(next_sunrise_jd, tz_name),
        },
        "panchang": {
            **_element_payload(daily_panchang, next_sunrise_jd, tz_name),
            "moon_rashi": get_rashi_name(sunrise_planets["Moon"]),
            "reference_time": _serialize_event(sunrise_jd, tz_name),
        },
        "rules": {
            "primary_day_rule": "udaya_tithi",
            "notes": [
                "Daily Tithi is determined from the Tithi active at local sunrise.",
                "The +2h45m reference is provided separately for domain-specific observances only.",
            ],
            "special_reference": _special_reference_payload(
                special_reference_jd,
                ayanamsa_name,
                tz_name,
            ),
        },
        "structured": {
            "location": location["location"],
            "lat": location["lat"],
            "lon": location["lon"],
            "date": local_date.isoformat(),
            "sunrise": jd_to_iso_local_string(sunrise_jd, tz_name),
            "sunset": jd_to_iso_local_string(sunset_jd, tz_name),
            "tithi": daily_panchang["Tithi_Name"],
            "nakshatra": daily_panchang["Nakshatra_Name"],
            "yoga": daily_panchang["Yoga_Name"],
            "karana": daily_panchang["Karana_Name"],
        },
    }
