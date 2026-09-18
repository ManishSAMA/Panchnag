"""
visualize.py — Visualization and debugging tools for the Panchang Generator.

Provides:
  - plot_planetary_motion()   : Line charts of planet longitudes over time
  - plot_tithi_distribution() : Bar chart of Tithi frequency
  - plot_panchang_calendar()  : Monthly calendar heatmap for a Panchang element
  - compare_with_reference()  : Diff table vs. a reference ephemeris CSV
  - print_debug_day()         : Console dump of all values for one date

Usage:
  python visualize.py --file panchang_2025_2025.csv --plot planets --year 2025
  python visualize.py --file panchang_2025_2025.csv --plot tithis --year 2025
  python visualize.py --file panchang_2025_2025.csv --plot calendar --element Nakshatra --year 2025
  python visualize.py --file panchang_2025_2025.csv --ref reference.csv --compare
  python visualize.py --debug --date 2025-01-14 --lat 26.9124 --lon 75.7873
"""

import argparse
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Lazy matplotlib import
# ---------------------------------------------------------------------------

def _require_matplotlib():
    try:
        import matplotlib
        return matplotlib
    except ImportError:
        print("matplotlib is required for visualization. Run: pip install matplotlib")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 1. Planetary Motion Chart
# ---------------------------------------------------------------------------

def plot_planetary_motion(csv_file: str, planets: list[str] = None,
                          year: int = None) -> None:
    """Plot sidereal longitude of planets over time.

    Args:
        csv_file: Path to a Panchang CSV output file.
        planets:  List of planet names to plot. Default: all 9 grahas.
        year:     If given, restrict to that year only.
    """
    import pandas as pd
    mpl = _require_matplotlib()
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    PLANET_COLORS = {
        'Sun':     '#FFB347',
        'Moon':    '#B0C4DE',
        'Mars':    '#FF4444',
        'Mercury': '#90EE90',
        'Jupiter': '#FFD700',
        'Venus':   '#FF69B4',
        'Saturn':  '#A0A0FF',
        'Rahu':    '#8B4513',
        'Ketu':    '#9370DB',
    }

    df = pd.read_csv(csv_file, parse_dates=['Date'])
    if year:
        df = df[df['Date'].dt.year == year]
    if df.empty:
        print(f"No data found for year {year}.")
        return

    if planets is None:
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
                   'Venus', 'Saturn', 'Rahu', 'Ketu']

    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')

    for planet in planets:
        col = f'{planet}_Dec'
        if col not in df.columns:
            print(f"  Column '{col}' not found, skipping {planet}.")
            continue
        color = PLANET_COLORS.get(planet, '#FFFFFF')
        ax.plot(df['Date'], df[col], label=planet, color=color,
                linewidth=1.5, alpha=0.85)

    # Rashi boundary lines at 0, 30, 60, ... 330
    for deg in range(0, 361, 30):
        ax.axhline(y=deg, color='#444466', linewidth=0.5, linestyle='--')

    RASHI_LABELS = [
        "Mesha", "Vrishabha", "Mithuna", "Karka",
        "Simha", "Kanya", "Tula", "Vrishchika",
        "Dhanu", "Makara", "Kumbha", "Meena",
    ]
    for i, name in enumerate(RASHI_LABELS):
        ax.annotate(name, xy=(df['Date'].iloc[0], i * 30 + 15),
                    fontsize=6, color='#666688', va='center')

    ax.set_ylim(0, 360)
    ax.set_yticks(range(0, 361, 30))
    ax.set_ylabel("Sidereal Longitude (°)", color='white', fontsize=11)
    ax.set_xlabel("Date", color='white', fontsize=11)
    ax.tick_params(colors='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    title = f"Planetary Motion (Nirayana) — {year or 'All Years'}"
    ax.set_title(title, color='white', fontsize=14, fontweight='bold', pad=15)
    legend = ax.legend(loc='upper right', framealpha=0.3, labelcolor='white',
                        facecolor='#1a1a2e', edgecolor='#444466')

    plt.tight_layout()
    out = f"planetary_motion_{year or 'all'}.png"
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  ✓ Saved: {out}")
    plt.show()


# ---------------------------------------------------------------------------
# 2. Tithi Frequency Distribution
# ---------------------------------------------------------------------------

def plot_tithi_distribution(csv_file: str, year: int = None) -> None:
    """Bar chart showing how many days each Tithi appeared."""
    import pandas as pd
    _require_matplotlib()
    import matplotlib.pyplot as plt
    import numpy as np

    df = pd.read_csv(csv_file, parse_dates=['Date'])
    if year:
        df = df[df['Date'].dt.year == year]

    counts = df['Tithi'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(18, 6))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')

    colors = plt.cm.plasma(np.linspace(0.1, 0.9, len(counts)))
    bars = ax.bar(range(len(counts)), counts.values, color=colors, edgecolor='#333', linewidth=0.5)

    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index.tolist(), rotation=75, ha='right',
                        fontsize=7, color='white')
    ax.set_ylabel("Days Count", color='white', fontsize=11)
    ax.tick_params(colors='white')
    ax.set_title(f"Tithi Frequency Distribution — {year or 'All Years'}",
                  color='white', fontsize=14, fontweight='bold', pad=15)

    # Annotate bar tops
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(val), ha='center', va='bottom', color='white', fontsize=7)

    plt.tight_layout()
    out = f"tithi_distribution_{year or 'all'}.png"
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  ✓ Saved: {out}")
    plt.show()


