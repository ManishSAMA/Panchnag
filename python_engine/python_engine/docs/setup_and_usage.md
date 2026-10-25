# Setup and Usage

This guide is for people who want to run the application locally, use the web UI, call the API, or generate exports from the command line.

## 1. Requirements

You need:

- Python 3.9 or newer
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

The web app contains the main generator flows:

1. single-date Panchang lookup
2. month overview data
3. Choghadiya slots
4. year-range export
5. printable PDF generation

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

## 5. Using the Month Overview Endpoint

The month overview endpoint returns compact day-level data for a Gregorian month. It is mainly intended for calendar-style UI views.

Example:

```text
/month-overview?year=2026&month=4&lat=26.9124&lon=75.7873&ayanamsa=Lahiri
```

The response includes one item per day with:

- Tithi name and index
- Tithi end time
- Nakshatra name and index
- Nakshatra end time
- Vara
- flags for Purnima, Amavasya, and Ekadashi

The endpoint requires `year`, `month`, and either a city or both coordinates.

## 6. Using Choghadiya

The Choghadiya endpoint returns eight daytime slots and eight nighttime slots.

Example request:

```json
{
  "date": "2026-04-18",
  "lat": 26.9124,
  "lon": 75.7873
}
```

Each slot includes a name, meaning, nature, start time, end time, and whether it belongs to the day or night period.

## 7. Using Jain Festival Generation

The Jain festival endpoint returns all Jain festival occurrences for a year, location, and sectarian profile.

### Supported profiles

- `shwetambar_murtipujak_tapagachchha`
- `shwetambar_sthanakvasi`
- `shwetambar_terapanthi`

Example request:

```json
{
  "year": 2025,
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri",
  "profile": "shwetambar_murtipujak_tapagachchha"
}
```

The response includes one entry per festival with:

- start and end dates
- Jain lunar month, paksha, and Tithi
- category: `festival`, `kalyanak`, or `parva`
- observance notes and sources
- vriddhi or kshaya status when applicable

Dates are computed from astronomical first principles, not a static lookup table. Festival dates shift year to year because they follow the Jain lunar calendar.

### Festival exports

The `/generate-jain-festival-exports` endpoint generates downloadable CSV, Excel, or JSON files for a range of years using the same request structure as the range Panchang generator, with an added `profile` field.

## 7b. Using Dainika Muhurta

The Dainika Muhurta endpoint detects active Jain daily Yogas and provides a day-level recommendation.

Example request:

```json
{
  "date": "2025-01-01",
  "lat": 26.9124,
  "lon": 75.7873,
  "ayanamsa": "Lahiri"
}
```

The response includes:

- detected yogas with name, nature, severity, start and end times, and cancellation status
- an overall `recommendation` field: `highly_auspicious`, `auspicious`, `caution`, or `avoid`

Yogas are matched from a built-in rule registry keyed by Vara, Tithi, and Nakshatra. Auspicious yogas can cancel inauspicious ones.

### Muhurta exports

The `/dainika-muhurta-export` endpoint generates a downloadable workbook with Muhurta data for every day in a requested year range.

## 9. Using the Year-Range Generator

The range generator is designed for bulk exports.

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

## 10. Using the PDF Generator

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

## 10b. Using the Hindi Calendar PDF

Settings → Export Panchang Data → **Hindi Calendar PDF (हिन्दी पंचांग)**.

It uses the current location and ayanamsa. You choose:

- start year and start month (default March, the Chaitra-to-Chaitra edition)
- number of months (1–24, default 13)

The PDF is printed by headless Playwright if it is installed, otherwise by
Microsoft Edge. Edge runs with a throwaway profile, so it works even while the
user has Edge open. When neither is available the app offers the `.html`
instead; open it and press Ctrl+P → Save as PDF.

## 10d. Using the Laghu Panchang (yearly booklet)

Settings → **Laghu Panchang (लघु पंचांग) — January to December**. Choose the year,
the format (PDF, Excel, or both) and the **kalyanak school**: All schools, or one
of 1 · Vrindavan, 2 · Uttarapurana, 3 · Ashadhara. The three traditions disagree
on some kalyanak tithis; with one chosen, the booklet prints only that school's
kalyanaks (parvas and vrats always appear). It uses the location, ayanamsa, Jain
profile, clock and sunrise rule currently set in the app.

