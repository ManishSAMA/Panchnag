# Panchak Kaal Implementation Plan

**Date:** 2026-06-02  
**Status:** In Progress

## Core Concept

Panchak = Moon sidereal longitude in [300°, 360°). Covers:
- Dhanishtha last 2 padas (300°–306.67°)
- Shatabhisha (306.67°–320°)
- Purva Bhadrapada (320°–333.33°)
- Uttara Bhadrapada (333.33°–346.67°)
- Revati (346.67°–360°)

A day has Panchak if this zone overlaps sunrise → next sunrise.

## Increments

### 1. Core Engine (`panchang.py`) + Tests
- RED: write `tests/test_panchak.py` (boundary, overlap, clipping, nakshatra, next_period)
- GREEN: add `calculate_panchak_kaal(sunrise_jd, next_sunrise_jd, ayanamsa)` → dict:
  - `windows`: list of overlap segments (0 or 1 per day)
    - `start_jd`, `end_jd`, `nakshatra`, `clipped_start`, `clipped_end`
  - `period`: `{entry_jd, exit_jd}` — full Panchak containing the window (None if no window)
  - `next_period`: `{entry_jd, exit_jd}` — next Panchak (None if window exists)
- Helpers:
  - `_find_lon_crossing_jd(lo_jd, hi_jd, target_lon, ayanamsa)` — binary search (handles 360°→0° wraparound)
  - `_find_next_panchak_period(from_jd, ayanamsa)` — search forward for next entry at 300°

### 2. Service Layer
- `panchang_service.py`: serialize `panchak_kaal` as top-level key with `has_window`, `is_active`, `windows[]`, `period`, `next_period`
- `app.py` month-overview: add `has_panchak` bool to each day_payload

### 3. Exports
- `export.py`: add `Has_Panchak` and `Panchak_Window` columns to `format_row_data()`
- `main.py`: import + call `calculate_panchak_kaal`, pass to `format_row_data()`, store raw segments in `row["Panchak_Segments"]`
- `export_pdf.py`: add compact "Panchak Kaal" column (time range or "None")

### 4. Frontend (app.js + app.css)
- Panchak card after Bhadra card in panchang page `_render()`
- `#panchak?date=YYYY-MM-DD` page (registerPage):
  - prev/next arrows, 7-tab date strip
  - active/inactive status with timing
  - complete period timing
  - active-now badge
  - nakshatra at overlap start
  - next-period preview on inactive days
  - expandable "What is Panchak?" section
- Clickable Panchak row at bottom of panchang table (opens `#panchak?date=`)
- Calendar badge on days with panchak (tap → panchak page, cell tap → panchang page)

## Key Decisions
- Binary search converges to < 1 minute accuracy (0.0007 JD delta)
- `_find_next_panchak_period` scans up to 30 days forward in 6-hour steps
- Moon in panchak zone checked via `300.0 <= lon < 360.0` after getting sidereal longitude
- No weekday-type classification (out of scope)
