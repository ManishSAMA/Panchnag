# 🪐 Panchang Generator

A high-accuracy Vedic Panchang ephemeris generator powered by **Swiss Ephemeris** (`pyswisseph`).

Generates detailed daily astronomical and Panchang data for any date range, location, and timezone.

---

## Project Structure

```
panchang_generator/
  astronomy.py   — Swiss Ephemeris wrapper (positions, rise/set, DMS)
  panchang.py    — Vedic Panchang calculations (Tithi, Nakshatra, Yoga, Karana, Vara)
  export.py      — CSV / Excel / JSON export
  main.py        — CLI interface
  visualize.py   — Charts + debug tools
  requirements.txt
```

---

## Installation

```bash
pip install -r requirements.txt
```

> **Note**: `pyswisseph` requires a C compiler and Python development headers on some platforms if a pre-compiled wheel isn't available for your Python version.
> - **Fedora/RHEL**: run `sudo dnf install -y python3-devel gcc` before `pip install`.
> - **Windows**: install the pre-built wheel from PyPI: `pip install pyswisseph`

---

## Quick Start

```bash
# Generate full-year 2025 Panchang for Jaipur (Lahiri ayanamsa, CSV output)
python main.py --start_year 2025 --end_year 2025 \
               --lat 26.9124 --lon 75.7873 \
               --format csv --output panchang_jaipur

# Generate 2025-2030 using 4 CPU cores (Excel)
python main.py --start_year 2025 --end_year 2030 \
               --lat 26.9124 --lon 75.7873 \
               --format excel --workers 4

# Monthly output files
python main.py --start_year 2025 --end_year 2025 \
               --lat 26.9124 --lon 75.7873 \
               --format all --monthly

# Mumbai + Krishnamurti ayanamsa
python main.py --start_year 2025 --end_year 2025 \
               --lat 19.0760 --lon 72.8777 \
               --ayanamsa Krishnamurti --format csv
```

---

## CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--start_year` | *(required)* | Start year |
| `--end_year` | *(required)* | End year (inclusive) |
| `--lat` | *(required)* | Latitude (decimal degrees, positive = North) |
| `--lon` | *(required)* | Longitude (decimal degrees, positive = East) |
| `--tz_offset` | `5.5` | Timezone offset from UTC (hours). Default = IST |
| `--tz_label` | `IST` | Label used in column headers |
| `--ayanamsa` | `Lahiri` | Ayanamsa system: `Lahiri`, `Raman`, `Krishnamurti` |
| `--format` | `csv` | Output format: `csv`, `excel`, `json`, `all` |
| `--output` | `panchang` | Base filename (no extension) |
| `--monthly` | `False` | One file per month instead of one big file |
| `--workers` | `1` | Number of parallel CPU workers |

---

## Output Columns

| Column | Description |
|---|---|
| `Date` | ISO date (YYYY-MM-DD) |
| `Julian_Date` | Julian Day Number |
| `Weekday` | Vara name (e.g., Ravivara) |
| `Tithi_No`, `Tithi` | Lunar day number and name |
| `Nakshatra_No`, `Nakshatra`, `Nakshatra_Pada` | Lunar mansion + quarter |
| `Yoga_No`, `Yoga` | Yoga index and name |
| `Karana_No`, `Karana` | Karana index and name |
| `Sunrise (IST)`, `Sunset (IST)` | Local rise / set times |
| `Moonrise (IST)`, `Moonset (IST)` | Local moonrise / moonset |
| `Sun_Dec`, `Sun_DMS` | Sun sidereal longitude (decimal + DMS) |
| *(same pattern for Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)* | |
| `Ayanamsa_Dec`, `Ayanamsa_DMS` | Ayanamsa value |

---

## Visualization Tools

```bash
# Planetary motion chart (PNG)
python visualize.py --file panchang_2025_2025.csv --plot planets --year 2025

# Tithi frequency bar chart
python visualize.py --file panchang_2025_2025.csv --plot tithis --year 2025

# Monthly calendar heatmap for Nakshatra
python visualize.py --file panchang_2025_2025.csv --plot calendar --element Nakshatra --year 2025

# Compare with a reference ephemeris
python visualize.py --file panchang_2025_2025.csv --ref reference.csv --compare

# Debug a single date (console dump)
python visualize.py --debug --date 2025-01-14 --lat 26.9124 --lon 75.7873
```

---

## Accuracy Notes

- Uses **Swiss Ephemeris** high-precision mode (`FLG_SWIEPH`)
- **Geocentric apparent positions** with `FLG_SPEED`
- Sidereal conversion via the selected ayanamsa (`FLG_SIDEREAL`)
- True Lunar Node used for Rahu (more accurate than Mean Node)
- Calculations performed at **05:30 local time** each day (traditional Panchang epoch)
- Sunrise/moonrise use `swe.rise_trans()` with disc-center correction

---

## Common Locations

| City | Latitude | Longitude |
|---|---|---|
| Jaipur | 26.9124 | 75.7873 |
| New Delhi | 28.6139 | 77.2090 |
| Mumbai | 19.0760 | 72.8777 |
| Varanasi | 25.3176 | 82.9739 |
| Chennai | 13.0827 | 80.2707 |
| Kolkata | 22.5726 | 88.3639 |