The layout follows the printed *laghu panchang* booklet: one 8 × 5 inch landscape
page per month, two half-month tables per page. Each half has a four-line header
(Vira Nirvana and Vikram Samvat, the date span, the Hindu month/tithi span, and
sunrise/sunset on its first day) and these columns:

| Column | Meaning |
|---|---|
| शुभ दि. | `卐` when a *highly auspicious* yoga (Aanandadi, Dainika or Ravi; e.g. Amrit Siddhi, Sarvartha Siddhi, Guru Pushya) is in force at sunrise, else `-` |
| जैन तिथि / उदय तिथि | Tithi at sunrise + 2h24m (Jain) and at sunrise; 1–14, 15 = Purnima, 30 = Amavasya; Pratipada shows the Purnimanta month, e.g. `पौ.शु. 01`; a kshaya tithi shows as `3-4` |
| तिथि / नक्षत्र समाप्ति समय | End time counted from that day's midnight, so `25:47` means 01:47 the next morning; `अहोरात्र` when it outlasts the next sunrise |
| योग | Yoga at sunrise (abbreviated) |
| चन्द्र राशि प्रवेश | The Moon's sign, or the new sign and entry time (`वृ.-28:21`) when it changes before the next sunrise |
| पर्व, त्यौहार, पंचक आदि | The app's festivals and Kalyanaks for the profile, Bhadra (`भ. 25:47 से`), Panchak start/end |

Not included, because the app has no data for them: acharya/muni diksha and
samadhi anniversaries, and melas.

The PDF holds real Unicode Hindi text, so it can be searched and copied. Printing
uses Playwright or Edge as for the Hindi Calendar PDF. The Excel workbook has one
sheet per month with both halves side by side.

```bash
python main.py laghu --year 2027 --city Delhi --format both --output ./booklets
python main.py laghu --year 2027 --city Delhi --school vrindavan --format pdf
python main.py laghu --year 2027 --lat 40.2203 --lon -74.7658 --city Trenton --format pdf
```

Times follow the location's own clock, including daylight saving time.

## 10c. Building the Client Release

Clients get a self-contained folder instead of this repository:

```bash
python scripts/build_client_bundle.py
```

This writes `client_release/` and `client_release.zip` at the repo root (both
gitignored). The folder contains:

- `start.bat`: on first run, finds Python 3.11–3.14, creates `.venv`, and
  installs `requirements.txt`. Every run starts the app and opens the browser.
- `README.txt`: client-facing instructions
- `panchang_app/`: the web app, the modules it imports, `templates/`, `static/`,
  and `wheels/` (bundled pre-compiled wheels for `pyswisseph` so no C++ compiler is needed).

The module list is found by following imports from `client_files/run_client.py`,
so there is no file list to maintain. Re-run the script after every change.
`tests/test_client_bundle.py` checks that every import in the bundle resolves
from the bundle itself.

The bundle supports standard Windows Python 3.11, 3.12, 3.13, and 3.14. Pre-built
wheels for `pyswisseph` are included directly in the bundle so setup runs cleanly
without Microsoft Visual C++ Build Tools.

## 11. CLI Usage

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

### Hindi Excel example

`--language hi` writes Hindi headers and text values to a `_hi` file. The web UI's
range export has the same choice (Language: English / हिंदी).

```bash
python main.py --start_year 2027 --end_year 2027 --lat 40.2203 --lon -74.7658 --tz_offset -5 --tz_label EST --format excel --language hi
```

### Clock and sunrise rule

`--tz_name` names the zone instead of a fixed `--tz_offset`, which lets
`--clock` choose standard time (default) or the wall clock per day. `--sunrise`
picks the modern (default) or traditional rule. The same flags exist on
`main.py laghu`, and on `hindi_calendar_pdf.py` as `--tz-name`.

```bash
python main.py --start_year 2027 --end_year 2027 --lat 40.8333 --lon -74.1 --tz_name America/New_York --clock standard --sunrise traditional --format excel
```

## 12. API Overview

If you want to use the app programmatically, the main endpoints are:

