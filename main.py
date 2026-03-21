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
import sys
import os
from datetime import datetime, timedelta, date
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
    AYANAMSA_SYSTEMS,
)
from panchang import generate_daily_panchang
from export import format_row_data, export_data

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


def _compute_day(args_tuple) -> dict:
    """Compute all Panchang data for a single date.

    Args:
        args_tuple: (year, month, day)

    Returns:
        Row dict ready for export, or None on unrecoverable error.
    """
    year, month, day = args_tuple
    lat         = _G['lat']
    lon         = _G['lon']
    tz_offset   = _G['tz_offset']
    tz_label    = _G['tz_label']
    ayanamsa    = _G['ayanamsa']

    try:
        # 05:30 local time → JD
        jd = local_time_to_jd(year, month, day, local_hour=5.5, tz_offset=tz_offset)

        # Ayanamsa value
        ayanamsa_val = get_ayanamsa(jd, ayanamsa)

        # All 9 planet sidereal longitudes in one call
        planets = get_all_planet_positions(jd, ayanamsa)

        # Panchang elements
        panchang = generate_daily_panchang(jd, ayanamsa)

        # Sunrise / Sunset / Moonrise / Moonset
        jd_sr = get_sunrise(jd, lat, lon)
        jd_ss = get_sunset(jd, lat, lon)
        jd_mr = get_moonrise(jd, lat, lon)
        jd_ms = get_moonset(jd, lat, lon)

        row = format_row_data(
            date_str      = f"{year:04d}-{month:02d}-{day:02d}",
            julian_date   = jd,
            planets       = planets,
            panchang      = panchang,
            sunrise_str   = jd_to_local_time_string(jd_sr, tz_offset),
            sunset_str    = jd_to_local_time_string(jd_ss, tz_offset),
            moonrise_str  = jd_to_local_time_string(jd_mr, tz_offset),
            moonset_str   = jd_to_local_time_string(jd_ms, tz_offset),
            ayanamsa_dec  = ayanamsa_val,
            tz_label      = tz_label,
        )
        return row

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
    import calendar
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

def main():
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

    # --- Performance ---
    parser.add_argument("--workers", type=int, default=1,
                        help=f"Number of CPU workers for parallel generation "
                             f"(max on this machine: {cpu_count()})")

    args = parser.parse_args()

    # Validate
    if args.start_year > args.end_year:
        parser.error("--start_year must be ≤ --end_year")
    workers = max(1, min(args.workers, cpu_count()))

    # Shared worker config
    config = {
        'lat':       args.lat,
        'lon':       args.lon,
        'tz_offset': args.tz_offset,
        'tz_label':  args.tz_label,
        'ayanamsa':  args.ayanamsa,
    }

    start_date = date(args.start_year, 1, 1)
    end_date   = date(args.end_year, 12, 31)
    total_days = (end_date - start_date).days + 1

    print("=" * 65)
    print("  🪐  Panchang Generator — Swiss Ephemeris")
    print("=" * 65)
    print(f"  Date range : {start_date} → {end_date} ({total_days} days)")
    print(f"  Location   : Lat {args.lat}°, Lon {args.lon}°")
    print(f"  Timezone   : UTC{args.tz_offset:+.1f} ({args.tz_label})")
    print(f"  Ayanamsa   : {args.ayanamsa}")
    print(f"  Format     : {args.format}")
    print(f"  Workers    : {workers}")
    print(f"  Monthly    : {args.monthly}")
    print("=" * 65)

    if args.monthly:
        # One file per (year, month)
        import calendar
        for year in range(args.start_year, args.end_year + 1):
            for month in range(1, 13):
                m_start = date(year, month, 1)
                _, last_day = calendar.monthrange(year, month)
                m_end = date(year, month, last_day)

                # Clamp to the overall range
                m_start = max(m_start, start_date)
                m_end   = min(m_end,   end_date)
                if m_start > m_end:
                    continue

                month_dates = list(_dates_in_range(m_start, m_end))
                month_name  = calendar.month_abbr[month]
                print(f"  ► {year}-{month_name} ({len(month_dates)} days) …")

                results = run_generation(config, month_dates, workers)
                if results:
                    fname = f"{args.output}_{year}_{month:02d}_{month_name}"
                    export_data(results, fname, args.format)

    else:
        # One big file
        all_dates = list(_dates_in_range(start_date, end_date))
        print(f"  Computing {len(all_dates)} days with {workers} worker(s) …")

        results = run_generation(config, all_dates, workers)

        print(f"\n  ✓ Computed {len(results)} days")
        print("  Exporting …")

        out_base = f"{args.output}_{args.start_year}_{args.end_year}"
        export_data(results, out_base, args.format)

    print("\n  ✅ Done!\n")


if __name__ == "__main__":
    main()
