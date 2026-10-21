"""
main.py — Command-line interface for the Panchang Generator.

Usage examples:
  # Generate 2025 for Jaipur (CSV)
  python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv

  # 2025-2030, Excel, 4 CPU workers
  python main.py --start_year 2025 --end_year 2030 --lat 26.9124 --lon 75.7873 \\
                 --format excel --workers 4

  # All formats, monthly output files
  python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 \\
                 --format all --monthly

  # Using Mumbai location + Krishnamurti ayanamsa + custom timezone
  python main.py --start_year 2025 --end_year 2025 --lat 19.0760 --lon 72.8777 \\
                 --ayanamsa Krishnamurti --tz_offset 5.5
"""

import argparse
import calendar
import os
import sys
from datetime import date, datetime, timedelta
from multiprocessing import Pool, cpu_count

# ---------------------------------------------------------------------------
# Local imports (all relative to this directory)
# ---------------------------------------------------------------------------
from astronomy import (
    local_time_to_jd,
    get_ayanamsa,
    get_all_planet_positions,
    get_sunrise, get_sunset,
    get_moonrise, get_moonset,
    jd_to_local_time_string,
    utc_offset_hours,
    AYANAMSA_SYSTEMS,
    CLOCK_MODES,
    SUNRISE_RULES,
)
from panchang import (
    calculate_bhadra_kaal,
    calculate_panchak_kaal,
    calculate_jain_tithi_from_sunrise,
    find_chaitra_shukla_1,
    find_diwali,
    generate_daily_panchang,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
)
from export import apply_element_continuity_formatting, export_data, format_row_data
from hindi_export import translate_rows_to_hindi

# ---------------------------------------------------------------------------
# Progress bar (optional tqdm, fallback to simple print)
# ---------------------------------------------------------------------------
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


def _progress(iterable, total: int, desc: str = ""):
    if HAS_TQDM:
        return tqdm(iterable, total=total, desc=desc, unit="day")
    return iterable


# ---------------------------------------------------------------------------
# Per-day computation (must be a module-level function for multiprocessing)
# ---------------------------------------------------------------------------

# Global config shared across worker processes (set once via initializer)
_G: dict = {}


def _init_worker(cfg: dict) -> None:
    """Initialize worker process with shared configuration."""
    global _G
    _G = cfg