- `GET /search-location?q=<query>` — city autocomplete
- `GET /get-coordinates?city=<name>` — resolve city to coordinates and timezone
- `POST /generate-panchang` — daily Panchang payload
- `GET /month-overview` — compact month data for calendar views
- `POST /choghadiya` — day and night Choghadiya slots
- `POST /generate-range-panchang` — multi-year export files
- `POST /generate-pdf-panchang` — year PDF
- `POST /generate-laghu-panchang` — yearly Laghu Panchang booklet (PDF / Excel)
- `POST /generate-jain-festivals` — Jain festival list for a year and profile
- `POST /generate-jain-festival-exports` — Jain festival export files
- `POST /dainika-muhurta` — daily Yoga detection and recommendation
- `POST /dainika-muhurta-export` — Muhurta workbook export
- `POST /api/generate-db` — trigger background database pre-computation
- `GET /downloads/<token>` — download a generated file by UUID token

For payload examples, see [API reference](./api.md).

## 13. Common Validation Rules

The server enforces:

- date is required for daily generation
- year is required for PDF generation
- year and month are required for month overview
- `start_year <= end_year` for range generation
- coordinates must be numeric
- latitude and longitude must be provided together
- either a city or both coordinates must be supplied
- output format must be one of `csv`, `excel`, `json`, or `all`

## 14. Generated Files

Generated range exports and PDFs are written under:

```text
/tmp/jain_panchang_exports
```

The browser receives tokenized download URLs such as:

```text
/downloads/<token>
```

Those tokens live in memory inside the running Flask process. If the process restarts, old download links stop working.

The UI offers `Lahiri`, `Raman`, and `Krishnamurti` ayanamsas. Unknown ayanamsa names currently fall back to Lahiri in the astronomy layer, so API clients should send one of those exact names.

## 15. Practical Notes

### Timezones, clock and sunrise rule

The timezone is inferred from the coordinates. Two settings in **Settings**
(also `--clock` / `--sunrise` on the CLIs and `clock` / `sunrise` in the API)
control how times are computed and shown:

- **Clock**: *Standard time all year* (default) or *Daylight saving time*
  (the wall clock). Printed panchangs for DST countries keep standard time all
  year; the New Jersey reference sheet prints EST through the summer. Zones
  without DST, such as India, read the same under both.
- **Sunrise**: *Modern* (default; upper limb with refraction) or *Traditional*
  (centre of the disc, no refraction), which printed panchangs use. Traditional
  sunrise is about 2–8 minutes later. Because the Udaya and Jain tithi are taken
  at sunrise, on rare days this moves which tithi owns a date, and with it a
  festival (in 2026–2027: Delhi on 30 Jun 2026 and 16 Mar 2027, New Jersey on a
  handful of days).

Exports under *Standard time* use the zone's real standard offset, so they are
right south of the equator as well. Under *Daylight saving time* each row
carries its own day's offset, and the column label names both abbreviations
(`Sunrise (EST/EDT)`).

Against the New Jersey reference (40°50′N 74°06′W, 2027) with standard time
and the traditional sunrise: sunrise agrees within a minute and tithi,
nakshatra and Moon-sign times run 2–3 minutes early, all year.

### Geocoding

Location search depends on Nominatim. If the service is unavailable or the network is blocked, city search may fail while manual coordinates still work.

### Performance

Single-date lookups are near-instant. Multi-year exports take longer depending on range size, output format, and machine speed. Use `--workers` to parallelize over multiple CPU cores for large ranges.

## 16. Visualization Tools

The `visualize.py` module provides charts and debugging utilities against generated CSV output. See [Visualizations](./visualizations.md) for full usage details.

Quick examples:

```bash
# Plot planetary motion for 2025
python visualize.py --file panchang_2025_2025.csv --plot planets --year 2025

# Debug a single date in the terminal
python visualize.py --debug --date 2025-01-14 --lat 26.9124 --lon 75.7873
```

## 17. Running Tests

```bash
python -m unittest discover -s tests -v
```

Install the dependencies first, because the tests import application modules that require packages such as `pyswisseph`, `Flask`, `requests`, and `reportlab`.

## 18. Troubleshooting

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
