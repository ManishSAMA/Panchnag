# Jain Panchang

Jain Panchang is a location-aware Panchang generator built on Swiss Ephemeris. It provides:

- a Flask web interface for daily lookup
- year-range export generation from the UI or CLI
- printable PDF generation from the UI
- a CLI for larger batch generation
- JSON, CSV, Excel, and PDF outputs

The project is intended to make Panchang generation practical for both day-to-day use and larger archival and export workflows, while keeping the underlying astronomy and Panchang math explicit and maintainable.

## Current Scope

The current implementation is best described as a sunrise-based Panchang engine with comparison reference snapshots.

What that means:

- the primary daily Tithi is determined from the Tithi active at local sunrise
- the daily Nakshatra, Yoga, Karana, and Vara are computed from the same sunrise reference
- the Jain Tithi is determined from the Tithi active `+2h24m` (2 hours 24 minutes) after local sunrise

What that does not mean:

- this is not yet a finalized Agamic Jain calendrical rules engine
- the comparison snapshots are inspection aids and do not override the primary daily label

That distinction is important, especially if you intend to use this system for strict sect-specific calendrical decisions.

## Main User Flows

### 1. Daily Panchang

Use the web app to:

- search for a city or enter manual coordinates
- pick a date
- choose an ayanamsa (Lahiri, Raman, or Krishnamurti)
- inspect sunrise, sunset, moonrise, moonset, all five Panchang elements, and rule snapshots

### 2. Year-Range Export

Use the web app or CLI to generate:

- a single year such as `2025`
- a multi-year range such as `2025` to `2030`
- monthly-split output files if needed

Supported export formats:

- CSV
- Excel
- JSON
- all supported formats in one run

### 3. Printable PDF

Use the web app to generate a year-wise PDF calendar for the selected location and ayanamsa. The PDF renders month-by-month tables with Tithi, Jain Tithi, Nakshatra, Yoga, Karana, Moon Rashi, Sun Rashi, sunrise, sunset, and Vara.

## Project Structure

```
Jain_panchang/
├── app.py                      Flask app factory, API routes, file downloads
├── main.py                     CLI entry point and batch generation engine
├── request_parsing.py          Shared validation for all API payloads
├── panchang_service.py         Daily Panchang orchestration and payload assembly
├── range_generation_service.py Web-facing multi-year export orchestration
├── pdf_generation_service.py   Web-facing PDF generation orchestration
├── astronomy.py                Swiss Ephemeris wrapper and time utilities
├── panchang.py                 Tithi, Nakshatra, Yoga, Karana, Vara math
├── location_service.py         Geocoding and timezone resolution
├── export.py                   CSV, Excel, and JSON serialization
├── export_pdf.py               PDF table generation via ReportLab
├── visualize.py                Planetary charts and debug tools
├── templates/index.html        Single-page web UI
├── static/app.js               Client-side interaction logic
├── static/app.css              Frontend styling
├── tests/
│   ├── test_api.py             API endpoint and validation tests
│   ├── test_panchang_rules.py  Sunrise and rule-model tests
│   ├── test_weekday_outputs.py Weekday consistency tests
│   └── test_output_formatting.py Output serialization tests
└── docs/                       Long-form documentation
```

## Quick Start

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the web app

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

### Run the CLI

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv
```

## API Endpoints

### `GET /search-location?q=jaipur`

Searches locations via Nominatim and returns lightweight suggestions for city autocomplete.

### `GET /get-coordinates?city=Jaipur`

Resolves a city or place string to a normalized coordinate result including timezone.

### `POST /generate-panchang`

Generates a daily Panchang JSON payload.

Example:

```json
{
  "date": "2025-01-01",
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

### `POST /generate-range-panchang`

Generates downloadable CSV, Excel, or JSON exports for a year range.

Example:

```json
{
  "start_year": 2025,
  "end_year": 2026,
  "lat": 26.9124,
  "lon": 75.7873,
  "format": "csv",
  "monthly": false,
  "ayanamsa": "Lahiri"
}
```

### `POST /generate-pdf-panchang`

Generates a downloadable year-wise PDF calendar.

Example:

```json
{
  "year": 2025,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

### `GET /downloads/<token>`

Serves a previously generated file by its UUID token.

## Developer Notes

### Validation strategy

Request validation is intentionally centralized in `request_parsing.py`. This keeps Flask route handlers thin and makes it easier to add new generators without duplicating coordinate, year, or format validation logic.

### Location handling

The app supports two input styles:

- city search with automatic coordinate lookup
- direct latitude and longitude input

`panchang_service.resolve_location()` is the shared boundary for normalizing both inputs into a consistent `ResolvedLocation` object.

### Timezone behavior

The daily web generator uses a location-derived IANA timezone and validates that the resolved sunrise belongs to the requested civil date.

The range and PDF generators derive a timezone label and offset snapshot for export formatting. This works well for the main India-based use case and keeps the export engine compatible with the existing CLI pipeline, but it is a fixed offset for the whole export. Locations with daylight-saving transitions can therefore show drifted civil times in range and PDF outputs.

### Generated downloads

Generated range exports and PDFs are written to temporary directories under `/tmp` and exposed through per-process UUID download tokens. Those download URLs are convenient for the current running server, but they are not durable across app restarts and there is no built-in cleanup lifecycle yet.

### Parallel batch generation

The CLI and range export engine support parallel processing via `multiprocessing.Pool`. Worker count is configurable. Day-level computation is fully independent, so parallelism scales well over multi-year ranges.

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

The test modules import the application directly, so install the dependencies from `requirements.txt` before running them.

Verify syntax for the main Python modules:

```bash
python -m py_compile app.py panchang_service.py request_parsing.py range_generation_service.py pdf_generation_service.py
```

## Documentation

- [Documentation index](./docs/index.md)
- [Setup and usage](./docs/setup_and_usage.md)
- [Architecture](./docs/architecture.md)
- [Components](./docs/components.md)
- [Calculations](./docs/calculations.md)
- [Visualizations](./docs/visualizations.md)
