# API Reference

The Flask app exposes JSON endpoints for location lookup, daily Panchang generation, month overview data, Choghadiya slots, range exports, PDF exports, and generated file downloads.

Unless noted otherwise, requests and responses are JSON.

## Location Inputs

Most generator endpoints accept either:

- `city`
- both `lat` and `lon`

Manual coordinates take the form:

```json
{
  "lat": 26.9124,
  "lon": 75.7873
}
```

If coordinates are used, latitude and longitude must be supplied together. If neither a city nor coordinates are provided, the request is rejected.

Supported ayanamsa names are:

- `Lahiri`
- `Raman`
- `Krishnamurti`

If `ayanamsa` is omitted, the app defaults to `Lahiri`.

## `GET /search-location`

Searches locations through Nominatim for autocomplete-style city selection.

Example:

```text
/search-location?q=jaipur
```

Response:

```json
{
  "results": [
    {
      "display_name": "Jaipur, Rajasthan, India",
      "lat": 26.9124,
      "lon": 75.7873
    }
  ]
}
```

An empty query returns an empty results list.

## `GET /get-coordinates`

Resolves a city or place name to coordinates.

Example:

```text
/get-coordinates?city=Jaipur
```

Response includes the normalized display name, latitude, and longitude. Depending on the geocoding result, additional location metadata may also be present.

## `POST /generate-panchang`

Generates the daily Panchang payload for one civil date and location.

Request:

```json
{
  "date": "2025-01-01",
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

You can also send a city:

```json
{
  "date": "2025-01-01",
  "city": "Jaipur",
  "ayanamsa": "Lahiri"
}
```

Response includes:

- resolved location and timezone
- sunrise, sunset, moonrise, moonset, and next sunrise
- Tithi, Jain Tithi, Nakshatra, Yoga, Karana, and Vara
- Sun Rashi and Moon Rashi
- Hindu month, Vikram Samvat, and Vira Nirvana Samvat
- rule metadata and reference snapshots

## `GET /month-overview`

Returns compact day-by-day Panchang fields for a Gregorian month. This endpoint is useful for calendar views.

Example:

```text
/month-overview?year=2026&month=4&lat=26.9124&lon=75.7873&ayanamsa=Lahiri
```

Required query parameters:

- `year`
- `month`
- `city` or both `lat` and `lon`

Validation:

- `month` must be between `1` and `12`
- `year` must be between `1900` and `2200`

Response includes:

- Gregorian year and month
- resolved location and timezone
- Hindu month summary from the first generated day
- Vikram Samvat
- one entry per day with Tithi, Nakshatra, Vara, end times, and flags for Purnima, Amavasya, and Ekadashi

## `POST /choghadiya`

Generates eight daytime and eight nighttime Choghadiya slots for a date and coordinates.

Request:

```json
{
  "date": "2026-04-18",
  "lat": 26.9124,
  "lon": 75.7873
}
```

Response includes:

- date
- sunrise time
- sunset time
- 16 slots total

Each slot includes:

- `name`
- `meaning`
- `nature`
- `start_time`
- `end_time`
- `period`

## `POST /generate-range-panchang`

Generates downloadable CSV, Excel, JSON, or all-format exports for a year range.

Request:

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

Supported formats:

- `csv`
- `excel`
- `json`
- `all`

Response includes:

- resolved location
- requested year range
- format and monthly mode
- worker count
- rows generated
- generated file names and download URLs

Generated files are stored under `/tmp/jain_panchang_exports` and exposed through `/downloads/<token>`.

## `POST /generate-pdf-panchang`

Generates a downloadable year PDF calendar.

Request:

```json
{
  "year": 2025,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

Response includes:

- year
- ayanamsa
- resolved location
- PDF filename and download URL

## `POST /generate-jain-festivals`

Generates all Jain festival occurrences for a given year, location, and sectarian profile.

Request:

```json
{
  "year": 2025,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri",
  "profile": "shwetambar_murtipujak_tapagachchha"
}
```

Supported profiles:

- `shwetambar_murtipujak_tapagachchha`
- `shwetambar_sthanakvasi`
- `shwetambar_terapanthi`

Response includes:

- year
- profile
- resolved location with timezone
- list of festival entries

Each festival entry includes:

- `id` — unique identifier for the festival rule
- `name` — English name
- `name_hindi` — Hindi name
- `category` — `festival`, `kalyanak`, or `parva`
- `start_date` and `end_date` — ISO date strings
- `jain_month` — Jain lunar month name
- `paksha` — `Shukla` or `Krishna`
- `tithi` — Tithi number (1–30)
- `profile` — which profile this entry belongs to
- `status` — `observed` or `skipped` (kshaya/vriddhi handling)
- `meaning` — short description
- `observance` — how to observe
- `sources` — list of reference URLs

## `POST /generate-jain-festival-exports`

Generates downloadable CSV, Excel, or JSON exports of Jain festivals for a year range.

Request:

```json
{
  "start_year": 2025,
  "end_year": 2026,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri",
  "profile": "shwetambar_murtipujak_tapagachchha",
  "format": "csv"
}
```

Response structure matches the range export response with generated file names and download URLs.

## `POST /dainika-muhurta`

Detects active Dainika (daily) Yogas and returns an overall day recommendation.

Request:

```json
{
  "date": "2025-01-01",
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

Response includes:

- `date`
- `vara` — weekday index (0–6)
- `tithi` — Tithi index at sunrise
- `nakshatra` — Nakshatra index at sunrise
- `yogas` — list of detected yoga entries
- `recommendation` — overall day classification: `highly_auspicious`, `auspicious`, `caution`, or `avoid`

Each yoga entry includes:

- `name`
- `nature` — `shubh` or `ashubh`
- `severity` — `highly_auspicious`, `auspicious`, `inauspicious`, or `highly_inauspicious`
- `trigger_kind` — `tithi` or `nakshatra`
- `meaning`
- `start_time` and `end_time`
- `cancelled` — boolean, true when an auspicious yoga negates an inauspicious one

## `POST /dainika-muhurta-export`

Exports Dainika Muhurta data for a year range as a downloadable workbook.

Request:

```json
{
  "start_year": 2025,
  "end_year": 2025,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

Response includes the generated file name and download URL.

## `POST /api/generate-db`

Triggers background pre-computation of a SQLite database for a location. The database covers the range 1950-01-01 through 2075-12-31 and is stored under `data/panchang_{city_slug}.db`. Pre-computed databases allow subsequent lookups to skip live astronomical calculations.

Request:

```json
{
  "lat": 26.9124,
  "lon": 75.7873
}
```

Response:

```json
{
  "status": "started",
  "city_slug": "jaipur_rajasthan_india"
}
```

## `GET /downloads/<token>`

Downloads a file generated by the range or PDF endpoints.

Download tokens are stored in memory in the running Flask process. They are convenient for local use, but they are not durable across server restarts.

## Error Format

Validation and runtime errors generally return:

```json
{
  "error": "Message describing the problem"
}
```

Common validation errors include:

- missing `date`
- missing `year`
- invalid `month`
- `start_year` greater than `end_year`
- incomplete latitude/longitude pair
- missing location input
- unsupported export format
