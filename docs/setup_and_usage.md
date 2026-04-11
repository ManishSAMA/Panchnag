# Setup and Usage

This guide is written primarily for people who want to run and use the application.

## 1. Requirements

You need:

- Python 3.9 or newer (the project is developed on Python 3.14)
- the dependencies listed in `requirements.txt`
- internet access if you want to use city search, because geocoding depends on Nominatim

## 2. Installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Packages installed from `requirements.txt`:

- `pyswisseph` — Swiss Ephemeris wrapper for all astronomical calculations
- `flask` — web framework and API server
- `requests` — HTTP client for Nominatim geocoding
- `timezonefinder` — IANA timezone lookup from coordinates
- `pandas` — data manipulation for export generation
- `openpyxl` — Excel file writing
- `matplotlib` — planetary charts and visualization tools
- `tqdm` — progress bars for CLI batch generation
- `reportlab` — PDF generation

## 3. Running the Web App

Start the development server:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The web app contains three generator sections:

1. single-date Panchang lookup
2. year-range export
3. printable PDF generation

## 4. Using the Daily Panchang Generator

The first section is designed for day-level inspection.

### Input options

You can either:

- search for a city and select one of the autocomplete suggestions
- manually enter latitude and longitude

If you use city search, the coordinate fields are filled automatically when you choose a suggestion.

### Required fields

- a valid location (city or coordinates)
- a valid date
- ayanamsa choice (defaults to Lahiri if not specified)

### Output

The result includes:

- sunrise, sunset, moonrise, moonset times
- next sunrise
- Tithi (with end time)
- Jain Tithi with its `+2h24m` reference time and end time
- Nakshatra and Pada (with end time)
- Yoga
- Karana
- Vara (weekday)
- Sun Rashi and Moon Rashi
- Hindu month, Vikram Samvat, and Vira Nirvana Samvat
- full structured JSON payload

### Rule snapshots

The current daily generator shows:

- the primary sunrise-based Panchang label (Udaya Tithi)
- the Jain Tithi, determined at `+2h24m` (2 hours 24 minutes) after sunrise

The Jain Tithi does not override the primary daily label; it is displayed alongside it for comparison.

## 5. Using the Year-Range Generator

The second section is designed for bulk exports.

### How it works

The range generator reuses the same location and ayanamsa you already entered in the daily section.

You provide:

- `Start year`
- `End year`
- output `Format`
- optional `Monthly files` toggle

### Available formats

- `csv`
- `excel`
- `json`
- `all` — generates all three in one run

### Output behavior

After generation, the interface returns:

- summary information including rows generated and timezone used
- one or more downloadable file links

If `Monthly files` is enabled, you receive one file per month instead of one large file for the full range.

The exported rows use a fixed timezone label and numeric offset snapshot for the whole run. That is a good fit for the main India-focused workflow, but locations with daylight-saving transitions can show one-hour drift in exported civil times.

### Good use cases

- yearly Panchang archives
- data validation and QA exports
- downstream spreadsheet analysis
- historical comparisons across ayanamsas

## 6. Using the PDF Generator

The third section generates a printable PDF for a single year.

### Inputs

The PDF generator reuses:

- the current city or coordinates
- the current ayanamsa

You only need to provide:

- a target year

### Output

The app generates a downloadable PDF named like:

```text
panchang_2025.pdf
```

The PDF renders landscape monthly tables for the selected year, including Tithi, Jain Tithi, Nakshatra, Yoga, Karana, Moon Rashi, Sun Rashi, sunrise, sunset, and Vara.

Like the range generator, the PDF path uses a fixed timezone offset snapshot for the selected year rather than a full per-date timezone conversion.

## 7. CLI Usage

The CLI is useful when:

- you prefer terminal workflows
- you want scripted generation
- you want multi-year exports without the browser

### Single-year CSV example

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv
```

### Multi-year Excel example with parallel workers

```bash
python main.py --start_year 2025 --end_year 2030 --lat 26.9124 --lon 75.7873 --format excel --workers 4
```

### Monthly JSON split example

```bash
python main.py --start_year 2025 --end_year 2026 --lat 26.9124 --lon 75.7873 --format json --monthly
```

### All formats in one run

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format all
```

## 8. API Overview

If you want to use the app programmatically, the main endpoints are:

- `GET /search-location?q=<query>` — city autocomplete
- `GET /get-coordinates?city=<name>` — resolve city to coordinates and timezone
- `POST /generate-panchang` — daily Panchang payload
- `POST /generate-range-panchang` — multi-year export files
- `POST /generate-pdf-panchang` — year PDF
- `GET /downloads/<token>` — download a generated file by UUID token

## 9. Common Validation Rules

The server enforces:

- date is required for daily generation
- year is required for PDF generation
- `start_year <= end_year` for range generation
- coordinates must be numeric
- latitude and longitude must be provided together
- either a city or both coordinates must be supplied
- output format must be one of `csv`, `excel`, `json`, or `all`

The UI offers `Lahiri`, `Raman`, and `Krishnamurti` ayanamsas. Unknown ayanamsa names currently fall back to Lahiri in the astronomy layer, so API clients should send one of those exact names.

## 10. Practical Notes

### Timezones

For daily results, the app uses the timezone inferred from coordinates and validates that the resolved sunrise belongs to the requested civil date.

For range and PDF export generation, the export pipeline uses a derived timezone label and offset snapshot for output formatting. This works well for the main India-based use case.

### Geocoding

Location search depends on Nominatim. If the service is unavailable or the network is blocked, city search may fail while manual coordinates still work.

### Performance

Single-date lookups are near-instant. Multi-year exports take longer depending on range size, output format, and machine speed. Use `--workers` to parallelize over multiple CPU cores for large ranges.

## 11. Visualization Tools

The `visualize.py` module provides charts and debugging utilities against generated CSV output. See [Visualizations](./visualizations.md) for full usage details.

Quick examples:

```bash
# Plot planetary motion for 2025
python visualize.py --file panchang_2025_2025.csv --plot planets --year 2025

# Debug a single date in the terminal
python visualize.py --debug --date 2025-01-14 --lat 26.9124 --lon 75.7873
```

## 12. Running Tests

```bash
python -m unittest discover -s tests -v
```

Install the dependencies first, because the tests import application modules that require packages such as `pyswisseph`, `Flask`, `requests`, and `reportlab`.

## 13. Troubleshooting

### The server does not start

Check whether port `5000` is already in use by another process.

### City search does not work

Check internet access and Nominatim availability. Manual coordinates still work offline.

### PDF generation fails

Check that the dependencies from `requirements.txt` are installed and that the location is valid.

### Excel export fails

Check that `pandas` and `openpyxl` are installed.

### CLI generation is slow

Add `--workers N` to use parallel processing. A value of 4 is a reasonable starting point for most machines.