# ---------------------------------------------------------------------------
# 3. Monthly Calendar Heatmap
# ---------------------------------------------------------------------------

def plot_panchang_calendar(csv_file: str, element: str = 'Nakshatra',
                            year: int = None) -> None:
    """Calendar-style heatmap of a chosen Panchang element (by numeric index).

    Args:
        element: Column name to visualize, e.g. 'Nakshatra_No', 'Tithi_No'.
    """
    import pandas as pd
    import numpy as np
    _require_matplotlib()
    import matplotlib.pyplot as plt

    df = pd.read_csv(csv_file, parse_dates=['Date'])
    if year:
        df = df[df['Date'].dt.year == year]

    # Map element name → numeric column
    col_map = {
        'Nakshatra': 'Nakshatra_No',
        'Tithi':     'Tithi_No',
        'Yoga':      'Yoga_No',
        'Karana':    'Karana_No',
    }
    col = col_map.get(element, element)
    if col not in df.columns:
        col = element  # Try directly

    if col not in df.columns:
        print(f"Column '{col}' not found in data. Available: {list(df.columns)}")
        return

    months = sorted(df['Date'].dt.month.unique())
    fig, axes = plt.subplots(3, 4, figsize=(20, 12))
    fig.patch.set_facecolor('#1a1a2e')
    fig.suptitle(f"{element} Calendar — {year or 'All'}", color='white',
                  fontsize=16, fontweight='bold', y=1.01)

    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]

    cmap = plt.cm.viridis
    global_min = df[col].min()
    global_max = df[col].max()

    for ax, month in zip(axes.flat, range(1, 13)):
        ax.set_facecolor('#16213e')
        mdata = df[df['Date'].dt.month == month]
        if mdata.empty:
            ax.set_visible(False)
            continue

        import calendar
        _, num_days = calendar.monthrange(mdata['Date'].dt.year.iloc[0], month)
        days = mdata['Date'].dt.day.values
        vals = mdata[col].values

        norm_vals = (vals - global_min) / max(global_max - global_min, 1)
        colors = cmap(norm_vals)

        ax.bar(days, vals, color=colors, edgecolor='#333', linewidth=0.3)
        ax.set_title(MONTH_NAMES[month - 1], color='white', fontsize=10)
        ax.set_xlim(0, num_days + 1)
        ax.tick_params(colors='white', labelsize=7)
        ax.spines[:].set_color('#444466')

    plt.tight_layout()
    out = f"calendar_{element.lower()}_{year or 'all'}.png"
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  ✓ Saved: {out}")
    plt.show()


# ---------------------------------------------------------------------------
# 4. Reference Comparison
# ---------------------------------------------------------------------------

def compare_with_reference(generated_csv: str, reference_csv: str,
                            columns: list[str] = None) -> None:
    """Print a diff table comparing generated data to a reference ephemeris.

    Args:
        generated_csv:  Path to the generated Panchang CSV.
        reference_csv:  Path to the reference CSV (same Date column).
        columns:        Which columns to compare. Default: Sun, Moon, Tithi.
    """
    import pandas as pd

    gen = pd.read_csv(generated_csv)
    ref = pd.read_csv(reference_csv)

    # Merge on Date
    merged = gen.merge(ref, on='Date', suffixes=('_gen', '_ref'))

    if columns is None:
        columns = ['Sun_Dec', 'Moon_Dec', 'Tithi_No']

    print(f"\n{'Date':<12}", end="")
    for c in columns:
        print(f"  {c[:16]:<18}  {'Diff':<10}", end="")
    print()
    print("-" * (12 + len(columns) * 30))

    mismatches = 0
    for _, row in merged.iterrows():
        line = f"{row['Date']:<12}"
        flag = False
        for c in columns:
            gc = f"{c}_gen"
            rc = f"{c}_ref"
            if gc in row and rc in row:
                try:
                    diff = abs(float(row[gc]) - float(row[rc]))
                    if diff > 0.01:
                        flag = True
                    line += f"  {str(row[gc]):<18}  {diff:<10.4f}"
                except (ValueError, TypeError):
                    match = "✓" if str(row[gc]) == str(row[rc]) else "✗"
                    if match == "✗":
                        flag = True
                    line += f"  {str(row[gc]):<18}  {match:<10}"
        if flag:
            mismatches += 1
            print(line + "  ◀ DIFF")

    total = len(merged)
    matched = total - mismatches
    print(f"\nMatched: {matched}/{total} rows. Mismatches: {mismatches}")


# ---------------------------------------------------------------------------
# 5. Debug: Print all values for one date
# ---------------------------------------------------------------------------

