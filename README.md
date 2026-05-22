# Jain Panchang

Jain Panchang is a location-aware Panchang generator built with Flask and Swiss Ephemeris. It can generate a daily Panchang, month summaries, Choghadiya slots, year-range exports, and printable PDF calendars from either a searched city or manual latitude/longitude coordinates.

The project is designed for practical Panchang lookup and export workflows while keeping the astronomical calculations and rule assumptions visible in the code and documentation.

## What It Does

- Daily Panchang lookup from the web UI or API
- City search and timezone detection through Nominatim and TimezoneFinder
- Sunrise-bound Tithi, Nakshatra, Yoga, Karana, and Vara calculation
- Jain Tithi calculation using the sunrise `+2h24m` reference
- Month overview data for calendar-style UI views
- Day and night Choghadiya slot generation
- Year-range exports as CSV, Excel, JSON, or all formats
- Optional monthly split exports
- Printable year PDF generation
- CLI batch generation with optional multiprocessing
- Visualization and QA helpers for generated CSV files

## Scope

The current implementation is a sunrise-based Panchang engine.

It currently:

- determines the primary daily Tithi from the Tithi active at local sunrise
- computes daily Nakshatra, Yoga, Karana, and Vara from the same sunrise reference
- computes Jain Tithi from the Tithi active 2 hours 24 minutes after local sunrise
- exposes reference data clearly so results can be inspected and compared

It does not yet claim to be a complete Agamic or sect-specific Jain calendrical authority. Use the output with that distinction in mind, especially for strict religious decision-making.

## Quick Start

Create an environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the web app:

```bash

```

Open:

```text
http://127.0.0.1:5000
```

Run a CLI export:

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Web App Workflows

The app has five main user-facing workflows:

1. Daily Panchang lookup
2. Month overview lookup
3. Choghadiya slot lookup
4. Year-range export generation
5. Printable PDF calendar generation

Daily lookup returns sunrise, sunset, moonrise, moonset, Tithi, Jain Tithi, Nakshatra, Pada, Yoga, Karana, Vara, Sun Rashi, Moon Rashi, Hindu month, Vikram Samvat, and Vira Nirvana Samvat.

Range exports and PDFs reuse the selected location and ayanamsa. Generated files are stored in temporary directories and served through short-lived download tokens.

## CLI Examples

Single-year CSV:

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv
```

Multi-year Excel with workers:

```bash
python main.py --start_year 2025 --end_year 2030 --lat 26.9124 --lon 75.7873 --format excel --workers 4
```

Monthly JSON files:

```bash
python main.py --start_year 2025 --end_year 2026 --lat 26.9124 --lon 75.7873 --format json --monthly
```

All supported flat formats:

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format all
```

Use a non-default ayanamsa and timezone label:

```bash
python main.py --start_year 2025 --end_year 2025 --lat 19.0760 --lon 72.8777 --ayanamsa Krishnamurti --tz_offset 5.5 --tz_label IST
```

Supported ayanamsas:

- `Lahiri`
- `Raman`
- `Krishnamurti`

## API Overview

Core endpoints:

- `GET /search-location?q=jaipur`
- `GET /get-coordinates?city=Jaipur`
- `POST /generate-panchang`
- `GET /month-overview`
- `POST /choghadiya`
- `POST /generate-range-panchang`
- `POST /generate-pdf-panchang`
- `GET /downloads/<token>`

Daily Panchang request:

```json
{
  "date": "2025-01-01",
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

Range export request:

```json
{
  "start_year": 2025,
  "end_year": 2026,
  "lat": 26.9124,
  "lon": 75.7873,
  "format": "csv",
  "monthly": false,
  "workers": 1,
  "ayanamsa": "Lahiri"
}
```

PDF request:

```json
{
  "year": 2025,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

See [API reference](./docs/api.md) for request and response notes.

## Project Structure

```text
Jain_panchang/
├── app.py                      Flask app factory, routes, file downloads
├── main.py                     CLI entry point and batch generation engine
├── request_parsing.py          Shared request validation
├── panchang_service.py         Daily Panchang orchestration
├── range_generation_service.py Web range export orchestration
├── pdf_generation_service.py   Web PDF export orchestration
├── astronomy.py                Swiss Ephemeris wrapper and time helpers
├── panchang.py                 Panchang formulas and rule helpers
├── location_service.py         Geocoding and timezone lookup
├── export.py                   CSV, Excel, and JSON serialization
├── export_pdf.py               PDF generation
├── visualize.py                CSV visualization and debug tools
├── templates/index.html        Web UI
├── static/                     Frontend JavaScript and CSS
├── tests/                      Unit and API tests
└── docs/                       Long-form documentation
```

## Important Notes

- City search requires internet access because it uses Nominatim.
- Daily API output uses the resolved IANA timezone for local civil dates.
- Range and PDF exports use a timezone offset snapshot for the whole run. This is simple and works well for India-focused usage, but it is not daylight-saving aware for every date in every location.
- Download URLs are stored in memory and are only valid for the current Flask process.
- Generated export files are placed under `/tmp/jain_panchang_exports`.

## Documentation

- [Documentation index](./docs/index.md)
- [Setup and usage](./docs/setup_and_usage.md)
- [API reference](./docs/api.md)
- [Architecture](./docs/architecture.md)
- [Components](./docs/components.md)
- [Calculations](./docs/calculations.md)
- [Visualizations](./docs/visualizations.md)
