"""
db_generator.py — Pre-compute all Panchang data into a SQLite database.

Generates one row per calendar date for 1950-01-01 through 2075-12-31.
All datetimes are stored as UTC ISO strings.  Jain-specific offsets are NOT
applied; this DB stores raw Vedic/Hindu values only.

Usage (CLI for testing):
    python db_generator.py
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import swisseph as swe

from astronomy import (
    build_eclipse_date_sets,
    get_ayanamsa,
    get_moonrise,
    get_moonset,
    get_sunrise,
    get_sunset,
    jd_to_zoned_datetime,
    local_date_anchor_jd,
    get_planetary_longitude,
)
from panchang import (
    NAKSHATRA_NAMES,
    VARA_NAMES,
    calculate_karana_details,
    calculate_rahu_kaal,
    find_chaitra_shukla_1,
    generate_daily_panchang,
    get_hindu_month,
    get_shaka_samvat,
    get_tithi_start_jd,
    get_nakshatra_start_jd,
    get_yoga_start_jd,
    get_vara_from_date,
    get_vikram_samvat,
    is_kshaya_month,
)
from choghadiya_service import calculate_choghadiya_slots

_DATE_START = date(1950, 1, 1)
_DATE_END = date(2075, 12, 31)
_BATCH_SIZE = 500

_CREATE_DAYS = """
CREATE TABLE IF NOT EXISTS panchang_days (
    date                    TEXT PRIMARY KEY,
    sunrise                 TEXT,
    sunset                  TEXT,
    moonrise                TEXT,
    moonset                 TEXT,
    tithi_number            INTEGER,
    tithi_name              TEXT,
    tithi_start             TEXT,
    tithi_end               TEXT,
    paksha                  TEXT,
    nakshatra_name          TEXT,
    nakshatra_start         TEXT,
    nakshatra_end           TEXT,
    yoga_name               TEXT,
    yoga_start              TEXT,
    yoga_end                TEXT,
    karana_1_name           TEXT,
    karana_1_end            TEXT,
    karana_2_name           TEXT,
    karana_2_end            TEXT,
    vara                    TEXT,
    lunar_month             TEXT,
    lunar_month_type        TEXT,
    vikram_samvat           INTEGER,
    shaka_samvat            INTEGER,
    rahu_kalam_start        TEXT,
    rahu_kalam_end          TEXT,
    gulika_kalam_start      TEXT,
    gulika_kalam_end        TEXT,
    yamaganda_start         TEXT,
    yamaganda_end           TEXT,
    abhijit_muhurta_start   TEXT,
    abhijit_muhurta_end     TEXT,
    choghadiya_day          TEXT,
    choghadiya_night        TEXT,
    hora                    TEXT,
    surya_grahan            INTEGER,
    chandra_grahan          INTEGER,
    ayanamsa_value          REAL,
    generated_at            TEXT,
    swisseph_version        TEXT
)
"""

_CREATE_META = """
CREATE TABLE IF NOT EXISTS meta (
    city_name               TEXT,
    city_slug               TEXT,
    latitude                REAL,
    longitude               REAL,
    timezone                TEXT,
    date_range_start        TEXT,
    date_range_end          TEXT,
    generated_at            TEXT,
    swisseph_version        TEXT,
    ayanamsa                TEXT
)
"""

_INSERT_DAY = """
INSERT OR REPLACE INTO panchang_days VALUES (
    :date, :sunrise, :sunset, :moonrise, :moonset,
    :tithi_number, :tithi_name, :tithi_start, :tithi_end, :paksha,
    :nakshatra_name, :nakshatra_start, :nakshatra_end,
    :yoga_name, :yoga_start, :yoga_end,
    :karana_1_name, :karana_1_end, :karana_2_name, :karana_2_end,
    :vara, :lunar_month, :lunar_month_type,
    :vikram_samvat, :shaka_samvat,
    :rahu_kalam_start, :rahu_kalam_end,
    :gulika_kalam_start, :gulika_kalam_end,
    :yamaganda_start, :yamaganda_end,
    :abhijit_muhurta_start, :abhijit_muhurta_end,
    :choghadiya_day, :choghadiya_night, :hora,
    :surya_grahan, :chandra_grahan,
    :ayanamsa_value, :generated_at, :swisseph_version
)
"""


def _jd_to_utc_iso(jd: float) -> str | None:
    if not jd or jd <= 0:
        return None
    try:
        y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
        utc_dt = datetime(int(y), int(m), int(d), tzinfo=timezone.utc) + timedelta(hours=h)
        return utc_dt.isoformat(timespec="seconds")
    except Exception:
        return None


def _tz_offset_hours(tz_name: str, year: int) -> float:
    tz = ZoneInfo(tz_name)
    dt = datetime(year, 6, 15, tzinfo=tz)
    offset = dt.utcoffset()
    if offset is None:
        return 5.5
    return offset.total_seconds() / 3600.0


def _compute_samvat_cache(
    year: int,
    lat: float,
    lon: float,
    tz_name: str,
    cache: dict[int, date],
) -> date:
    if year not in cache:
        tz_offset = _tz_offset_hours(tz_name, year)
        cache[year] = find_chaitra_shukla_1(year, lat, lon, tz_offset)
    return cache[year]


def _slots_for_db(slots: list[dict], period: str) -> str:
    """Extract day or night slots and return as compact JSON array."""
    filtered = [
        {"name": s["name"], "start": s["start_utc"], "end": s["end_utc"]}
        for s in slots
        if s["period"] == period
    ]
    return json.dumps(filtered, ensure_ascii=False)


def _compute_day_row(
    local_date: date,
    lat: float,
    lon: float,
    tz_name: str,
    solar_eclipse_dates: set[str],
    lunar_eclipse_dates: set[str],
    cs1_cache: dict[int, date],
    swisseph_ver: str,
    generated_at: str,
    ayanamsa: str = "Lahiri",
) -> dict:
    date_str = local_date.isoformat()
    anchor_jd = local_date_anchor_jd(local_date, tz_name)

    sunrise_jd = get_sunrise(anchor_jd, lat, lon)
    sunset_jd = get_sunset(anchor_jd, lat, lon)
    moonrise_jd = get_moonrise(anchor_jd, lat, lon)
    moonset_jd = get_moonset(anchor_jd, lat, lon)

    next_anchor_jd = local_date_anchor_jd(local_date + timedelta(days=1), tz_name)
    next_sunrise_jd = get_sunrise(next_anchor_jd, lat, lon)

    # Use Jain reference time (Sunrise + 2h24m / 2.4 hrs); fall back to anchor if sunrise failed
    ref_jd = (sunrise_jd + (2.4 / 24.0)) if sunrise_jd and sunrise_jd > 0 else anchor_jd

    sun_lon = get_planetary_longitude(ref_jd, "Sun", ayanamsa)
    moon_lon = get_planetary_longitude(ref_jd, "Moon", ayanamsa)

    # ── Panchang elements ────────────────────────────────────────────────────
    panchang = generate_daily_panchang(ref_jd, ayanamsa, sun_lon, moon_lon, local_date)

    tithi_idx = panchang["Tithi_Index"]
    tithi_end_jd = panchang["Tithi_End_JD"]
    tithi_start_jd = get_tithi_start_jd(ref_jd, tithi_idx, sun_lon, moon_lon, ayanamsa)

    nak_idx = panchang["Nakshatra_Index"]
    nak_end_jd = panchang["Nakshatra_End_JD"]
    nak_start_jd = get_nakshatra_start_jd(ref_jd, nak_idx, moon_lon, ayanamsa)

    yoga_idx = panchang["Yoga_Index"]
    yoga_end_jd = panchang["Yoga_End_JD"]
    yoga_start_jd = get_yoga_start_jd(ref_jd, yoga_idx, sun_lon, moon_lon, ayanamsa)

    # ── Karana (two per day) ─────────────────────────────────────────────────
    k1 = panchang  # karana_1 data is in panchang result
    k1_end_jd = panchang["Karana_End_JD"]
    try:
        k2 = calculate_karana_details(k1_end_jd + 0.0001, ayanamsa)
        k2_name = k2["Karana_Name"]
        k2_end_jd = k2["Karana_End_JD"]
    except Exception:
        k2_name = None
        k2_end_jd = None

    # ── Weekday / Vara ───────────────────────────────────────────────────────
    weekday = get_vara_from_date(local_date)
    vara_name = VARA_NAMES[weekday]

    # ── Rahu Kaal ────────────────────────────────────────────────────────────
    if sunrise_jd and sunset_jd and sunrise_jd > 0 and sunset_jd > 0:
        rahu = calculate_rahu_kaal(sunrise_jd, sunset_jd, weekday)
        rahu_start = _jd_to_utc_iso(rahu["start_jd"])
        rahu_end = _jd_to_utc_iso(rahu["end_jd"])
    else:
        rahu_start = rahu_end = None

    # ── Hindu month & lunar month type ───────────────────────────────────────
    month_name, _, is_adhika = get_hindu_month(ref_jd, ayanamsa)
    try:
        kshaya = is_kshaya_month(ref_jd, ayanamsa)
    except Exception:
        kshaya = False
    if kshaya:
        lunar_month_type = "Kshaya"
    elif is_adhika:
        lunar_month_type = "Adhika"
    else:
        lunar_month_type = "Nija"

    # ── Samvat years ─────────────────────────────────────────────────────────
    cs1 = _compute_samvat_cache(local_date.year, lat, lon, tz_name, cs1_cache)
    vikram = get_vikram_samvat(local_date, cs1)
    shaka = get_shaka_samvat(local_date, cs1)

    # ── Paksha ───────────────────────────────────────────────────────────────
    paksha = "Shukla" if tithi_idx <= 15 else "Krishna"

    # ── Choghadiya ───────────────────────────────────────────────────────────
    if (sunrise_jd and sunset_jd and next_sunrise_jd
            and sunrise_jd > 0 and sunset_jd > 0 and next_sunrise_jd > 0):
        slots = calculate_choghadiya_slots(
            sunrise_jd, sunset_jd, next_sunrise_jd, weekday, tz_name, local_date
        )
        chog_day = _slots_for_db(slots, "day")
        chog_night = _slots_for_db(slots, "night")
    else:
        chog_day = chog_night = json.dumps([])

    # ── Eclipse ──────────────────────────────────────────────────────────────
    surya_grahan = 1 if date_str in solar_eclipse_dates else 0
    chandra_grahan = 1 if date_str in lunar_eclipse_dates else 0

    # ── Ayanamsa value for this date ─────────────────────────────────────────
    ayanamsa_val = get_ayanamsa(ref_jd, ayanamsa)

    return {
        "date": date_str,
        "sunrise": _jd_to_utc_iso(sunrise_jd),
        "sunset": _jd_to_utc_iso(sunset_jd),
        "moonrise": _jd_to_utc_iso(moonrise_jd),
        "moonset": _jd_to_utc_iso(moonset_jd),
        "tithi_number": tithi_idx,
        "tithi_name": panchang["Tithi_Name"],
        "tithi_start": _jd_to_utc_iso(tithi_start_jd),
        "tithi_end": _jd_to_utc_iso(tithi_end_jd),
        "paksha": paksha,
        "nakshatra_name": NAKSHATRA_NAMES[nak_idx - 1],
        "nakshatra_start": _jd_to_utc_iso(nak_start_jd),
        "nakshatra_end": _jd_to_utc_iso(nak_end_jd),
        "yoga_name": panchang["Yoga_Name"],
        "yoga_start": _jd_to_utc_iso(yoga_start_jd),
        "yoga_end": _jd_to_utc_iso(yoga_end_jd),
        "karana_1_name": panchang["Karana_Name"],
        "karana_1_end": _jd_to_utc_iso(k1_end_jd),
        "karana_2_name": k2_name,
        "karana_2_end": _jd_to_utc_iso(k2_end_jd) if k2_end_jd else None,
        "vara": vara_name,
        "lunar_month": month_name,
        "lunar_month_type": lunar_month_type,
        "vikram_samvat": vikram,
        "shaka_samvat": shaka,
        "rahu_kalam_start": rahu_start,
        "rahu_kalam_end": rahu_end,
        "gulika_kalam_start": None,
        "gulika_kalam_end": None,
        "yamaganda_start": None,
        "yamaganda_end": None,
        "abhijit_muhurta_start": None,
        "abhijit_muhurta_end": None,
        "choghadiya_day": chog_day,
        "choghadiya_night": chog_night,
        "hora": None,
        "surya_grahan": surya_grahan,
        "chandra_grahan": chandra_grahan,
        "ayanamsa_value": ayanamsa_val,
        "generated_at": generated_at,
        "swisseph_version": swisseph_ver,
    }


def generate_panchang_db(
    city_name: str,
    city_slug: str,
    latitude: float,
    longitude: float,
    timezone_str: str,
    db_path: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Generate a complete Panchang SQLite database for the given city.

    Args:
        city_name: Human-readable city name (stored in meta).
        city_slug: Slug used in the filename (e.g. 'ahmedabad').
        latitude: Geographic latitude in decimal degrees.
        longitude: Geographic longitude in decimal degrees.
        timezone_str: IANA timezone name (e.g. 'Asia/Kolkata').
        db_path: Absolute path where the .db file will be written.
        progress_callback: Optional callable(current_day, total_days).  Called
            after each successfully written batch.

    Raises:
        Any exception from the calculation layer.  The partial DB file is
        deleted before re-raising so no incomplete databases are left on disk.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    swisseph_ver: str = swe.version

    # Build the full list of dates to process
    all_dates: list[date] = []
    cur = _DATE_START
    while cur <= _DATE_END:
        all_dates.append(cur)
        cur += timedelta(days=1)
    total_days = len(all_dates)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        # Pre-compute eclipse dates for the whole range (avoids per-day swe calls)
        if progress_callback:
            progress_callback(0, total_days)

        start_jd = swe.julday(_DATE_START.year, _DATE_START.month, _DATE_START.day, 0.0)
        end_jd = swe.julday(_DATE_END.year, _DATE_END.month, _DATE_END.day + 1, 0.0)
        solar_eclipse_dates, lunar_eclipse_dates = build_eclipse_date_sets(
            start_jd, end_jd, latitude, longitude
        )

        cs1_cache: dict[int, date] = {}
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(_CREATE_DAYS)
            conn.execute(_CREATE_META)
            conn.commit()

            batch: list[dict] = []
            days_done = 0

            for local_date in all_dates:
                row = _compute_day_row(
                    local_date=local_date,
                    lat=latitude,
                    lon=longitude,
                    tz_name=timezone_str,
                    solar_eclipse_dates=solar_eclipse_dates,
                    lunar_eclipse_dates=lunar_eclipse_dates,
                    cs1_cache=cs1_cache,
                    swisseph_ver=swisseph_ver,
                    generated_at=generated_at,
                )
                batch.append(row)
                days_done += 1

                if len(batch) >= _BATCH_SIZE:
                    conn.executemany(_INSERT_DAY, batch)
                    conn.commit()
                    batch.clear()
                    if progress_callback:
                        progress_callback(days_done, total_days)

            # Flush remaining rows
            if batch:
                conn.executemany(_INSERT_DAY, batch)
                conn.commit()
                if progress_callback:
                    progress_callback(days_done, total_days)

            # Write meta
            conn.execute(
                "INSERT INTO meta VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    city_name, city_slug, latitude, longitude, timezone_str,
                    _DATE_START.isoformat(), _DATE_END.isoformat(),
                    generated_at, swisseph_ver, "Lahiri",
                ),
            )
            conn.commit()
        finally:
            conn.close()

    except Exception:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
        raise


if __name__ == "__main__":
    import sys

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    db_path = os.path.join(data_dir, "panchang_ahmedabad_test.db")

    # Quick test: only generate 30 days
    _DATE_END_SAVED = _DATE_END
    import db_generator as _self
    _self._DATE_END = date(1950, 1, 31)  # type: ignore[attr-defined]

    def _progress(done: int, total: int) -> None:
        pct = int(done / total * 100) if total else 0
        print(f"\r  {done}/{total} ({pct}%)", end="", flush=True)

    print(f"Generating test DB: {db_path}")
    try:
        generate_panchang_db(
            city_name="Ahmedabad",
            city_slug="ahmedabad_test",
            latitude=23.0225,
            longitude=72.5714,
            timezone_str="Asia/Kolkata",
            db_path=db_path,
            progress_callback=_progress,
        )
        print(f"\nDone. DB written to {db_path}")
    except Exception as exc:
        print(f"\nFailed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        _self._DATE_END = _DATE_END_SAVED
