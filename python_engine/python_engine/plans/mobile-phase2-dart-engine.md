# Phase 2 — Dart engine core (parity layers L1–L3)

**Parent plan:** [`mobile-app-flutter.md`](mobile-app-flutter.md) §3–4
**Inputs:**
- Phase 0 spike: [`mobile/spikes/astro_accuracy/REPORT.md`](../../../mobile/spikes/astro_accuracy/REPORT.md)
- Phase 1 fixtures: [`mobile-phase1-fixtures.md`](mobile-phase1-fixtures.md)

**Status:** Approved 2026-10-21. M1 complete; M2 next.

## Progress

### M1 done (2026-10-21)

Covers time, Sun and sunrise/sunset. The Moon moved to M2, where tithi times can tune its truncation.

**Results, against Swiss Ephemeris on every day 2016–2040 (`astro.json.gz`):**
- ΔT < 0.01 s; nutation < 0.01″; Sun longitude, RA and Dec < 0.5″; GAST < 2 ms.
- Sunrise, sunset and next sunrise: every core day, 17 locations × 2 rules, worst **0.036 s**. The test guards 0.1 s; the plan allows 10 s.

**Findings:**
- **Sidereal time must be IAU 2006** (Earth Rotation Angle + polynomial). The Meeus/IAU 1982 formula was 6.5 ms off.
- **The traditional sunrise is topocentric.** Swiss Ephemeris puts the disc centre at 0° *topocentric*, i.e. +8.794″ parallax in geocentric altitude. Without it the error is 0.7–1.25 s (worse at high latitude); with it, 0.017 s.
- **The modern refraction constant** (33.447′, measured in the spike) already absorbs the parallax.
- **Sunrise search:** an hour-angle estimate, a ±1 h bracket, then the Illinois method, with an hourly scan as fallback. About 9 Sun evaluations instead of about 34.

**New supporting files:**
- `astro.json.gz`: Swiss Ephemeris positions per day.
- `delta_t_table.py` → `lib/src/time/delta_t_table.g.dart`, with a freshness test.
- `tool/vendor_persis.py`: copies VSOP87D and IAU 2000B *coefficients only* (MIT notice).

**Fixtures:** schema v2 adds `month_amanta` (open question 1 resolved: keep the toggle).

**Follow-up for M4:** the full parity run takes about 3 min under the JIT. The cost is mostly sunrise calls (3 per day), each recomputing nutation several times; cache per instant.

## Goal

`mobile/packages/panchang_engine` is a pure-Dart package with no Flutter dependency. It reproduces every field of the Phase 1 day rows for any location, within the §3 tolerances, verified against `test/fixtures/core/`. Festivals (L4) are Phase 5 and out of scope here.

## Public API (the only surface the app sees)

```dart
final engine = PanchangEngine();
final day = engine.day(
  location: Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
  date: CivilDate(2026, 10, 21),
  sunriseRule: SunriseRule.modern,          // or .traditional
);
// day.sunrise, day.sunset, day.nextSunrise   (UTC instants)
// day.tithis       [(index, endsAt?)]
// day.jainTithi    (index, endsAt?, reference)
// day.nakshatra    (index, endsAt?)
// day.vara, day.month (index, name, isAdhika), day.vikramSamvat, day.viraNirvanaSamvat
// day.choghadiya   16 slots (name, start, end)
```

- All values are immutable (`freezed` or hand-written `final` classes).
- **Time zones:** the engine takes the time zone as an input. Looking it up from coordinates is an app concern (Phase 4); the core fixtures already carry it.

## Layers and the Python they port

