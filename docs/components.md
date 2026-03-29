# Components

This document explains the responsibility of each important module in the repository.

## `app.py`

`app.py` is the Flask entry point and web delivery layer.

It is responsible for:

- creating the Flask app
- serving the main HTML page
- exposing API endpoints
- turning generated files into downloadable responses

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
- integers
- numeric coordinates
- complete lat/lon pairs
- output formats
- workers count

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
- daily solar event computation
- sunrise validation
- daily Panchang payload assembly
- comparison reference snapshot assembly

Important concepts inside this module:

- `ResolvedLocation`
- `DailyEventSet`
- `_calculate_daily_events()`
- `generate_location_panchang()`

Why it matters:

- it is the main bridge between raw astronomy and the user-facing daily payload
- if daily rule behavior changes, this is the first place to inspect

## `range_generation_service.py`

This module powers the year-range export path used by the web UI.

It is responsible for:

- resolving the location once
- deriving a timezone export label and offset
- building generation config for the existing runner
- generating rows for the requested range
- exporting files into a temporary directory
- returning file metadata for download

Why it matters:

- it allows the web app to reuse the existing CLI compute engine
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

This is the CLI entry point and the existing computation runner used by range exports.

It contains:

- CLI argument parsing
- worker configuration
- multiprocessing support
- date iteration
- day-level row computation
- export dispatch

Important internal concepts:

- `_init_worker()`
- `_compute_day()`
- `_dates_in_range()`
- `run_generation()`

Why it matters:

- it is still the core batch-generation engine
- the range web generator intentionally reuses this logic instead of replacing it

## `astronomy.py`

This module wraps Swiss Ephemeris and time conversions.

It provides:

- Julian Day conversion
- timezone-aware datetime to JD conversion
- local civil date anchors
- ayanamsa configuration
- planetary longitude retrieval
- sunrise, sunset, moonrise, and moonset
- JD back to local time conversion

Why it matters:

- it is the lowest-level astronomical boundary in the app
- errors here affect every generator path

## `panchang.py`

This module contains the Panchang mathematics.

It defines:

- Tithi names
- Nakshatra names
- Yoga names
- Vara names
- Karana cycle logic

It computes:

- Tithi
- Nakshatra
- Nakshatra Pada
- Yoga
- Karana
- Vara
- Tithi and Nakshatra end times using bracketing and bisection

Why it matters:

- it holds the formula-level Panchang logic
- it should remain as pure and testable as possible

## `export.py`

This module serializes row data to flat formats.

It handles:

- row shaping
- CSV export
- JSON export
- Excel export
- multi-format dispatch

Why it matters:

- it isolates file writing from computation
- it gives the CLI and range web path a single export layer

## `export_pdf.py`

This module renders printable monthly PDF tables.

It uses:

- ReportLab
- sunrise-based daily Panchang evaluation
- table layouts for each month

It includes:

- PDF page assembly
- monthly tables
- Tithi and Nakshatra end-time display
- ghati/pala formatting for event intervals

Why it matters:

- it is presentation-heavy and intentionally separate from flat-file export

## Frontend Files

### `templates/index.html`

Defines the main UI structure with three generator sections and multiple result panels.

### `static/app.js`

Handles:

- city search
- payload creation
- fetch calls to the backend
- result rendering
- download-link display

### `static/app.css`

Controls layout, card styling, responsiveness, and visual grouping of the three generators.

## Test Files

### `tests/test_api.py`

Covers:

- route behavior
- validation behavior
- range export endpoint behavior
- PDF endpoint behavior

### `tests/test_panchang_rules.py`

Covers:

- sunrise-bound Tithi behavior
- special/comparison reference behavior
- coordinate validation
- sunrise resolving to the requested local date
