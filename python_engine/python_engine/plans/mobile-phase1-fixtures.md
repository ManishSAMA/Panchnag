# Phase 1 — Parity fixture exporter

**Parent plan:** [`mobile-app-flutter.md`](mobile-app-flutter.md) §3–4
**Status:** In progress (2026-10-21), branch `feat/mobile-phase0`

The Python engine becomes the reference for the Dart engine. This phase builds
the exporter that writes down what the reference says, for any location.

## Decisions

| Topic | Decision |
|---|---|
| Sunrise rules | Both `modern` and `traditional`. Every fixture file is per rule. |
| Clock | Not a fixture axis. Fixtures store UTC Julian Days, and `clock` only changes how times are displayed. |
| Locations | Any location (`--lat/--lon/--name`), plus a default set of 13 fixed locations and a **seeded random sample**. |
| Storage | A **core set** is committed (for CI without Python). The full set is generated locally and gitignored. |
| Source of truth | The engine's public service functions (`generate_location_panchang`, `calculate_choghadiya_slots`, `generate_jain_festivals`), so fixtures reflect what users see. |
| Coordinates | Always explicit lat/lon, never `city=`. A city name goes through geocoding, which is not deterministic offline. |

## Locations

**Fixed (13):**
- Delhi, Ahmedabad, Mumbai, Surat, Palitana, Jaipur, Udaipur, Indore, Kolkata, Bengaluru, Chennai
- London (high latitude, daylight saving time)
- New York (western hemisphere, DST)

**Random:** seeded, `--random N --seed S`. Half are drawn inside India's bounding box (lat 8–35, lon 68–97) and half worldwide with |lat| ≤ 60°, so every day has a sunrise. The time zone comes from `get_timezone_name`; ocean points give `Etc/GMT±n`, which is valid.

## Output layout

```
mobile/packages/panchang_engine/test/fixtures/
  core/                         # committed
  full/                         # gitignored, local only
    manifest.json               # locations, range, rules, schema_version, swe version
    <slug>/<rule>/days.json.gz
    <slug>/<rule>/festivals.<profile>.json.gz
```

**Determinism:**
- No wall-clock timestamps in the output.
- gzip `mtime=0` and sorted keys, so re-running an unchanged engine gives byte-identical files.

### Day row (one per civil date)

| Field | Source |
|---|---|
| `date` | civil date (ISO) |
| `sunrise`, `sunset`, `next_sunrise` | `events.*.jd` |
| `tithi` | `[{index, ends}]` for every tithi touching the day; `ends` is null for the last one |
| `jain_tithi` | `{index, ends, reference}` (sunrise + 2h24m) |
| `nakshatra` | `{index, ends}` |
| `vara` | weekday index |
| `month` | `{index, name, is_adhika}` (Purnimanta, the engine default) |
| `vikram_samvat`, `vira_nirvana_samvat` | integers |
| `choghadiya` | the 16 slot names in order, from `calculate_choghadiya_slots`. Slot times are just sunrise→sunset and sunset→next sunrise each split into 8 equal parts, so they are derived rather than stored. |

Paksha, Kshaya and Vriddhi are **derived** from these fields (on both sides) rather than stored, so the fixtures don't store the same thing twice.

### Festival file (per profile, per year in range)

The file is `{years: {"2026": [{id, occurrence_id, start_date, end_date, status}, …]}}`, sorted by (start_date, occurrence_id), taken from `generate_jain_festivals(year, lat, lon, profile=…, sunrise_rule=…)`.
- The engine already limits each call to its own year, so years never overlap.
- Names and descriptions come from the shared registry JSON rather than being copied into every fixture.
- `multi_day_festivals` is a display grouping, so it is left out.
- **The engine silently accepts an unknown profile.** The exporter therefore checks profiles against `request_parsing.VALID_PROFILES`.
- **The sunrise rule really does move festivals.** For example, in Delhi 2026 one Rohini Vrat moves from 11 to 12 July under the traditional rule.

## Sets

| Set | Locations | Years | Rules | Est. time (14 workers) |
|---|---|---|---|---|
| core (committed) | Delhi, Ahmedabad, Mumbai (full range); all 13 + 4 random (2026–2027) | 2016–2040 / 2026–2027 | both | ~8 min |
| full (local) | 13 fixed + 8 random | 2016–2040 | both | ~50 min |

## Also in this phase

`shared/festival_registry.json` (repo root) is generated from `jain_observances.registry.FESTIVAL_REGISTRY`, with a freshness test. Dart loads it as an asset in Phase 5.

## Increments (TDD, each one green before the next)

1. Location set: fixed defaults, custom location, seeded random sample.
2. Day row: built from the engine for one location and date; invariants hold; row equals the engine payload.
3. Writer: deterministic gzip and manifest; every date in the range exactly once, in order.
4. Festival rows per profile and year.
5. CLI and parallel runner; `--set core|full`.
6. Registry JSON and freshness test.
7. Generate the core set and commit it.

## Noticed along the way (not fixed here)

On 2026-10-21 for Delhi, `reference_time` (sunrise used for the panchang) and `events.sunrise` differ by about 1 s. They are two separate sunrise computations. This is harmless at the 60 s tolerance, but the Dart port should compute sunrise once.
