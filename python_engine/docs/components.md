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
- `GET /month-overview`
- `POST /choghadiya`
- `POST /generate-range-panchang`
- `POST /generate-pdf-panchang`
- `POST /generate-jain-festivals`
- `POST /generate-jain-festival-exports`
- `POST /dainika-muhurta`
- `POST /dainika-muhurta-export`
- `POST /api/generate-db`
- `GET /api/generate-db/progress/<city_slug>`
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
- the month overview endpoint also depends on this module for each day in the requested month

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

## `choghadiya_service.py`

This module calculates Choghadiya (auspicious time) slots for a day.

It provides:

- `calculate_choghadiya_slots()` — divides daytime and nighttime into 8 slots each
- Slot names: Udveg, Char, Labh, Amrit, Kaal, Shubh, Rog
- Nature classification: auspicious or inauspicious
- Starting slot determination from the weekday (Vara)
- Time output in both local and UTC formats

Why it matters:

- Choghadiya is one of the most-used tools for auspicious time selection in Jain and Hindu practice
- keeping it as a separate service isolates the slot-math from Flask route code

## `dainika_muhurta_service.py`

This module detects active Dainika (daily) Yogas and produces a day-level recommendation.

It provides:

- `detect_yogas_for_day()` — given Vara, Tithi, Nakshatra, and event times, returns all active yogas and a composite recommendation
- a built-in yoga registry with trigger mappings (Vara → Tithi list or Vara → Nakshatra list)
- cancellation logic: auspicious yogas can cancel inauspicious ones
- severity levels: `highly_auspicious`, `auspicious`, `inauspicious`, `highly_inauspicious`
- overall recommendation derived from the highest-impact uncancelled yoga

Why it matters:

- Dainika Muhurta is a Jain-specific daily practice tool
- centralizing the yoga rules here makes it easy to add or correct yoga entries without touching Flask routes or astronomy code

## `jain_festival_service.py`

This module generates Jain festival occurrences for a year and sectarian profile.

It provides:

- `generate_jain_festivals()` — main entry point; produces a dated list of festival entries for any year between 1900 and 2100
- vriddhi (extra day) and kshaya (skipped day) handling for festivals that fall on astronomically compressed or doubled Tithis
- profile-specific festival filtering across three Shwetambar profiles

Why it matters:

- Jain festival dates shift year to year because they follow the lunar calendar
- the service computes dates from astronomical first principles rather than a static lookup table
- it is the only place where sect-specific profile logic should live

## `jain_festival_rules.py`

This module is the static registry of Jain festival rules.

It contains:

- the list of all known festivals with their canonical Jain month, paksha, and Tithi
- metadata per festival: English name, Hindi name, category, meaning, observance notes, sources
- profile membership: which profiles observe which festivals
- vriddhi and kshaya handling markers per festival

Why it matters:

- separating the static rule data from the dynamic occurrence computation keeps `jain_festival_service.py` focused on calculation logic
- when a new festival needs to be added or corrected, this is the only file that needs updating

## `db_generator.py`

This module pre-computes a SQLite database of Panchang data for a single location.

It provides:

- `generate_db()` — generates daily rows for 1950-01-01 through 2075-12-31 and writes them to a SQLite file
- multi-table storage: `panchang_days`, `panchang_daily_events`, `panchang_transits`, and others
- background-thread execution invoked through the `/api/generate-db` endpoint
- progress tracking accessible via `/api/generate-db/progress/<city_slug>`

Why it matters:

- pre-computed databases let the web app serve daily lookups without live Swiss Ephemeris calls
- the generation is slow but runs once per location and then acts as a fast cache

## `db_reader.py`

This module provides query utilities for pre-computed SQLite databases.

It provides:

- `read_day()` — fetch a single day's Panchang from the database
- helper functions for reading month or year ranges
- graceful fallback when the database file does not exist for a location

Why it matters:

- it gives the rest of the app a clean interface to the pre-computed data layer
- the daily service can check for a database hit before falling back to live calculation

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

Defines the main UI structure and result panels. Location and ayanamsa inputs are shared at the page level across the generator flows.

### `static/app.js`

Handles:

- city search with autocomplete suggestions
- payload construction for each generator
- fetch calls to the backend API
- result rendering for daily Panchang output
- download-link display for exports and PDFs

### `static/app.css`

Controls layout, card styling, responsiveness, and visual grouping for the generator flows.

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
