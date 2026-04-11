# Components

This document explains the responsibility of each important module in the repository.

## `app.py`

`app.py` is the Flask entry point and web delivery layer.

It is responsible for:

- creating the Flask app
- serving the main HTML page
- exposing API endpoints
- turning generated files into downloadable responses via UUID tokens

Current endpoints:

- `GET /`
- `GET /search-location`
- `GET /get-coordinates`
- `POST /generate-panchang`
- `POST /generate-range-panchang`
- `POST /generate-pdf-panchang`
- `GET /downloads/<token>`

Why it matters:

- it should stay thin
- it should avoid business logic
- it should mostly delegate to parsing and service modules

## `request_parsing.py`

This module centralizes API request validation and normalization.

It contains dedicated parsing functions for:

- daily generation
- range generation
- PDF generation

It validates:

- required fields
- integer year fields
- numeric coordinates
- complete lat/lon pairs
- allowed output formats
- workers count

It currently passes ayanamsa names through without validating them against the supported set.

Why it matters:

- keeps Flask routes short
- prevents repeated validation logic
- makes new routes easier to add consistently

## `panchang_service.py`

This is the main daily orchestration module.

It handles:

- date coercion
- location resolution
- coordinate validation
- timezone resolution
- daily solar and lunar event computation
- sunrise validation
- daily Panchang payload assembly
- comparison reference snapshot assembly

Important concepts inside this module:

- `ResolvedLocation`: normalized result of location input (city or coordinates)
- `DailyEventSet`: structured container for sunrise, sunset, moonrise, moonset
- `_calculate_daily_events()`: computes all solar and lunar events for a day
- `generate_location_panchang()`: main orchestrator that assembles the full daily JSON payload

Why it matters:

- it is the main bridge between raw astronomy and the user-facing daily payload
- if daily rule behavior changes, this is the first place to inspect

## `range_generation_service.py`

This module powers the year-range export path used by the web UI.

It is responsible for:

- resolving the location once
- deriving a timezone export label and offset snapshot
- building generation config for the existing runner
- generating rows for the requested date range
- exporting files into a temporary directory
- returning file metadata for download

Why it matters:

- it allows the web app to reuse the existing CLI compute engine without duplicating logic
- it isolates range-specific workflow concerns from Flask route code

## `pdf_generation_service.py`

This module powers the web PDF path.

It is responsible for:

- resolving the location
- deriving the timezone export snapshot
- creating a temporary output directory
- calling the PDF exporter
- returning the generated file metadata

Why it matters:

- it gives PDF generation a dedicated orchestration layer
- it prevents the PDF route from becoming large or procedural

## `main.py`

This is the CLI entry point and the core computation runner reused by range exports.

It contains:

- CLI argument parsing via argparse
- worker configuration
- multiprocessing support via `multiprocessing.Pool`
- date iteration
- day-level row computation
- export dispatch

Important internal concepts:

- `_init_worker()`: initializer that shares config across worker processes
- `_compute_day()`: per-day computation producing a flat row dict
- `_dates_in_range()`: date iterator for a start/end year pair
- `run_generation()`: main callable used by both CLI and the range web service

Why it matters:

- it is the core batch-generation engine
- the range web generator intentionally reuses this logic instead of duplicating it

## `astronomy.py`

This module wraps Swiss Ephemeris and time conversion utilities.

It provides:

- Julian Day conversion
- timezone-aware datetime to JD conversion
- local civil date anchors for day-level computation
- ayanamsa configuration (Lahiri, Raman, Krishnamurti)
- planetary longitude retrieval for 9 planets
- sunrise, sunset, moonrise, and moonset computation
- JD back to local time conversion

Why it matters:

- it is the lowest-level astronomical boundary in the app
- errors here affect every generator path

## `panchang.py`

This module contains the Panchang mathematics.

It defines:

- Tithi names (30)
- Nakshatra names (27)
- Yoga names (27)
- Vara names (7)
- Karana cycle logic (11 types)

It computes:

- Tithi and Tithi index
- Nakshatra and Nakshatra Pada
- Yoga
- Karana
- Vara
- Tithi and Nakshatra end times using bracketing and bisection

Why it matters:

- it holds the formula-level Panchang logic
- it should remain as pure and testable as possible

## `location_service.py`

This module handles geocoding and timezone resolution.

It provides:

- Nominatim-based city and place name search
- latitude and longitude resolution from a city string
- IANA timezone resolution from coordinates via TimezoneFinder
- LRU caching for geocode results to avoid redundant network calls

Why it matters:

- it isolates external network dependencies from the rest of the app
- it gives the service layer a clean, cached boundary for location resolution

## `export.py`

This module serializes row data to flat formats.

It handles:

- row shaping and DMS formatting for planet longitudes
- CSV export
- JSON export
- Excel export
- multi-format dispatch

Why it matters:

- it isolates file writing from computation
- it gives the CLI and range web path a single, consistent export layer

## `export_pdf.py`

This module renders printable monthly PDF tables.

It uses:

- ReportLab for PDF generation
- sunrise-based daily Panchang evaluation per day
- monthly table layouts for an entire year

It includes:

- PDF page assembly
- monthly Panchang tables
- continuity-aware Tithi and Nakshatra display
- Jain Tithi, Karana, Moon Rashi, Sun Rashi, sunrise, and sunset columns
- month headers that can show more than one lunar month when a Gregorian month spans a transition

Why it matters:

- it is presentation-heavy and intentionally separate from flat-file export
- PDF layout concerns do not belong in the general export layer

## `visualize.py`

This module provides visual debugging and analysis tools for generated Panchang data.

It handles:

- planetary sidereal longitude charts over time
- Tithi frequency bar charts
- Panchang element heatmaps by month
- CSV diff comparisons for QA between two datasets
- single-day console debug dumps

See [Visualizations](./visualizations.md) for usage examples.

Why it matters:

- it is useful during development for verifying calculation correctness
- it supports QA workflows when switching ayanamsas or changing calculation logic

## Frontend Files

### `templates/index.html`

Defines the main UI structure with three generator sections and multiple result panels. Location and ayanamsa inputs are shared at the page level across all three generators.

### `static/app.js`

Handles:

- city search with autocomplete suggestions
- payload construction for each generator
- fetch calls to the backend API
- result rendering for daily Panchang output
- download-link display for exports and PDFs

### `static/app.css`

Controls layout, card styling, responsiveness, and visual grouping of the three generator sections.

## Test Files

### `tests/test_api.py`

Covers:

- route behavior for all endpoints
- validation behavior for malformed inputs
- range export endpoint behavior
- PDF endpoint behavior

### `tests/test_panchang_rules.py`

Covers:

- sunrise-bound Tithi behavior
- comparison reference snapshot behavior
- coordinate validation
- sunrise resolving to the requested local date

### `tests/test_weekday_outputs.py`

Covers:

- Vara (weekday) consistency across generated output rows
- weekday alignment with local civil dates

### `tests/test_output_formatting.py`

Covers:

- continuity formatting for repeated Tithi, Nakshatra, and Yoga values
- helper-field stripping before flat-file export
