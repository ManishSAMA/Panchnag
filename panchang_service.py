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

from dataclasses import dataclass
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
from panchang import (
    JAIN_TITHI_OFFSET_DAYS,
    NAKSHATRA_NAMES,
    TITHI_NAMES,
    calculate_jain_tithi_from_sunrise,
    generate_daily_panchang,
    get_nakshatra,
    get_tithi,
)

SPECIAL_RULE_OFFSET = timedelta(hours=2, minutes=45)
JAIN_OFFSET_CHECK = timedelta(hours=2, minutes=24)


@dataclass(frozen=True)
class ResolvedLocation:
    name: str
    lat: float
    lon: float
    timezone: str


@dataclass(frozen=True)
class DailyEventSet:
    sunrise_jd: float
    sunset_jd: float
    moonrise_jd: float
    moonset_jd: float
    next_sunrise_jd: float


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
    payload = {
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
    if "Jain_Tithi_Index" in panchang_data:
        payload["jain_tithi"] = {
            "index": panchang_data["Jain_Tithi_Index"],
            "name": panchang_data["Jain_Tithi_Name"],
            "ends": _serialize_event(panchang_data["Jain_Tithi_End_JD"], tz_name),
            "continues_past_next_sunrise": panchang_data["Jain_Tithi_End_JD"] >= next_sunrise_jd,
            "reference": _serialize_event(panchang_data["Jain_Tithi_Reference_JD"], tz_name),
        }
    return payload


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


def _reference_check_payload(
    sunrise_jd: float,
    offset: timedelta,
    rule_name: str,
    ayanamsa_name: str,
    tz_name: str,
) -> dict:
    reference_jd = sunrise_jd + (offset.total_seconds() / 86400.0)
    payload = _special_reference_payload(reference_jd, ayanamsa_name, tz_name)
    payload["rule"] = rule_name
    payload["offset_minutes"] = int(offset.total_seconds() // 60)
    return payload


def calculate_jain_tithi(
    input_date: str | date,
    location: ResolvedLocation,
    ayanamsa_name: str = "Lahiri",
) -> dict:
    """Return Jain Tithi for a local date and resolved location."""
    local_date = _coerce_date(input_date)
    events = _calculate_daily_events(local_date, location)
    return calculate_jain_tithi_from_sunrise(events.sunrise_jd, ayanamsa_name)


def _coerce_date(input_date: str | date) -> date:
    if isinstance(input_date, date):
        return input_date
    return datetime.strptime(input_date, "%Y-%m-%d").date()


def _validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    lat_value = float(lat)
    lon_value = float(lon)
    if not -90.0 <= lat_value <= 90.0:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not -180.0 <= lon_value <= 180.0:
        raise ValueError("Longitude must be between -180 and 180 degrees.")
    return lat_value, lon_value


def resolve_location(city: str | None = None, lat: float | None = None, lon: float | None = None) -> ResolvedLocation:
    """Resolve either a city name or manual coordinates to a normalized location payload."""
    if (lat is None) ^ (lon is None):
        raise ValueError("Latitude and longitude must be provided together.")

    if lat is not None and lon is not None:
        lat_value, lon_value = _validate_coordinates(lat, lon)
        return ResolvedLocation(
            name=city or "Custom coordinates",
            lat=lat_value,
            lon=lon_value,
            timezone=get_timezone_name(lat_value, lon_value),
        )

    if city:
        match = geocode_city(city)
        lat_value, lon_value = _validate_coordinates(match["lat"], match["lon"])
        return ResolvedLocation(
            name=match["display_name"],
            lat=lat_value,
            lon=lon_value,
            timezone=get_timezone_name(lat_value, lon_value),
        )

    raise ValueError("Provide either a city name or both latitude and longitude.")


def _calculate_daily_events(local_date: date, location: ResolvedLocation) -> DailyEventSet:
    day_start_jd = local_date_anchor_jd(local_date, location.timezone, hour=0)
    next_day_start_jd = local_date_anchor_jd(local_date + timedelta(days=1), location.timezone, hour=0)

    sunrise_jd = get_sunrise(day_start_jd, location.lat, location.lon)
    sunset_jd = get_sunset(day_start_jd, location.lat, location.lon)
    moonrise_jd = get_moonrise(day_start_jd, location.lat, location.lon)
    moonset_jd = get_moonset(day_start_jd, location.lat, location.lon)
    next_sunrise_jd = get_sunrise(next_day_start_jd, location.lat, location.lon)

    if sunrise_jd == 0.0 or sunset_jd == 0.0 or next_sunrise_jd == 0.0:
        raise ValueError("Could not compute solar events for the given date and location.")

    sunrise_dt = jd_to_zoned_datetime(sunrise_jd, location.timezone)
    sunset_dt = jd_to_zoned_datetime(sunset_jd, location.timezone)
    if sunrise_dt is None or sunset_dt is None:
        raise ValueError("Could not compute sunrise/sunset for the given date and location.")
    if sunrise_dt.date() != local_date:
        raise ValueError("Sunrise calculation did not resolve to the requested local date.")
    if sunset_dt <= sunrise_dt:
        raise ValueError("Sunset calculation resolved before sunrise for the requested local date.")

    return DailyEventSet(
        sunrise_jd=sunrise_jd,
        sunset_jd=sunset_jd,
        moonrise_jd=moonrise_jd,
        moonset_jd=moonset_jd,
        next_sunrise_jd=next_sunrise_jd,
    )


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
    events = _calculate_daily_events(local_date, location)

    sunrise_planets = get_all_planet_positions(events.sunrise_jd, ayanamsa_name)
    daily_panchang = generate_daily_panchang(
        events.sunrise_jd,
        ayanamsa_name,
        sun_lon=sunrise_planets["Sun"],
        moon_lon=sunrise_planets["Moon"],
        local_date=local_date,
    )
    daily_panchang.update(calculate_jain_tithi_from_sunrise(events.sunrise_jd, ayanamsa_name))

    special_reference_jd = events.sunrise_jd + (SPECIAL_RULE_OFFSET.total_seconds() / 86400.0)
    ayanamsa_value = get_ayanamsa(events.sunrise_jd, ayanamsa_name)
    tz_name = location.timezone

    return {
        "location": location.name,
        "lat": location.lat,
        "lon": location.lon,
        "timezone": tz_name,
        "date": local_date.isoformat(),
        "ayanamsa": {
            "name": ayanamsa_name,
            "degrees": round(ayanamsa_value, 6),
        },
        "events": {
            "sunrise": _serialize_event(events.sunrise_jd, tz_name),
            "sunset": _serialize_event(events.sunset_jd, tz_name),
            "moonrise": _serialize_event(events.moonrise_jd, tz_name),
            "moonset": _serialize_event(events.moonset_jd, tz_name),
            "next_sunrise": _serialize_event(events.next_sunrise_jd, tz_name),
        },
        "panchang": {
            **_element_payload(daily_panchang, events.next_sunrise_jd, tz_name),
            "moon_rashi": get_rashi_name(sunrise_planets["Moon"]),
            "reference_time": _serialize_event(events.sunrise_jd, tz_name),
        },
        "rules": {
            "primary_day_rule": "udaya_tithi",
            "notes": [
                "Daily Tithi is determined from the Tithi active at local sunrise.",
                "Jain Tithi is determined from the Tithi active 2 hours 24 minutes after local sunrise.",
                "The reference snapshots are provided for comparison only and do not relabel the day's primary Tithi.",
                "The legacy special reference remains available for comparison only.",
            ],
            "special_reference": _special_reference_payload(
                special_reference_jd,
                ayanamsa_name,
                tz_name,
            ),
            "reference_checks": [
                _reference_check_payload(
                    events.sunrise_jd,
                    JAIN_OFFSET_CHECK,
                    "sunrise_plus_2h24m_candidate",
                    ayanamsa_name,
                    tz_name,
                ),
                _reference_check_payload(
                    events.sunrise_jd,
                    SPECIAL_RULE_OFFSET,
                    "sunrise_plus_2h45m_legacy",
                    ayanamsa_name,
                    tz_name,
                ),
            ],
        },
        "structured": {
            "location": location.name,
            "lat": location.lat,
            "lon": location.lon,
            "date": local_date.isoformat(),
            "sunrise": jd_to_iso_local_string(events.sunrise_jd, tz_name),
            "sunset": jd_to_iso_local_string(events.sunset_jd, tz_name),
            "tithi": daily_panchang["Tithi_Name"],
            "jain_tithi": daily_panchang["Jain_Tithi_Name"],
            "jain_tithi_reference": jd_to_iso_local_string(
                events.sunrise_jd + JAIN_TITHI_OFFSET_DAYS,
                tz_name,
            ),
            "nakshatra": daily_panchang["Nakshatra_Name"],
            "yoga": daily_panchang["Yoga_Name"],
            "karana": daily_panchang["Karana_Name"],
        },
    }
