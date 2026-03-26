# Jain Panchang

Location-aware daily Panchang generation powered by Swiss Ephemeris and a lightweight Flask frontend.

## What Changed

- Daily Panchang is now computed from the local sunrise for the requested date and coordinates.
- Udaya Tithi is the primary day rule.
- The special `+2h45m after sunrise` rule is exposed separately and only used where explicitly required by domain logic.
- Location search and coordinate lookup are available through OpenStreetMap Nominatim.
- Timezone handling is coordinate-based via IANA timezones, not hardcoded offsets.
- A small web UI is included for city search, coordinate autofill, date selection, and Panchang display.

## Project Structure

```text
app.py                  Flask app and API routes
astronomy.py            Swiss Ephemeris helpers and JD/timezone conversion
location_service.py     Geocoding and timezone resolution
panchang.py             Core Panchang math
panchang_service.py     Sunrise-based daily Panchang assembly
templates/index.html    Frontend page
static/app.css          Frontend styles
static/app.js           Frontend behavior
tests/test_api.py       Flask API tests
tests/test_panchang_rules.py  Panchang rule tests
main.py                 Existing CLI generator
```

## API Endpoints

- `GET /search-location?q=jaipur`
- `GET /get-coordinates?city=Jaipur`
- `POST /generate-panchang`

Example request:

```json
{
  "date": "2025-01-01",
  "city": "Jaipur",
  "ayanamsa": "Lahiri"
}
```

You can also send manual coordinates instead of a city:

```json
{
  "date": "2025-01-01",
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the web app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000`.

## Running Tests

```bash
python -m unittest discover -s tests
python test_panchang.py
```

## Panchang Rules Implemented

- `Udaya Tithi`: the civil day's Tithi is determined by the Tithi active at local sunrise.
- `Sunrise reference`: the returned daily Nakshatra, Yoga, Karana, and Vara are computed from the same sunrise reference.
- `Sunrise + 2h45m`: returned separately under `rules.special_reference` for domain-specific observances. It does not relabel the day.

## Notes

- Sunrise and sunset are computed dynamically from the requested date, latitude, and longitude.
- Timezone is inferred from coordinates using `timezonefinder`, then converted with Python `zoneinfo`.
- Geocoding uses the free Nominatim API, so internet access is required for city search and coordinate lookup.
