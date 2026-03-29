# Calculations

This document explains the calculation model used by the current implementation.

## 1. Astronomical Foundation

The project uses Swiss Ephemeris through the `pyswisseph` package.

That gives us:

- accurate Sun and Moon positions
- ayanamsa-aware sidereal longitudes
- sunrise and sunset calculations
- moonrise and moonset calculations

The app does not invent planetary positions on its own. It uses Swiss Ephemeris as the underlying astronomy engine and applies Panchang logic on top of those values.

## 2. Time Model

Most astronomy functions work with Julian Day Number (`JD`), so the project must convert civil times into Julian Days and convert the results back into local clock times.

### Core helpers

Important helpers in `astronomy.py`:

- `get_julian_date()`
- `local_time_to_jd()`
- `zoned_datetime_to_jd()`
- `local_date_anchor_jd()`
- `jd_to_local_time_string()`
- `jd_to_zoned_datetime()`

### Why this matters

Panchang logic is extremely sensitive to timing. Even a small shift in the reference instant can change:

- the Tithi index
- the Nakshatra index
- end times for Tithi and Nakshatra

## 3. Ayanamsa and Sidereal Positions

The system supports these ayanamsas:

- Lahiri
- Raman
- Krishnamurti

At calculation time:

1. the sidereal mode is set in Swiss Ephemeris
2. the requested planet is computed using sidereal flags
3. the longitude is normalized into `[0, 360)`

For Rahu and Ketu:

- Rahu is based on the true lunar node
- Ketu is computed as `(Rahu + 180) % 360`

## 4. Panchang Formulas

The five Panchang elements are derived from Sun and Moon longitudes.

### Tithi

Tithi is determined by the angular separation between the Moon and the Sun.

```text
Difference = (Moon_Lon - Sun_Lon) % 360
Tithi_Index = floor(Difference / 12) + 1
```

There are 30 Tithis:

- 15 in the Shukla paksha
- 15 in the Krishna paksha

### Nakshatra

The zodiac is divided into 27 equal Nakshatras.

```text
Nakshatra_Index = floor(Moon_Lon / (360 / 27)) + 1
```

### Nakshatra Pada

Each Nakshatra is divided into 4 padas.

```text
Pada_Index = floor(Moon_Lon / ((360 / 27) / 4)) % 4 + 1
```

### Yoga

Yoga is based on the sum of Sun and Moon longitudes.

```text
Sum = (Sun_Lon + Moon_Lon) % 360
Yoga_Index = floor(Sum / (360 / 27)) + 1
```

### Karana

Karana is half a Tithi.

```text
Difference = (Moon_Lon - Sun_Lon) % 360
Karana_Index = floor(Difference / 6) + 1
```

The project maps Karana positions through the classical movable/fixed Karana cycle.

### Vara

Vara is derived from Julian Day.

```text
Vara_Index = (floor(JD + 0.5) + 1) % 7
```

## 5. End-Time Search

The app does not just label the current Tithi and Nakshatra. It also estimates when they end.

This is handled by:

- `get_tithi_at_jd()`
- `get_nakshatra_at_jd()`
- `_find_exact_end_time()`

### How the search works

1. determine the current index at the reference JD
2. choose a low and high guess for when the index will change
3. expand the search window if the change is not yet bracketed
4. apply repeated bisection until the boundary is tightly located

This gives end times precise enough for application display purposes.

## 6. Rise and Set Calculations

Sunrise, sunset, moonrise, and moonset are calculated with Swiss Ephemeris rise/set functionality.

Important behaviors:

- calculations are location-dependent
- the event search starts from the provided JD anchor
- atmospheric parameters are passed to Swiss Ephemeris
- a fallback call is attempted if the preferred rise/set call fails

For the daily web flow, sunrise and sunset are especially important because they define the reference frame for the daily Panchang label.

## 7. Daily Rule Handling in the Current App

The current implementation uses a sunrise-bound daily model.

That means:

- sunrise is computed for the requested local civil date and location
- Sun and Moon longitudes are sampled at sunrise
- Tithi, Nakshatra, Yoga, Karana, and Vara are derived from that sunrise instant

The response also exposes:

- a legacy special reference
- comparison snapshots for `+2h24m`
- comparison snapshots for `+2h45m`

These snapshots are included for inspection and comparison. They do not override the primary daily label.

## 8. Validation Around Sunrise

Because the whole daily model depends on sunrise being correct, the service validates that:

- sunrise exists
- sunset exists
- next sunrise exists
- sunrise resolves to the requested local civil date
- sunset occurs after sunrise

If these checks fail, the service returns an error instead of a misleading Panchang payload.

## 9. Export Calculation Model

The export paths reuse the core Panchang logic but shape the outputs differently.

### Year-range exports

These use the existing batch-generation engine in `main.py`:

- compute a JD reference per day
- compute planetary longitudes
- compute Panchang fields
- compute sunrise/sunset/moonrise/moonset
- flatten results with `format_row_data()`
- export through `export.py`

### PDF exports

The PDF exporter computes daily sunrise-based Panchang values per day and renders them month by month into a printable layout.

## 10. Important Scope Note

This project currently calculates a sunrise-based Panchang and exposes comparison snapshots for alternative offset inspection.

It does not yet claim to fully encode every Jain sect-specific or Agamic calendrical rule. If such rules are finalized later, the most likely place for those changes will be:

- `panchang_service.py` for daily orchestration
- tests in `tests/test_panchang_rules.py`
- documentation in this file