def print_debug_day(date_str: str, lat: float, lon: float,
                     ayanamsa: str = 'Lahiri', tz_offset: float = 5.5) -> None:
    """Print a comprehensive debug dump for a single date.

    Useful for verifying calculations against published almanacs.
    """
    from astronomy import (
        local_time_to_jd, get_all_planet_positions, get_ayanamsa,
        get_sunrise, get_sunset, get_moonrise, get_moonset,
        jd_to_local_time_string, format_dms, get_rashi_name,
    )
    from panchang import generate_daily_panchang, TITHI_NAMES, NAKSHATRA_NAMES

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    jd = local_time_to_jd(dt.year, dt.month, dt.day, 5.5, tz_offset)
    planets = get_all_planet_positions(jd, ayanamsa)
    panchang = generate_daily_panchang(jd, ayanamsa)
    ayanamsa_val = get_ayanamsa(jd, ayanamsa)

    jd_sr = get_sunrise(jd, lat, lon)
    jd_ss = get_sunset(jd, lat, lon)
    jd_mr = get_moonrise(jd, lat, lon)
    jd_ms = get_moonset(jd, lat, lon)

    tz_lbl = f"UTC+{tz_offset:.1f}"

    print("=" * 60)
    print(f"  🪐  Panchang Debug Dump: {date_str}")
    print(f"  Lat: {lat}°  Lon: {lon}°  Ayanamsa: {ayanamsa}")
    print("=" * 60)
    print(f"  Julian Date        : {jd:.5f}")
    print(f"  Ayanamsa           : {format_dms(ayanamsa_val)}")
    print()
    print("  PANCHANG ELEMENTS")
    print(f"  ├── Vara (Weekday)  : {panchang['Vara_Name']}")
    print(f"  ├── Tithi           : [{panchang['Tithi_Index']:2d}] {panchang['Tithi_Name']}")
    print(f"  ├── Nakshatra       : [{panchang['Nakshatra_Index']:2d}] {panchang['Nakshatra_Name']} "
          f"(Pada {panchang['Nakshatra_Pada']})")
    print(f"  ├── Yoga            : [{panchang['Yoga_Index']:2d}] {panchang['Yoga_Name']}")
    print(f"  └── Karana          : [{panchang['Karana_Index']:2d}] {panchang['Karana_Name']}")
    print()
    print("  PLANETARY POSITIONS (Nirayana / Sidereal)")
    for name, lon_dec in planets.items():
        rashi = get_rashi_name(lon_dec)
        print(f"  ├── {name:<10} : {format_dms(lon_dec):>22}  ({rashi})")
    print()
    print("  RISE / SET TIMES")
    print(f"  ├── Sunrise         : {jd_to_local_time_string(jd_sr, tz_offset)} {tz_lbl}")
    print(f"  ├── Sunset          : {jd_to_local_time_string(jd_ss, tz_offset)} {tz_lbl}")
    print(f"  ├── Moonrise        : {jd_to_local_time_string(jd_mr, tz_offset)} {tz_lbl}")
    print(f"  └── Moonset         : {jd_to_local_time_string(jd_ms, tz_offset)} {tz_lbl}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Panchang Visualization & Debug Tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--file",    type=str, help="Path to Panchang CSV file")
    parser.add_argument("--plot",    type=str,
                        choices=["planets", "tithis", "calendar"],
                        help="What to plot")
    parser.add_argument("--planets", type=str, nargs='+',
                        default=None,
                        help="Planet names to include in planet plot")
    parser.add_argument("--element", type=str, default="Nakshatra",
                        choices=["Tithi", "Nakshatra", "Yoga", "Karana"],
                        help="Panchang element for calendar plot")
    parser.add_argument("--year",    type=int, default=None,
                        help="Filter data to a specific year")

    # Reference comparison
    parser.add_argument("--ref",     type=str, help="Reference CSV for comparison")
    parser.add_argument("--compare", action="store_true",
                        help="Compare generated CSV with reference CSV")

    # Debug single day
    parser.add_argument("--debug",   action="store_true",
                        help="Debug a single date (print all values)")
    parser.add_argument("--date",    type=str, help="Date in YYYY-MM-DD format")
    parser.add_argument("--lat",     type=float, default=26.9124)
    parser.add_argument("--lon",     type=float, default=75.7873)
    parser.add_argument("--ayanamsa",type=str, default="Lahiri",
                        choices=["Lahiri", "Raman", "Krishnamurti"])
    parser.add_argument("--tz_offset",type=float, default=5.5)

    args = parser.parse_args()

    if args.debug:
        if not args.date:
            parser.error("--debug requires --date YYYY-MM-DD")
        print_debug_day(args.date, args.lat, args.lon, args.ayanamsa, args.tz_offset)

    elif args.compare:
        if not (args.file and args.ref):
            parser.error("--compare requires --file and --ref")
        compare_with_reference(args.file, args.ref)

    elif args.plot:
        if not args.file:
            parser.error("--plot requires --file")
        if args.plot == "planets":
            plot_planetary_motion(args.file, args.planets, args.year)
        elif args.plot == "tithis":
            plot_tithi_distribution(args.file, args.year)
        elif args.plot == "calendar":
            plot_panchang_calendar(args.file, args.element, args.year)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
