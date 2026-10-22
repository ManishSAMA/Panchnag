"""Parity fixtures: the engine's answers, exported for the Dart engine's tests.

The Python engine is the reference; the Dart port in mobile/ must reproduce
what is written here. Design: plans/mobile-phase1-fixtures.md.
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
from dataclasses import asdict, dataclass
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import swisseph

from astronomy import SUNRISE_RULES, get_ayanamsa, get_planetary_longitude
from choghadiya_service import calculate_choghadiya_slots
from jain_observances.festival_service import generate_jain_festivals
from panchang import HINDU_MONTH_NAMES, get_hindu_month
from panchang_service import generate_location_panchang, resolve_location
from request_parsing import VALID_PROFILES

# Bump when a fixture's shape changes, so the Dart side can refuse a stale set.
SCHEMA_VERSION = 2

PROFILES: tuple[str, ...] = VALID_PROFILES


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


def _amanta_month(jd: float) -> dict:
    name, _, is_adhika = get_hindu_month(jd)
    return {
        "index": HINDU_MONTH_NAMES.index(name.removeprefix("Adhika ")),
        "name": name,
        "is_adhika": is_adhika,
    }


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
        # The engine names the month at the Jain reference instant in both systems.
        "month_amanta": _amanta_month(panchang["jain_tithi"]["reference"]["jd"]),
        "vikram_samvat": panchang["vikram_samvat"],
        "vira_nirvana_samvat": panchang["vira_nirvana_samvat"],
        "choghadiya": [slot["name"] for slot in choghadiya],
    }


def _dumps(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_gzip(path: Path, obj: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 and no embedded filename keep regenerated files byte-identical.
    path.write_bytes(gzip.compress(_dumps(obj), mtime=0))
    return path


def read_fixture(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def _dates(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError(f"Range ends ({end}) before it starts ({start}).")
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def write_days(
    location: FixtureLocation, *, start: date, end: date, sunrise_rule: str, out_dir: Path
) -> Path:
    days = _dates(start, end)
    return _write_gzip(
        out_dir / location.slug / sunrise_rule / "days.json.gz",
        {
            "schema_version": SCHEMA_VERSION,
            "location": asdict(location),
            "sunrise_rule": sunrise_rule,
            "days": [day_row(location, d, sunrise_rule=sunrise_rule) for d in days],
        },
    )


def _astro_sample(jd: float) -> dict:
    sun, _ = swisseph.calc_ut(jd, swisseph.SUN, swisseph.FLG_SWIEPH)
    moon, _ = swisseph.calc_ut(jd, swisseph.MOON, swisseph.FLG_SWIEPH)
    sun_eq, _ = swisseph.calc_ut(jd, swisseph.SUN, swisseph.FLG_SWIEPH | swisseph.FLG_EQUATORIAL)
    true_obliquity, _mean, nutation_longitude, nutation_obliquity, *_ = swisseph.calc_ut(
        jd, swisseph.ECL_NUT, 0
    )[0]
    return {
        "jd_ut": jd,
        "delta_t": swisseph.deltat(jd) * 86400.0,
        "sun_apparent": sun[0],
        "moon_apparent": moon[0],
        "sun_ra": sun_eq[0],
        "sun_dec": sun_eq[1],
        "true_obliquity": true_obliquity,
        "nutation_longitude": nutation_longitude,
        "nutation_obliquity": nutation_obliquity,
        "gast_hours": swisseph.sidtime(jd),
        "ayanamsa": get_ayanamsa(jd, "Lahiri"),
        "sun_sidereal": get_planetary_longitude(jd, "Sun", "Lahiri"),
        "moon_sidereal": get_planetary_longitude(jd, "Moon", "Lahiri"),
    }


def astro_samples(*, start: date, end: date) -> list[dict]:
    """Positions at 0h UT on every day of the range, independent of any location."""
    return [
        _astro_sample(swisseph.julday(d.year, d.month, d.day, 0.0)) for d in _dates(start, end)
    ]


def write_astro(*, out_dir: Path, start: date, end: date) -> Path:
    return _write_gzip(
        out_dir / "astro.json.gz",
        {"schema_version": SCHEMA_VERSION, "samples": astro_samples(start=start, end=end)},
    )


def write_manifest(*, out_dir: Path, plan: FixturePlan) -> Path:
    path = out_dir / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "swisseph_version": swisseph.version,
        "sunrise_rules": list(plan.sunrise_rules),
        "profiles": list(plan.profiles),
        "locations": [
            asdict(entry.location) | {"start": entry.start.isoformat(), "end": entry.end.isoformat()}
            for entry in plan.entries
        ],
    }
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def festival_rows(
    location: FixtureLocation, year: int, *, profile: str, sunrise_rule: str
) -> list[dict]:
    """The engine's festival occurrences for one year, reduced to ids, dates and status."""
    # The engine accepts any profile string and quietly returns the wrong festivals.
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of {PROFILES} (got {profile!r}).")
    festivals = generate_jain_festivals(
        year, location.lat, location.lon, profile=profile, sunrise_rule=sunrise_rule
    )["festivals"]
    return sorted(
        (
            {key: f[key] for key in ("id", "occurrence_id", "start_date", "end_date", "status")}
            for f in festivals
        ),
        key=lambda row: (row["start_date"], row["occurrence_id"]),
    )


