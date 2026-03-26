# Setup and Usage

This page guides you through setting up the environment and using the Panchang Generator's command-line interface.

## Prerequisites

1. Ensure **Python 3.9+** is installed on your system.
2. The generator requires the Python wrapper for the Swiss Ephemeris and data analysis libraries.

Activate your virtual environment and install dependencies via:
```bash
pip install -r requirements.txt
```
*(Common dependencies include `pyswisseph`, `tqdm`, `pandas`, `openpyxl`, `reportlab`, and `matplotlib`.)*

---

## 🚀 Running the Main Generator
The primary entry point is `main.py`, which is run natively from the terminal.

### Basic Generation
Generate a Panchang for Jaipur (Lat: 26.9124, Lon: 75.7873) for the entire year of **2025** and save it as a CSV:
```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv
```

### Advanced Usage Flags

- `--start_year` / `--end_year`: Define the generation range.
- `--lat` / `--lon`: Setup geographic coordinates (decimal degrees).
- `--tz_offset`: Shifts standard UTC Time to a specific timezone (Default: `5.5` for IST).
- `--tz_label`: Useful moniker for table headers (Default `IST`).
- `--ayanamsa`: `Lahiri` (default), `Raman`, or `Krishnamurti`.
- `--format`: `csv`, `excel`, `json`, or `all`.
- `--output`: File prefix (default: `panchang`).
- `--monthly`: Generates an isolated file chunk per month instead of one massive file block (`panchang_2025_01_Jan.csv`).
- `--workers`: Determines amount of parallel CPU workers. Speeds up decade-long generation ranges significantly. Max out matching your local CPU core count.

### Multi-Year, Multi-Core Example
Generate data between 2025 and 2030, output as an Excel spreadsheet, using 4 CPU workers:
```bash
python main.py --start_year 2025 --end_year 2030 --lat 26.9124 --lon 75.7873 --format excel --workers 4
```

---

## 📄 Generating PDF Tables
If you need a beautifully structured monthly printable layout, use `export_pdf.py` directly:
```bash
python export_pdf.py --year 2025 --out panchang_table_2025.pdf
```
*Note: This generates an immediate Landscape letter-size format layout depicting Tithis, Nakshatras, Yogas, and basic Sunrise constraints mapped directly to the local timezone provided inside the script.*