def _compute_day(args_tuple) -> dict | None:
    """Compute all Panchang data for a single date.

    Args:
        args_tuple: (year, month, day)

    Returns:
        Row dict ready for export, or None on unrecoverable error.
    """
    year, month, day = args_tuple
    lat         = _G['lat']
    lon         = _G['lon']
    tz_label    = _G['tz_label']
    ayanamsa    = _G['ayanamsa']
    rule        = _G.get('sunrise_rule', 'modern')
    civil_date  = date(year, month, day)
    # A named zone gives each day its own offset under the clock setting; the
    # CLI's bare --tz_offset keeps one fixed offset.
    tz_offset = (
        utc_offset_hours(_G['tz_name'], civil_date, clock=_G.get('clock', 'standard'))
        if _G.get('tz_name') else _G['tz_offset']
    )

    try:
        # Local midnight anchors the civil day: sunrise is searched forward from it.
        # (A 05:30 anchor skipped any sunrise earlier than 05:30 -- Trenton in summer,
        # Delhi in June -- and the whole row described the next morning.)
        jd = local_time_to_jd(year, month, day, local_hour=0.0, tz_offset=tz_offset)

        # Sunrise / Sunset / Moonrise / Moonset
        jd_sr = get_sunrise(jd, lat, lon, rule)
        jd_ss = get_sunset(jd, lat, lon, rule)
        jd_mr = get_moonrise(jd, lat, lon)
        jd_ms = get_moonset(jd, lat, lon)

        # Ayanamsa value
        ayanamsa_val = get_ayanamsa(jd_sr, ayanamsa)

        # All 9 planet sidereal longitudes in one call at sunrise.
        planets = get_all_planet_positions(jd_sr, ayanamsa)

        # Panchang elements are sunrise-bound for the daily label.
        panchang = generate_daily_panchang(
            jd_sr,
            ayanamsa,
            sun_lon=planets['Sun'],
            moon_lon=planets['Moon'],
            local_date=civil_date,
        )
        jain_tithi = calculate_jain_tithi_from_sunrise(jd_sr, ayanamsa)

        festivals = _G.get('festival_dates', {}).get(year, {})
        cs1 = festivals.get('chaitra_shukla_1')
        diwali = festivals.get('diwali')
        vs = get_vikram_samvat(civil_date, cs1) if cs1 else None
        vns = get_vira_nirvana_samvat(civil_date, diwali) if diwali else None

        jd_next_day = jd + 1.0
        jd_next_sr = get_sunrise(jd_next_day, lat, lon, rule)
        bhadra_kaal = calculate_bhadra_kaal(jd_sr, jd_next_sr, ayanamsa)
        panchak_raw = calculate_panchak_kaal(jd_sr, jd_next_sr, ayanamsa)
        panchak_segs = panchak_raw["windows"]

        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        festival_index = _G.get("festival_index", {})
        day_fests = festival_index.get(date_str, {})
        row = format_row_data(
            date_str            = date_str,
            julian_date         = jd_sr,
            planets             = planets,
            panchang            = panchang,
            jain_tithi          = jain_tithi,
            sunrise_str         = jd_to_local_time_string(jd_sr, tz_offset),
            sunset_str          = jd_to_local_time_string(jd_ss, tz_offset),
            moonrise_str        = jd_to_local_time_string(jd_mr, tz_offset),
            moonset_str         = jd_to_local_time_string(jd_ms, tz_offset),
            ayanamsa_dec        = ayanamsa_val,
            ayanamsa_name       = ayanamsa,
            tz_offset           = tz_offset,
            tz_label            = tz_label,
            vikram_samvat       = vs,
            vira_nirvana_samvat = vns,
            bhadra_kaal         = bhadra_kaal,
            panchak_segments    = panchak_segs,
            jain_festivals      = day_fests.get("festivals") or None,
            jain_parva_tithis   = day_fests.get("parva_tithis") or None,
            festival_profile    = _G.get("festival_profile"),
        )
        return {**row, "__tz_offset": tz_offset}

    except Exception as exc:
        print(f"\n  [WARNING] {year}-{month:02d}-{day:02d}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Date generation helper
# ---------------------------------------------------------------------------

def _dates_in_range(start: date, end: date):
    """Yield (year, month, day) tuples from start to end inclusive."""
    delta = timedelta(days=1)
    current = start
    while current <= end:
        yield (current.year, current.month, current.day)
        current += delta


def _dates_in_month(year: int, month: int):
    """Yield (year, month, day) tuples for every day in the given month."""
    _, num_days = calendar.monthrange(year, month)
    for day in range(1, num_days + 1):
        yield (year, month, day)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_generation(config: dict, date_tuples: list, workers: int) -> list[dict]:
    """Run parallel/serial day computation.

    Args:
        config:       Configuration dict passed to each worker.
        date_tuples:  List of (year, month, day) tuples to process.
        workers:      Number of parallel processes (1 = serial).

    Returns:
        List of result dicts (None entries filtered out).
    """
    if workers > 1:
        with Pool(
            processes=workers,
            initializer=_init_worker,
            initargs=(config,),
        ) as pool:
            results_raw = list(pool.imap(_compute_day, date_tuples, chunksize=30))
    else:
        _init_worker(config)
        results_raw = [_compute_day(t) for t in date_tuples]

    return [r for r in results_raw if r is not None]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def add_time_setting_arguments(parser: argparse.ArgumentParser) -> None:
    """--clock and --sunrise, shared by every command."""
    parser.add_argument("--clock", type=str, default="standard", choices=CLOCK_MODES,
                        help="standard: the zone's standard time all year; daylight: the wall clock with DST")
    parser.add_argument("--sunrise", type=str, default="modern", choices=SUNRISE_RULES,
                        help="modern: upper limb with refraction; traditional: disc centre, no refraction")


def laghu_cli(argv: list[str]) -> None:
    """`python main.py laghu --year 2027 --city Delhi --format both`"""
    # Imported here: pdf_generation_service imports range_generation_service,
    # which imports this module.
    from pdf_generation_service import generate_laghu_panchang_export
    from hindi_calendar_pdf import SCHOOL_CHOICES
    from request_parsing import DEFAULT_PROFILE, LAGHU_FORMATS, VALID_PROFILES

    parser = argparse.ArgumentParser(
        prog="main.py laghu",
        description="Laghu Panchang booklet (Jan-Dec) as Hindi PDF and/or Excel.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--city", type=str, help="City name (geocoded), or use --lat/--lon")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--ayanamsa", type=str, default="Lahiri", choices=list(AYANAMSA_SYSTEMS.keys()))
    parser.add_argument("--profile", type=str, default=DEFAULT_PROFILE, choices=VALID_PROFILES)
    parser.add_argument("--format", type=str, default="pdf", choices=LAGHU_FORMATS)
    parser.add_argument("--output", type=str, default=".", help="Directory to write into")
    parser.add_argument("--school", type=str, default="all", choices=SCHOOL_CHOICES,
                        help="Kalyanak school: all, or one of Vrindavan (1), Uttarapurana (2), Ashadhara (3)")
    add_time_setting_arguments(parser)
    args = parser.parse_args(argv)

    if args.city is None and (args.lat is None or args.lon is None):
        parser.error("give --city, or both --lat and --lon")

    print(f"\n  Laghu Panchang {args.year} — building the year...")
    result = generate_laghu_panchang_export(
        year=args.year, city=args.city, lat=args.lat, lon=args.lon,
        ayanamsa_name=args.ayanamsa, profile=args.profile,
        output_format=args.format, output_dir=args.output,
        clock=args.clock, sunrise_rule=args.sunrise, school=args.school,
    )
    location = result["location"]
    print(f"  Location: {location['name']} ({location['lat']:.4f}, {location['lon']:.4f}) {location['timezone']}")
    for generated in result["files"]:
        print(f"  -> {generated['path']}")
    print("\n  [DONE]\n")


def main(argv: list[str] | None = None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["laghu"]:
        laghu_cli(argv[1:])
        return

    parser = argparse.ArgumentParser(
        description="Panchang Ephemeris Generator — Swiss Ephemeris based",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # --- Date range ---
    parser.add_argument("--start_year", type=int, required=True,
                        help="Start year (e.g. 2025)")
    parser.add_argument("--end_year",   type=int, required=True,
                        help="End year inclusive (e.g. 2030)")

    # --- Location ---
    parser.add_argument("--lat", type=float, required=True,
                        help="Latitude in decimal degrees (positive = North)")
    parser.add_argument("--lon", type=float, required=True,
                        help="Longitude in decimal degrees (positive = East)")

    # --- Timezone ---
    parser.add_argument("--tz_offset", type=float, default=5.5,
                        help="Timezone offset in hours east of UTC (default 5.5 = IST)")
    parser.add_argument("--tz_label",  type=str,   default="IST",
                        help="Label used in column headers for the timezone")

    # --- Ayanamsa ---
    parser.add_argument("--ayanamsa", type=str,
                        choices=list(AYANAMSA_SYSTEMS.keys()),
                        default="Lahiri",
                        help="Ayanamsa system to use")

    # --- Output ---
    parser.add_argument("--format", type=str,
                        choices=["csv", "excel", "json", "all"],
                        default="csv",
                        help="Output format")
    parser.add_argument("--output", type=str, default="panchang",
                        help="Base filename (without extension) for output files")
    parser.add_argument("--monthly", action="store_true",
                        help="Generate one output file per month instead of one large file")
    parser.add_argument("--language", type=str, choices=["en", "hi"], default="en",
                        help="Language of headers and text values (hi files get a _hi suffix)")

    parser.add_argument("--profile", type=str,
                        default="shwetambar_murtipujak_tapagachchha",
                        help="Jain sect profile (e.g. shwetambar_murtipujak_tapagachchha, digambar, etc.)")

    # --- Clock and sunrise rule ---
    parser.add_argument("--tz_name", type=str, default=None,
                        help="IANA zone (e.g. America/New_York). Overrides --tz_offset/--tz_label "
                             "and lets --clock choose standard time or the wall clock per day.")
    add_time_setting_arguments(parser)

    # --- Performance ---
    parser.add_argument("--workers", type=int, default=1,
                        help=f"Number of CPU workers for parallel generation "
                             f"(max on this machine: {cpu_count()})")

    args = parser.parse_args(argv)

    # Validate
    if args.start_year > args.end_year:
        parser.error("--start_year must be <= --end_year")
    workers = max(1, min(args.workers, cpu_count()))
    if args.tz_name:
        from range_generation_service import export_timezone

        zone = export_timezone(args.tz_name, args.start_year, clock=args.clock)
        args.tz_offset, args.tz_label = zone["offset_hours"], zone["label"]

    # Precompute festival dates for Samvat calculations (once per year, before workers start)
    print("  Computing festival dates for Samvat years...")
    festival_dates: dict = {}
    festival_index: dict = {}
    from jain_observances.festival_service import generate_jain_festivals
    for year in range(args.start_year, args.end_year + 1):
        festival_dates[year] = {
            'chaitra_shukla_1': find_chaitra_shukla_1(
                year, args.lat, args.lon, args.tz_offset, args.ayanamsa, sunrise_rule=args.sunrise
            ),
            'diwali': find_diwali(
                year, args.lat, args.lon, args.tz_offset, args.ayanamsa, sunrise_rule=args.sunrise
            ),
        }
        fest_data = generate_jain_festivals(
            year, args.lat, args.lon, args.ayanamsa, args.profile, sunrise_rule=args.sunrise
        )
        for f in fest_data.get("festivals", []):
            start_d = datetime.strptime(f["start_date"], "%Y-%m-%d").date()
            end_d = datetime.strptime(f.get("end_date", f["start_date"]), "%Y-%m-%d").date()
            curr_d = start_d
            while curr_d <= end_d:
                d_str = curr_d.isoformat()
                if d_str not in festival_index:
                    festival_index[d_str] = {"festivals": [], "parva_tithis": []}
                if f.get("category") == "parva":
                    festival_index[d_str]["parva_tithis"].append(f)
                else:
                    festival_index[d_str]["festivals"].append(f)
                curr_d += timedelta(days=1)

    # Shared worker config
    config = {
        'lat':              args.lat,
        'lon':              args.lon,
        'tz_offset':        args.tz_offset,
        'tz_label':         args.tz_label,
        'tz_name':          args.tz_name,
        'clock':            args.clock,
        'sunrise_rule':     args.sunrise,
        'ayanamsa':         args.ayanamsa,
        'festival_dates':   festival_dates,
        'festival_index':   festival_index,
        'festival_profile': args.profile,
    }

    start_date = date(args.start_year, 1, 1)
    end_date   = date(args.end_year, 12, 31)
    total_days = (end_date - start_date).days + 1

    print("=" * 65)
    print("  * Panchang Generator - Swiss Ephemeris")
    print("=" * 65)
    print(f"  Date range : {start_date} to {end_date} ({total_days} days)")
    print(f"  Location   : Lat {args.lat} deg, Lon {args.lon} deg")
    print(f"  Timezone   : UTC{args.tz_offset:+.1f} ({args.tz_label})")
    print(f"  Ayanamsa   : {args.ayanamsa}")
    print(f"  Format     : {args.format}")
    print(f"  Workers    : {workers}")
    print(f"  Monthly    : {args.monthly}")
    print("=" * 65)

    all_dates = list(_dates_in_range(start_date, end_date))
    print(f"  Computing {len(all_dates)} days with {workers} worker(s)...")
    results = run_generation(config, all_dates, workers)
    formatted_results = apply_element_continuity_formatting(results, tz_offset=args.tz_offset)
    suffix = "_hi" if args.language == "hi" else ""

    def write(rows: list[dict], base_name: str) -> None:
        out_rows = translate_rows_to_hindi(rows) if args.language == "hi" else rows
        export_data(out_rows, f"{base_name}{suffix}", args.format)

    print(f"\n  [OK] Computed {len(results)} days")
    print("  Exporting...")

    if args.monthly:
        for year in range(args.start_year, args.end_year + 1):
            for month in range(1, 13):
                month_rows = [
                    row for row in formatted_results
                    if date.fromisoformat(row["Date"]).year == year
                    and date.fromisoformat(row["Date"]).month == month
                ]
                if not month_rows:
                    continue

                month_name = calendar.month_abbr[month]
                print(f"  -> {year}-{month_name} ({len(month_rows)} days)...")
                write(month_rows, f"{args.output}_{year}_{month:02d}_{month_name}")
    else:
        write(formatted_results, f"{args.output}_{args.start_year}_{args.end_year}")

    print("\n  [DONE] Completed!\n")


if __name__ == "__main__":
    main()