def write_festivals(
    location: FixtureLocation,
    *,
    start_year: int,
    end_year: int,
    profile: str,
    sunrise_rule: str,
    out_dir: Path,
) -> Path:
    if end_year < start_year:
        raise ValueError(f"Range ends ({end_year}) before it starts ({start_year}).")
    return _write_gzip(
        out_dir / location.slug / sunrise_rule / f"festivals.{profile}.json.gz",
        {
            "schema_version": SCHEMA_VERSION,
            "location": asdict(location),
            "sunrise_rule": sunrise_rule,
            "profile": profile,
            "years": {
                str(year): festival_rows(location, year, profile=profile, sunrise_rule=sunrise_rule)
                for year in range(start_year, end_year + 1)
            },
        },
    )


FULL_RANGE = (date(2016, 1, 1), date(2040, 12, 31))
CORE_SHORT_RANGE = (date(2026, 1, 1), date(2027, 12, 31))
_CORE_FULL_RANGE_CITIES = ("Delhi", "Ahmedabad", "Mumbai")
_RANDOM_COUNT = {"core": 4, "full": 8, "custom": 0}
RANDOM_SEED = 2026
_REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = _REPO_ROOT / "mobile" / "packages" / "panchang_engine" / "test" / "fixtures"


@dataclass(frozen=True)
class PlanEntry:
    location: FixtureLocation
    start: date
    end: date


@dataclass(frozen=True)
class Job:
    """One output file: a location's days (profile None) or one profile's festivals."""

    location: FixtureLocation
    sunrise_rule: str
    start: date
    end: date
    profile: str | None = None

    @property
    def cost(self) -> int:
        # One festival year costs about as much as fifty days (~4.4 s vs ~86 ms).
        if self.profile is None:
            return (self.end - self.start).days + 1
        return (self.end.year - self.start.year + 1) * 50

    def run(self, out_dir: Path) -> Path:
        if self.profile is None:
            return write_days(
                self.location, start=self.start, end=self.end,
                sunrise_rule=self.sunrise_rule, out_dir=out_dir,
            )
        return write_festivals(
            self.location, start_year=self.start.year, end_year=self.end.year,
            profile=self.profile, sunrise_rule=self.sunrise_rule, out_dir=out_dir,
        )


@dataclass(frozen=True)
class FixturePlan:
    entries: tuple[PlanEntry, ...]
    sunrise_rules: tuple[str, ...]
    profiles: tuple[str, ...]

    @property
    def jobs(self) -> tuple[Job, ...]:
        return tuple(
            Job(entry.location, rule, entry.start, entry.end, profile)
            for entry in self.entries
            for rule in self.sunrise_rules
            for profile in (None, *self.profiles)
        )


def _run_job(job: Job, out_dir: Path) -> Path:
    return job.run(out_dir)


def run_plan(plan: FixturePlan, *, out_dir: Path, workers: int) -> None:
    # Longest jobs first, so a slow one never starts last and holds up the pool.
    jobs = sorted(plan.jobs, key=lambda job: -job.cost)
    if workers == 1:
        for job in jobs:
            job.run(out_dir)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            list(pool.map(_run_job, jobs, [out_dir] * len(jobs)))
    write_astro(
        out_dir=out_dir,
        start=min(entry.start for entry in plan.entries),
        end=max(entry.end for entry in plan.entries),
    )
    write_manifest(out_dir=out_dir, plan=plan)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the Python engine's answers as parity fixtures for the Dart engine.",
    )
    parser.add_argument("--set", choices=("core", "full", "custom"), default="core")
    parser.add_argument("--random", type=int, help="random locations to add (default: core 4, full 8)")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--name", default="custom")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--start", type=date.fromisoformat, default=FULL_RANGE[0])
    parser.add_argument("--end", type=date.fromisoformat, default=FULL_RANGE[1])
    parser.add_argument("--rule", action="append", choices=SUNRISE_RULES, dest="rules")
    parser.add_argument("--profile", action="append", choices=PROFILES, dest="profiles")
    parser.add_argument("--out", type=Path, help="output directory (default: the set's fixtures folder)")
    parser.add_argument("--workers", type=int, default=1)
    return parser


def _entries(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[PlanEntry]:
    if args.set == "custom":
        if args.lat is None or args.lon is None:
            parser.error("--set custom needs --lat and --lon")
        return [PlanEntry(custom_location(name=args.name, lat=args.lat, lon=args.lon), args.start, args.end)]
    if args.set == "full":
        return [PlanEntry(loc, *FULL_RANGE) for loc in DEFAULT_LOCATIONS]
    return [
        PlanEntry(loc, *(FULL_RANGE if loc.name in _CORE_FULL_RANGE_CITIES else CORE_SHORT_RANGE))
        for loc in DEFAULT_LOCATIONS
    ]


def _plan_from_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> FixturePlan:
    count = _RANDOM_COUNT[args.set] if args.random is None else args.random
    random_range = FULL_RANGE if args.set == "full" else CORE_SHORT_RANGE
    return FixturePlan(
        entries=(
            *_entries(args, parser),
            *(PlanEntry(loc, *random_range) for loc in random_locations(count=count, seed=args.seed)),
        ),
        sunrise_rules=tuple(args.rules or SUNRISE_RULES),
        profiles=tuple(args.profiles or PROFILES),
    )


def parse_plan(argv: list[str]) -> FixturePlan:
    parser = _parser()
    return _plan_from_args(parser.parse_args(argv), parser)


def main(argv: list[str]) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    plan = _plan_from_args(args, parser)
    out_dir = args.out or FIXTURES_DIR / args.set
    run_plan(plan, out_dir=out_dir, workers=args.workers)
    print(f"{len(plan.jobs)} files for {len(plan.entries)} locations -> {out_dir}")
