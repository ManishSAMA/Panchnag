# Core Components Breakdown

This page offers a comprehensive look at the specific responsibilities of each Python module that powers the application.

### `main.py`
The CLI gateway and central runner.
- **Argparse Integration**: Catches logic strings related to latitude, longitude, and output directives.
- **Multiprocessing Handler**: Subdivides chunks of date tuples (`year, month, day`) dynamically and assigns computational boundaries equally amongst native CPU cores. Initializes global namespace worker dictionaries (`_init_worker()`) to avoid parameter repassing latency.

### `astronomy.py`
The mathematical backend mapping generic data towards the Swiss Ephemeris (`swisseph`) API constraint list.
- **Constants**: Holds reference integers mapping textual planets back to Swiss Ephemeris IDs (`swe.SUN`, `swe.MOON`, `swe.TRUE_NODE`).
- **Sidereal Math**: Enforces the Ayanamsas configuration by mutating internal Swiss Engine environment configurations dynamically.
- **Celestial Events**: Exposes distinct methods (`get_sunrise()`, `get_moonset()`) that trigger ephemeris calculations correcting for atmospheric refraction directly on the coordinate system provided.
- **DMS Conversion**: Formats decimal angles `(e.g. 143.51)` to traditional Degree-Minute-Second layouts `(143° 30' 36")`.

### `panchang.py`
The spiritual interpreter transforming pure planetary coordinates into standard Vedic labels via static arrays and boundary constraint logics.
- **Name Lists**: Hardcoded standard array indices defining textual blocks over structural limits (27 Nakshatras, 30 Tithis).
- **Core Tithi/Yoga/Karana Generators**: Employs mathematical offsets to define absolute boundaries natively without referencing arbitrary API endpoints.
- **Target Approximation Seekers**: Enacts binary-search-styled loops `_find_exact_end_time()` discovering subsequent points of transition on arbitrary temporal intervals.
- **Ishta Kaala Tools**: Conversions mapping native intervals back to archaic constraints (Ghati and Pala layouts).

### `export.py`
Data homogenization tool preparing outputs. 
- Transmutes pure Python dictionary outputs directly into string-serialized structures appending necessary structural column definitions.
- Conditionally builds and bridges native calls out to `csv`, `json`, or Pandas/Openpyxl dataframe handlers dependent on CLI format toggles.

### `export_pdf.py`
A decoupled CLI utility focused exclusively on transforming parsed output into visually appealing document hierarchies via `reportlab`. It recalculates local constraints identically but forces the rendered loop through strict stylistic PDF Table structures rather than raw dataset limits.

### `visualize.py`
Post-generation visual analysis toolkit manipulating finalized datasets natively. (Requires Pandas + Matplotlib). Discussed further within the [Visualizations guide](./visualizations.md).
