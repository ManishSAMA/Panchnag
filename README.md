# Jain Panchang

Jain Panchang is a location-aware Panchang generator built on top of Swiss Ephemeris. It provides:

- a Flask web interface for daily lookup
- year-range export generation from the UI
- printable PDF generation from the UI
- a CLI for larger batch generation
- JSON, CSV, Excel, and PDF outputs

The project is intended to make Panchang generation practical for both day-to-day use and larger archival/export workflows while keeping the underlying astronomy and Panchang math explicit and maintainable.

## Current Scope

The current implementation is best described as a sunrise-based Panchang engine with comparison reference snapshots.

What that means:

- the primary daily Tithi is determined from the Tithi active at local sunrise
- the daily Nakshatra, Yoga, Karana, and Vara are computed from the same sunrise reference
- the API also exposes comparison snapshots for `+2h24m` and `+2h45m`

What that does not mean:

- this is not yet a finalized Agamic Jain calendrical rules engine
- the comparison snapshots are inspection aids and do not override the primary daily label

That distinction is important, especially if you intend to use this system for strict sect-specific calendrical decisions.

## Main User Flows

### 1. Daily Panchang

Use the web app to:

- search for a city or enter manual coordinates
- pick a date
- choose an ayanamsa
- inspect sunrise, sunset, moonrise, moonset, Panchang elements, and rule snapshots

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

Use the web app to generate a year-wise PDF calendar for the current location and ayanamsa selection.

## Project Structure

### Runtime and API

- `app.py`  
  Flask application factory, API routes, and file downloads.

- `request_parsing.py`  
  Shared validation for daily, range, and PDF API payloads.

### Panchang orchestration

- `panchang_service.py`  
  Daily Panchang assembly, location resolution, solar event checks, and rule payload construction.

- `range_generation_service.py`  
  Web-facing multi-year export orchestration.

- `pdf_generation_service.py`  
  Web-facing PDF orchestration.

### Core calculations

- `astronomy.py`  
  Swiss Ephemeris wrapper and time conversion utilities.

- `panchang.py`  
  Tithi, Nakshatra, Yoga, Karana, Vara, and transition-finding logic.

### Output and presentation

- `export.py`  
  CSV, Excel, and JSON output serialization.

- `export_pdf.py`  
  PDF table generation using ReportLab.

- `templates/index.html`  
  Main web interface.

- `static/app.js`  
  Client-side interaction logic for the three generators.

- `static/app.css`  
  Frontend styling.

### CLI and tests

- `main.py`  
  CLI entry point and generation engine.

- `tests/test_api.py`  
  API behavior tests.

- `tests/test_panchang_rules.py`  
  Sunrise and rule-model tests.

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

Searches locations using Nominatim and returns lightweight suggestions.

### `GET /get-coordinates?city=Jaipur`

Resolves a city or place string to a normalized coordinate result.

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

Generates downloadable CSV/Excel/JSON exports.

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

Generates a downloadable year-wise PDF.

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

Serves a generated file by token.

## Developer Notes

### Validation strategy

Request validation is intentionally centralized in `request_parsing.py`. This keeps Flask handlers thin and makes it easier to add new generators without duplicating coordinate, year, or format validation logic.

### Location handling

The app supports two input styles:

- city search plus coordinate lookup
- direct latitude/longitude input

`panchang_service.resolve_location()` is the shared boundary for normalizing those inputs.

### Timezone behavior

The daily web generator uses a location-derived timezone and validates that sunrise resolves to the requested civil date.

The range and PDF generators currently derive a timezone label and offset snapshot for export formatting. This works well for the main India-based use case and keeps the export engine compatible with the existing CLI pipeline.

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

Optionally verify syntax for the main Python modules:

```bash
python -m py_compile app.py panchang_service.py request_parsing.py range_generation_service.py pdf_generation_service.py
```

## Documentation

- [Documentation index](./docs/index.md)
- [Setup and usage](./docs/setup_and_usage.md)
- [Architecture](./docs/architecture.md)
- [Components](./docs/components.md)
- [Calculations](./docs/calculations.md)
