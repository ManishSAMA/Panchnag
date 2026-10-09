# Phase 0 accuracy spike — result: **GO**

**Date:** 2026-10-07
**Question:** Can a pure-Dart, permissively licensed astronomy engine match the
Python engine (Swiss Ephemeris) closely enough for the parity tolerances in
[`plans/mobile-app-flutter.md`](../../../python_engine/python_engine/plans/mobile-app-flutter.md) §3?
**Answer:** Yes, by 10–300× margins on every check.

## Setup

- **Candidate:** [`persis_times`](https://pub.dev/packages/persis_times) 1.0.45 (MIT): VSOP87D Sun, full ELP/MPP02 Moon, IAU nutation.
- **Reference:** `python_engine` via pyswisseph 2.10.03. No `.se1` files are on its path, so it runs in **Moshier** mode (`retflag` = `FLG_MOSEPH`).
- **Coverage:** 2016-01-01 → 2040-12-31.
  - 18,264 position samples (00h and 12h UT daily)
  - 9,277 tithi, 9,025 nakshatra and 300 sankranti transitions
  - Sunrise and sunset every day for Delhi, Ahmedabad, Kolkata, London and New York (45,660 city-days)
- **To reproduce:** run `tool/dump_reference.py` (python_engine venv), then `dart compile exe bin/astro_accuracy.dart -o build/spike.exe` and `build\spike.exe`.

## Results vs. plan tolerances

| Layer | Quantity | Max error | Tolerance | Margin |
|---|---|---:|---:|---:|
| L1 | Sun apparent longitude | 0.16″ | 5″ | 30× |
| L1 | Moon apparent longitude | 3.2″ (p99 1.8″) | 15″ | 5× |
| L1 | Lahiri ayanamsa (precession model) | 0.13″ (constant offset) | 1″ | 8× |
| L1 | Sunrise / sunset, all 5 cities | 0.03 s | 10 s | 300× |
| L2 | Tithi transition instants | 6.0 s (p99 3.5 s) | 60 s | 10× |
| L2 | Nakshatra transition instants | 5.6 s | 60 s | 10× |
| L2 | Sankranti instants | 3.6 s | 60 s | 17× |

Most of the Moon residual is probably Moshier's own few-arcsecond Moon error rather than ELP/MPP02's. The Python bisection also only resolves to about 0.9 s.

## Findings that shape Phase 2

1. **Swiss Ephemeris's sidereal longitude is tropical apparent − Δψ − ayanamsa.**
   - The `FLG_SIDEREAL` positions used by `get_planetary_longitude` leave out nutation in longitude. The Dart engine reproduces this to 0.000″.
   - `astronomy._sidereal_sun_lon_lahiri` uses a different definition (it keeps Δψ, up to about 17″, which is about 7 min of Sankranti time). It is **not called by production code**, so this is not a live bug. The Dart port must follow `FLG_SIDEREAL`.
2. **Tithi doesn't depend on the ayanamsa:** it uses Moon − Sun, so the ayanamsa cancels. Only nakshatra and Sankranti/month need it.
3. **Swiss Ephemeris sunrise uses a fixed horizon** of −(33.447′ refraction + the Sun's semidiameter that day).
   - One constant fits all 45,660 city-days to within 0.19″. That's why sunrise matches to hundredths of a second.
   - The constant comes from `rise_trans` with 1013.25 hPa and 15 °C, the values `astronomy._rise_set` passes.
4. **ΔT matters more than the theory does.**
   - With persis's built-in ΔT model, tithi error grows to 12 s (still within tolerance).
   - Phase 2 should use a ΔT table matching Swiss Ephemeris's, so the two engines share one definition of "now".
5. **Ayanamsa:** an IAU-2006 precession formula with the Swiss Ephemeris Lahiri epoch is within 0.13″, a constant that can be calibrated away. A cubic fit is exact inside 2016–2040 but shouldn't be used outside it. Prefer the formula.

## Risks found

| Risk | Detail | Mitigation (Phase 2) |
|---|---|---|
| **Speed** | Moon longitude 0.43 ms and a tithi end-time solve 3.5 ms on this PC (AOT). Phones are about 3–10× slower, so a 30-day month view could take 1–3 s. | Truncate tiny ELP terms (the 38k-term series is far beyond what we need); use a cheap Moon for bracketing and the full one only for the final refinement; compute in a background isolate and cache by month. |
| **App size** | The ELP/MPP02 tables are about 8 MB of Dart source. | Truncation fixes this too. Measure the release APK size at Phase 3. |
| **Dependency** | Single-maintainer package with little adoption. | MIT allows vendoring: copy the needed series into `panchang_engine` with attribution, and drop the dependency. |

## Decision

**GO** for the pure-Dart engine. The open items move into Phase 2: ΔT table, term truncation, isolate/caching, and vendoring persis_times.
