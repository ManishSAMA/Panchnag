"""
export.py — Data formatting and file export utilities for the Panchang Generator.

Supports export to:
  - CSV   (comma-separated values, UTF-8)
  - Excel (.xlsx via openpyxl)
  - JSON  (pretty-printed)

Each row stores both raw decimal-degree values (machine-readable)
and human-readable DMS strings for every planetary longitude.
"""

import csv
import json
import os
from astronomy import format_dms

# ---------------------------------------------------------------------------
# Row Formatter
# ---------------------------------------------------------------------------

def format_row_data(
    date_str: str,
    julian_date: float,
    planets: dict[str, float],   # name → decimal degrees
    panchang: dict,
    sunrise_str: str,
    sunset_str: str,
    moonrise_str: str,
    moonset_str: str,
    ayanamsa_dec: float,
    tz_label: str = "IST",
) -> dict:
    """Build a flat dict representing one row of the Panchang table.

    Args:
        date_str:      ISO date string (YYYY-MM-DD).
        julian_date:   Julian Day Number.
        planets:       Dict of planet→decimal longitude (sidereal).
        panchang:      Output of generate_daily_panchang().
        sunrise_str:   Formatted local time string for sunrise.
        sunset_str:    Formatted local time string for sunset.
        moonrise_str:  Formatted local time string for moonrise.
        moonset_str:   Formatted local time string for moonset.
        ayanamsa_dec:  Ayanamsa value in decimal degrees.
        tz_label:      Timezone label used in column headers.

    Returns:
        Ordered flat dict suitable for CSV / Excel / JSON export.
    """
    row: dict = {}

    # ---- Date & JD ----
    row['Date'] = date_str
    row['Julian_Date'] = round(julian_date, 5)
    row['Weekday'] = panchang['Vara_Name']

    # ---- Panchang Elements ----
    row['Tithi_No']    = panchang['Tithi_Index']
    row['Tithi']       = panchang['Tithi_Name']
    row['Nakshatra_No']= panchang['Nakshatra_Index']
    row['Nakshatra']   = panchang['Nakshatra_Name']
    row['Nakshatra_Pada'] = panchang['Nakshatra_Pada']
    row['Yoga_No']     = panchang['Yoga_Index']
    row['Yoga']        = panchang['Yoga_Name']
    row['Karana_No']   = panchang['Karana_Index']
    row['Karana']      = panchang['Karana_Name']

    # ---- Sunrise / Sunset / Moonrise / Moonset ----
    row[f'Sunrise ({tz_label})']  = sunrise_str
    row[f'Sunset ({tz_label})']   = sunset_str
    row[f'Moonrise ({tz_label})'] = moonrise_str
    row[f'Moonset ({tz_label})']  = moonset_str

    # ---- Planetary Longitudes (decimal & DMS) ----
    planet_order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
                    'Venus', 'Saturn', 'Rahu', 'Ketu']
    for planet in planet_order:
        dec = planets.get(planet, 0.0)
        row[f'{planet}_Dec']  = round(dec, 6)
        row[f'{planet}_DMS']  = format_dms(dec)

    # ---- Ayanamsa ----
    row['Ayanamsa_Dec'] = round(ayanamsa_dec, 6)
    row['Ayanamsa_DMS'] = format_dms(ayanamsa_dec)

    return row


# ---------------------------------------------------------------------------
# Export Functions
# ---------------------------------------------------------------------------

def export_to_csv(data_list: list[dict], filename: str = "panchang_output.csv") -> None:
    """Export data to a UTF-8 CSV file."""
    if not data_list:
        print("No data to export.")
        return
    keys = list(data_list[0].keys())
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)
    print(f"  ✓ CSV  → {os.path.abspath(filename)}")


def export_to_json(data_list: list[dict], filename: str = "panchang_output.json") -> None:
    """Export data to a pretty-printed JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
    print(f"  ✓ JSON → {os.path.abspath(filename)}")


def export_to_excel(data_list: list[dict], filename: str = "panchang_output.xlsx") -> None:
    """Export data to an Excel workbook (.xlsx)."""
    try:
        import pandas as pd
    except ImportError:
        print("pandas not installed. Run: pip install pandas openpyxl")
        return
    if not data_list:
        print("No data to export.")
        return
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"  ✓ Excel→ {os.path.abspath(filename)}")


def export_data(data_list: list[dict], base_filename: str, fmt: str) -> None:
    """Dispatch export to the correct format.

    Args:
        data_list:      List of row dicts.
        base_filename:  Base path without extension.
        fmt:            One of 'csv', 'excel', 'json', 'all'.
    """
    if not data_list:
        print("Warning: No data rows to export.")
        return

    formats = ['csv', 'excel', 'json'] if fmt == 'all' else [fmt]
    for f in formats:
        ext_map = {'csv': 'csv', 'excel': 'xlsx', 'json': 'json'}
        fname = f"{base_filename}.{ext_map[f]}"
        if f == 'csv':
            export_to_csv(data_list, fname)
        elif f == 'json':
            export_to_json(data_list, fname)
        elif f == 'excel':
            export_to_excel(data_list, fname)
