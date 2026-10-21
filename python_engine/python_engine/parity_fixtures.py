"""Parity fixtures: the engine's answers, exported for the Dart engine's tests.

The Python engine is the reference; the Dart port in mobile/ must reproduce
what is written here. Design: plans/mobile-phase1-fixtures.md.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import date

from choghadiya_service import calculate_choghadiya_slots
from panchang_service import generate_location_panchang, resolve_location


@dataclass(frozen=True)
class FixtureLocation:
    slug: str
    name: str
    lat: float
    lon: float
    timezone: str


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def custom_location(*, name: str, lat: float, lon: float) -> FixtureLocation:
    resolved = resolve_location(lat=lat, lon=lon)
    return FixtureLocation(
        slug=_slugify(name),
        name=name,
        lat=resolved.lat,
        lon=resolved.lon,
        timezone=resolved.timezone,
    )


DEFAULT_LOCATIONS: tuple[FixtureLocation, ...] = tuple(
    custom_location(name=name, lat=lat, lon=lon)
    for name, lat, lon in (
        ("Delhi", 28.6139, 77.2090),
        ("Ahmedabad", 23.0225, 72.5714),
        ("Mumbai", 19.0760, 72.8777),
        ("Surat", 21.1702, 72.8311),
        ("Palitana", 21.5222, 71.8237),
        ("Jaipur", 26.9124, 75.7873),
        ("Udaipur", 24.5854, 73.7125),
        ("Indore", 22.7196, 75.8577),
        ("Kolkata", 22.5726, 88.3639),
        ("Bengaluru", 12.9716, 77.5946),
        ("Chennai", 13.0827, 80.2707),
        # High latitude with daylight saving: stresses sunrise and the civil-day anchor.
        ("London", 51.5074, -0.1278),
        # Western hemisphere: the civil date and the UT date differ for much of the day.
        ("New York", 40.7128, -74.0060),
    )
)

# India's bounding box, and a latitude cap that keeps a sunrise on every day of the year.
_INDIA_LAT = (8.0, 35.0)
_INDIA_LON = (68.0, 97.0)
_MAX_ABS_LAT = 60.0


def random_locations(*, count: int, seed: int) -> tuple[FixtureLocation, ...]:
    """Seeded sample: the first half inside India, the rest anywhere with |lat| <= 60."""
    rng = random.Random(seed)
    in_india = (count + 1) // 2

    def draw(i: int) -> tuple[float, float]:
        if i < in_india:
            return rng.uniform(*_INDIA_LAT), rng.uniform(*_INDIA_LON)
        return rng.uniform(-_MAX_ABS_LAT, _MAX_ABS_LAT), rng.uniform(-180.0, 180.0)

    return tuple(
        custom_location(name=f"random s{seed} {i:02d}", lat=round(lat, 4), lon=round(lon, 4))
        for i, (lat, lon) in enumerate(map(draw, range(count)))
    )


def _jd(event: dict | None) -> float | None:
    return event["jd"] if event else None


def day_row(location: FixtureLocation, local_date: date, *, sunrise_rule: str) -> dict:
    """One civil day as the engine reports it, reduced to JSON-ready instants and indices.

    Times are UT Julian Days, so the display clock never affects a fixture.
    """
    payload = generate_location_panchang(
        local_date, lat=location.lat, lon=location.lon, sunrise_rule=sunrise_rule
    )
    events = payload["events"]
    panchang = payload["panchang"]
    sunrise, sunset, next_sunrise = (
        events[key]["jd"] for key in ("sunrise", "sunset", "next_sunrise")
    )
    choghadiya = calculate_choghadiya_slots(
        sunrise, sunset, next_sunrise, panchang["vara"]["index"], location.timezone, local_date
    )
    return {
        "date": local_date.isoformat(),
        "sunrise": sunrise,
        "sunset": sunset,
        "next_sunrise": next_sunrise,
        "tithi": [{"index": t["index"], "ends": _jd(t["ends"])} for t in panchang["tithi"]],
        "jain_tithi": {
            "index": panchang["jain_tithi"]["index"],
            "ends": _jd(panchang["jain_tithi"]["ends"]),
            "reference": panchang["jain_tithi"]["reference"]["jd"],
        },
        "nakshatra": {
            "index": panchang["nakshatra"]["index"],
            "ends": _jd(panchang["nakshatra"]["ends"]),
        },
        "vara": panchang["vara"]["index"],
        "month": {
            "index": panchang["hindu_month"]["index"],
            "name": panchang["hindu_month"]["name"],
            "is_adhika": panchang["hindu_month"]["is_adhika"],
        },
        "vikram_samvat": panchang["vikram_samvat"],
        "vira_nirvana_samvat": panchang["vira_nirvana_samvat"],
        "choghadiya": [slot["name"] for slot in choghadiya],
    }