| # | Dart module | Ports | Verified by |
|---|---|---|---|
| 1 | `time/` | Julian Day ⇄ UTC, civil-day anchor (`local_date_anchor_jd`), **ΔT table** | unit and property tests |
| 2 | `astro/sun.dart`, `astro/moon.dart` | VSOP87D Sun and ELP/MPP02 Moon (vendored, see below), nutation | spike tolerances (Sun ≤ 5″, Moon ≤ 15″) |
| 3 | `astro/sidereal.dart` | Lahiri ayanamsa; `FLG_SIDEREAL` = tropical apparent − Δψ − ayanamsa | ≤ 1″ |
| 4 | `astro/rise_set.dart` | `get_sunrise` / `get_sunset`, both rules | fixture sunrise/sunset ≤ 10 s |
| 5 | `panchang/elements.dart` | `get_tithi`, `get_nakshatra`, end-time solver | fixture `ends` ≤ 60 s |
| 6 | `panchang/day.dart` | the tithi list per day, Jain tithi (sunrise + 2h24m), vara | fixture indices exact |
| 7 | `calendar/month.dart` | `find_new_moon_*`, `get_hindu_month` (Amanta), `get_purnimanta_month` | fixture month exact |
| 8 | `calendar/samvat.dart` | `find_chaitra_shukla_1`, Diwali, `get_vikram_samvat`, `get_vira_nirvana_samvat` | fixture samvats exact |
| 9 | `panchang/choghadiya.dart` | `choghadiya_service` tables | fixture names exact |

Each layer is built TDD: unit tests first, then its parity test against the core fixtures. A layer starts only when the one below it is green.

## Parity test harness

`test/parity/` loads `fixtures/core/manifest.json`, then every `days.json.gz`, and compares field by field.
- **Times:** absolute tolerance (§3).
- **Labels:** exact, *except* the §3 boundary rule. If Python's transition lies within tolerance of the reference instant, the case goes into `boundary_cases.json` (written by the test run) instead of failing.
- **Schema:** the harness refuses a fixture set whose `schema_version` differs.

## Technical decisions

| Topic | Decision | Why |
|---|---|---|
| Ephemeris code | **Vendor** the VSOP87D and ELP/MPP02 parts of `persis_times` into `lib/src/astro/` with its MIT notice; no package dependency | Single-maintainer package (spike finding). We need about 5% of it and must change it anyway (truncation). |
| Moon series size | Truncate ELP/MPP02 terms by amplitude. Pick the threshold by measurement: keep every term needed for ≤ 1″ worst-case difference from the full series over 2016–2040 | Speed (0.43 ms per call) and app size (about 8 MB of source) |
| ΔT | A yearly ΔT table exported from Swiss Ephemeris (`swe.deltat`), 2015–2041, linearly interpolated | Same time scale as the reference. The persis model added up to 12 s of tithi error. |
| Solver | Bracket with a cheap Moon, refine with the full one; Newton with a bisection fallback | Cuts full-Moon evaluations per end-time solve |
| Sunrise | Computed once per day, reused everywhere | The Python engine computes it twice (about 1 s apart); one is enough |
| Performance budget | Today screen < 100 ms; 31-day month < 1 s, on a mid-range phone in release mode, computed in a background isolate | Measured on the emulator and on the physical phone at the end of the phase |
| Lints | `package:lints/recommended` + `strict-casts`, `strict-inference`, `strict-raw-types` | Catch dynamic-JSON mistakes at compile time |

## Out of scope (later phases)

- Festivals (Phase 5)
- Time-zone lookup from coordinates, and the UI (Phase 4)
- Amanta display: see open question 1

## Open questions

1. **Amanta setting:** the beta Settings screen in the parent plan offers Purnimanta/Amanta, but the fixtures only cover Purnimanta, the engine's default. Either add Amanta month fixtures (re-run the core set, about 1 h) or drop the toggle from the beta.

## Milestones

1. **M1:** time + Sun/Moon + sidereal + rise/set. Parity: sunrise and sunset for all 17 core locations.
2. **M2:** elements and the day row. Parity: tithi, Jain tithi and nakshatra (indices and end times).
3. **M3:** month and samvats. Parity: month, Adhik, VS and VNS.
4. **M4:** choghadiya, the `PanchangEngine.day` façade, and the performance budget measured on the emulator and the phone.
