# Setup and Usage

This guide is written primarily for people who want to run and use the application.

## 1. Requirements

You need:

- Python 3.9 or newer
- the dependencies listed in `requirements.txt`
- internet access if you want to use city search, because geocoding depends on Nominatim

## 2. Installation

Create and activate a virtual environment if you want an isolated setup, then install dependencies:

```bash
pip install -r requirements.txt
```

Typical packages used by the project include:

- `pyswisseph`
- `flask`
- `requests`
- `timezonefinder`
- `pandas`
- `openpyxl`
- `reportlab`

## 3. Running the Web App

Start the development server:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The web app currently contains three generator sections:

1. single-date Panchang
2. year-range export
3. printable PDF generation

## 4. Using the Daily Panchang Generator

The first section is designed for day-level inspection.

### Input options

You can either:

- search for a city and select one of the location suggestions
- manually enter latitude and longitude

If you use city search, the coordinate fields are filled automatically when you choose a suggestion.

### Required fields

- a valid location
- a valid date
- optionally an ayanamsa choice

### Output

The result includes:

- sunrise
- sunset
- moonrise
- moonset
- next sunrise
- Tithi
- Nakshatra and Pada
- Yoga
- Karana
- Vara
- moon rashi
- a structured JSON payload

### Rule display

The current daily generator shows:

- the primary sunrise-based rule
- a legacy special reference
- comparison snapshots for `+2h24m` and `+2h45m`

These references help inspect how labels differ at different offsets. They do not override the primary daily label.

## 5. Using the Year-Range Generator

The second section is designed for exports.

### How it works

The range generator reuses the same location and ayanamsa selection you already entered in the daily section.

You provide:

- `Start year`
- `End year`
- output `Format`
- optional `Monthly files`

### Available formats

- `csv`
- `excel`
- `json`
- `all`

### Output behavior

After generation, the interface returns:

- summary information such as rows generated and timezone used
- one or more downloadable files

If `Monthly files` is enabled, you receive one output file per month instead of one large file for the full range.

### Good use cases

- yearly Panchang archives
- data validation exports
- downstream spreadsheet analysis
- larger historical comparisons

## 6. Using the PDF Generator

The third section generates a printable PDF for a single year.

### Inputs

The PDF generator reuses:

- the current city or coordinates
- the current ayanamsa

You only need to provide:

- a target year

### Output

The app generates a downloadable PDF file named like:

```text
panchang_2025.pdf
```

The PDF currently renders monthly calendar-style tables for the selected year.

## 7. CLI Usage

The CLI is useful when:

- you prefer terminal workflows
- you want scripted generation
- you want multi-year exports without using the browser

### Single-year CSV example

```bash
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv
```

### Multi-year Excel example

```bash
python main.py --start_year 2025 --end_year 2030 --lat 26.9124 --lon 75.7873 --format excel --workers 4
```

### Monthly JSON example

```bash
python main.py --start_year 2025 --end_year 2026 --lat 26.9124 --lon 75.7873 --format json --monthly
```

## 8. API Overview

If you want to use the app programmatically, the main endpoints are:

- `GET /search-location`
- `GET /get-coordinates`
- `POST /generate-panchang`
- `POST /generate-range-panchang`
- `POST /generate-pdf-panchang`
- `GET /downloads/<token>`

## 9. Common Validation Rules

The server currently enforces:

- date is required for daily generation
- year is required for PDF generation
- `start_year <= end_year` for range generation
- coordinates must be numeric
- latitude and longitude must be provided together
- either a city or both coordinates must be supplied

## 10. Practical Notes

### Timezones

For daily results, the app uses the timezone inferred from coordinates and validates that the resolved sunrise belongs to the requested civil date.

For range and PDF export generation, the export pipeline currently uses a derived timezone label and offset snapshot for output formatting. This is aligned with the current engine and works well for the main India-based use case.

### Geocoding

Location search depends on Nominatim. If the service is unavailable or the network is blocked, city search may fail while manual coordinates still work.

### Performance

Small requests such as daily generation are quick. Multi-year exports and PDF generation can take longer depending on range size, output format, and machine speed.

## 11. Running Tests

```bash
python -m unittest discover -s tests -v
```

## 12. Troubleshooting

### The server does not start

Check whether port `5000` is already in use by another process.

### City search does not work

Check internet access and Nominatim availability. Manual coordinates should still work.

### PDF generation fails

Check that the location is valid and the `reportlab` dependency is installed correctly.

### Excel export fails

Check that `pandas` and `openpyxl` are installed.
