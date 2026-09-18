# Sankranti Ingress Time — Design Spec

**Date:** 2026-04-18  
**Status:** Approved

---

## Context

Sun Rashi is already calculated and displayed across all outputs. On the day the Sun
crosses a 30° sidereal boundary (Sankranti), the current display simply changes the
Rashi name with no additional information. Users want to know:

1. That today is the final day of the outgoing Rashi (end marker)
2. The exact local time the Sun enters the new Rashi (ingress time)

Both are shown only on the Sankranti day itself. The ingress time must be computed
astronomically via Swiss Ephemeris bisection — never estimated or hardcoded.

---

## Architecture

Two-layer design to separate astronomy from timezone formatting:

### Layer 1 — Astronomical (timezone-agnostic)

**`_find_sankranti_crossing_jd(day_start_jd, day_end_jd)`** in `astronomy.py`

- Computes sidereal Sun longitude (Lahiri, always) at `day_start_jd` and `day_end_jd`
- Detects whether any 30° boundary is crossed in that interval
- Handles the 0°/360° wrap (Meena→Mesh, i.e., Mesha Sankranti)
- Bisects 50 iterations (~microsecond precision) to find crossing JD
- Returns `(crossing_jd: float | None, from_rashi: str | None, to_rashi: str | None)`
- Uses `SUN_RASHI_NAMES` — same short-form list as `get_sun_rashi` (e.g. "Mesh", "Vrishabh")

**Bisection detail:**
1. `lon_start = sidereal_sun_lon_lahiri(day_start_jd)`, same for `lon_end`
2. Detect wrap: if `lon_end < lon_start - 1`, the Sun crossed 0° (only Meena→Mesh case)
3. For each multiple of 30° in `[0, 330]`: check if it falls in `(lon_start, lon_end]`
   (for wrap, check if 0° falls in the interval using adjusted values)
4. Bisect between `day_start_jd` and `day_end_jd` with `f(jd) = lon(jd) - target`
   (wrap case: use `lon - 360` when `lon > 180` so f is monotonic through 0)

### Layer 2 — High-level (timezone-aware)

**`get_sankranti_moment(local_date: date, tz_name: str) -> dict`** in `astronomy.py`

- Computes `day_start_jd` and `day_end_jd` via `local_date_anchor_jd` (ZoneInfo)
- Calls Layer 1
- Converts `crossing_jd` to `"HH:MM"` local time via `jd_to_zoned_datetime`
- Returns:

```python
{
    "occurs_today": bool,
    "ingress_time": "HH:MM" | None,   # local time, 24-hour format
    "from_rashi": str | None,          # e.g. "Meen"
    "to_rashi": str | None,            # e.g. "Mesh"
}
```

---

## Changes by File

### `astronomy.py`

- Add `_find_sankranti_crossing_jd(day_start_jd, day_end_jd)` (internal helper)
- Add `get_sankranti_moment(local_date, tz_name)` (public API)
- Export `get_sankranti_moment` (it is imported by other modules)

### `panchang_service.py`

In `generate_location_panchang()`:

- Call `get_sankranti_moment(local_date, location.timezone)`
- Add to `panchang` section:

```json
"sun_rashi_transition": {
    "from_rashi": "Meen",
    "to_rashi": "Mesh",
    "ingress_time": "14:03",
    "is_rashi_end_day": true
}
```

- On non-Sankranti days: `"sun_rashi_transition": null`
- Import `get_sankranti_moment` at top of file

### `export.py` — `format_row_data()`

- Add optional param: `sun_rashi_transition: dict | None = None`
- After the existing `Sun_Rashi` column, add:
  - `row['Rashi Ends'] = "Yes" if transition occurs else ""`
  - `row['Sankranti Time'] = transition["ingress_time"] if transition occurs else ""`

### `main.py`

- Add `tz_name` to worker config dict `_G` (resolved from lat/lon via `TimezoneFinder`
  in `range_generation_service.py`, then passed through `run_generation`)
- In `_compute_day`: call `get_sankranti_moment(civil_date, tz_name)` and pass result
  to `format_row_data(..., sun_rashi_transition=...)`
- For standalone CLI path (no `range_generation_service`): resolve tz_name from lat/lon
  using `TimezoneFinder` (already a dependency via `location_service.py`)

### `range_generation_service.py`

- Add `"tz_name": location.timezone` to the `config` dict passed to `run_generation`

### `export_pdf.py`

- Add `tz_name: str | None = None` to `generate_pdf_calendar` signature
- When building `all_rows`: for each day, call `get_sankranti_moment(civil_date, tz_name)`
  and store result in row as `row["Sankranti"]`
- Replace the existing `Sun_Rashi_Display` post-processing loop (lines 100–106):
  - On Sankranti day: `Sun_Rashi_Display = f"{curr_rashi}\n{ingress_time}"`
    rendered as `Paragraph(f"{curr_rashi}<br/><font size='6'>{ingress_time}</font>", ...)`
  - On non-Sankranti day: `Sun_Rashi_Display = curr_rashi` (unchanged)
- If `tz_name` is None, fall back to deriving it from lat/lon via `TimezoneFinder`

---

## Return Value Naming

`from_rashi` / `to_rashi` use the same `SUN_RASHI_NAMES` short form as the existing
`sun_rashi` field: `["Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya", "Tula",
"Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"]`.

The spec example used "Vrishabha" — this was a typo; implementation uses "Vrishabh".

---

## Tests — New File: `tests/test_sankranti_moment.py`

| Date       | from_rashi | to_rashi  | Approx ingress (IST) |
|------------|------------|-----------|----------------------|
| 2025-04-14 | Meen       | Mesh      | ~14:00               |
| 2025-05-15 | Mesh       | Vrishabh  | verify vs drikpanchang |
| 2025-01-14 | Dhanu      | Makar     | ~20:00               |

For each Sankranti date:
- Assert `occurs_today` is `True`
- Assert `occurs_today` is `False` on day before and day after
- Assert `from_rashi` and `to_rashi` are correct
- Assert `ingress_time` is within ±5 minutes of published value (use known IST values)

Also:
- Assert non-Sankranti day (e.g. 2025-06-01): `occurs_today=False`, `ingress_time=None`

---

## Constraints

- Always Lahiri ayanamsa for this calculation — ignores user ayanamsa setting
- No new pip dependencies — `timezonefinder` already installed
- No changes to Tithi, Nakshatra, Yoga, Karana, Vara, Samvat, or month logic
- All existing tests must continue to pass
- Column positions: `Rashi Ends` and `Sankranti Time` inserted immediately after `Sun_Rashi`
- PDF: no arrows, no "ends/starts" labels — just Rashi name + time on two lines

---

## Verification

1. Run `python -m pytest tests/test_sankranti_moment.py -v` — all new tests pass
2. Run `python -m pytest tests/ -v` — all existing tests still pass
3. Generate one-day JSON for 2025-04-14 → confirm `sun_rashi_transition` present with
   correct values; confirm it's `null` on 2025-04-13
4. Generate CSV for April 2025 → confirm `Rashi Ends`/`Sankranti Time` columns appear
   on row 14 only
5. Generate PDF for 2025 → confirm Sun Rashi cell on April 14 shows "Mesh" + time on
   two lines; no arrows anywhere
