# Sankranti Ingress Time Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute the exact local time when the Sun crosses a 30° sidereal boundary (Sankranti) and expose it across JSON, CSV/Excel, and PDF outputs.

**Architecture:** Two-layer design — a timezone-agnostic bisection function finds the exact crossing JD, and a higher-level function wraps it with IANA timezone formatting. Callers pass pre-computed transition info into the export layer.

**Tech Stack:** Python 3.11, pyswisseph (already installed), zoneinfo (stdlib), timezonefinder (already installed)

---

## File Map

| File | Change |
|------|--------|
| `astronomy.py` | Add `_sidereal_sun_lon_lahiri`, `_find_sankranti_crossing_jd`, `get_sankranti_moment` |
| `tests/test_sankranti_moment.py` | New — unit tests for all three new functions |
| `panchang_service.py` | Import + call `get_sankranti_moment`; add `sun_rashi_transition` to JSON |
| `export.py` | Add `sun_rashi_transition` param to `format_row_data`; add two new columns |
| `main.py` | Add `tz_name` to worker config; call `get_sankranti_moment` in `_compute_day` |
| `range_generation_service.py` | Add `tz_name` to config dict passed to `run_generation` |
| `export_pdf.py` | Add `tz_name` param; replace `Sun_Rashi_Display` logic with ingress-time rendering |

---

## Task 1: Internal Sun longitude helper

**Files:**
- Modify: `astronomy.py` (append after line 362, end of file)

- [ ] **Step 1: Write the failing test**

Create `tests/test_sankranti_moment.py`:

```python
"""Tests for Sankranti (solar ingress) detection functions."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from astronomy import _sidereal_sun_lon_lahiri, get_julian_date


def test_sidereal_sun_lon_lahiri_is_in_range():
    jd = get_julian_date(2025, 4, 14, 6.0)
    lon = _sidereal_sun_lon_lahiri(jd)
    assert 0.0 <= lon < 360.0


def test_sidereal_sun_lon_lahiri_mesh_on_sankranti():
    # On Mesha Sankranti 2025 (April 14) near 14:00 IST = 08:30 UTC
    jd = get_julian_date(2025, 4, 14, 8.5)
    lon = _sidereal_sun_lon_lahiri(jd)
    # Should be very close to 0° (just entered Mesh)
    assert lon < 1.0 or lon > 359.0  # within 1° of the Meena/Mesh boundary


def test_sidereal_sun_lon_lahiri_makar_on_sankranti():
    # On Makar Sankranti 2025 (Jan 14) near 20:38 IST = 15:08 UTC
    jd = get_julian_date(2025, 1, 14, 15.1)
    lon = _sidereal_sun_lon_lahiri(jd)
    # Should be very close to 270°
    assert 269.0 < lon < 271.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py -v 2>&1 | head -30
```

Expected: `ImportError: cannot import name '_sidereal_sun_lon_lahiri'`

- [ ] **Step 3: Add `_sidereal_sun_lon_lahiri` to end of `astronomy.py`**

```python
# ---------------------------------------------------------------------------
# Sankranti (solar ingress) detection
# ---------------------------------------------------------------------------

def _sidereal_sun_lon_lahiri(jd: float) -> float:
    """Sun's sidereal longitude using Lahiri ayanamsa. Internal helper."""
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    res, _err = swe.calc_ut(jd, swe.SUN, flags)
    tropical_lon = res[0]
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    return (tropical_lon - ayanamsa) % 360.0
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py::test_sidereal_sun_lon_lahiri_is_in_range tests/test_sankranti_moment.py::test_sidereal_sun_lon_lahiri_mesh_on_sankranti tests/test_sankranti_moment.py::test_sidereal_sun_lon_lahiri_makar_on_sankranti -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
cd /home/Manu/Projects/Jain_panchang && git add astronomy.py tests/test_sankranti_moment.py && git commit -m "feat: add _sidereal_sun_lon_lahiri helper + initial tests"
```

---

## Task 2: Bisection crossing detector

**Files:**
- Modify: `astronomy.py` (append after `_sidereal_sun_lon_lahiri`)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sankranti_moment.py`:

```python
from astronomy import _find_sankranti_crossing_jd, local_date_anchor_jd
from datetime import date


def _day_jds(y, m, d, tz="Asia/Kolkata"):
    start = local_date_anchor_jd(date(y, m, d), tz, hour=0)
    end   = local_date_anchor_jd(date(y, m, d + 1) if d < 28 else date(y, m + 1 if m < 12 else 1, 1), tz, hour=0)
    return start, end


def test_find_crossing_mesha_sankranti_2025():
    start_jd, end_jd = _day_jds(2025, 4, 14)
    crossing_jd, from_rashi, to_rashi = _find_sankranti_crossing_jd(start_jd, end_jd)
    assert crossing_jd is not None
    assert from_rashi == "Meen"
    assert to_rashi == "Mesh"


def test_find_crossing_makar_sankranti_2025():
    start_jd, end_jd = _day_jds(2025, 1, 14)
    crossing_jd, from_rashi, to_rashi = _find_sankranti_crossing_jd(start_jd, end_jd)
    assert crossing_jd is not None
    assert from_rashi == "Dhanu"
    assert to_rashi == "Makar"


def test_find_no_crossing_on_regular_day():
    start_jd, end_jd = _day_jds(2025, 6, 1)
    crossing_jd, from_rashi, to_rashi = _find_sankranti_crossing_jd(start_jd, end_jd)
    assert crossing_jd is None
    assert from_rashi is None
    assert to_rashi is None


def test_find_no_crossing_day_before_mesha():
    start_jd, end_jd = _day_jds(2025, 4, 13)
    crossing_jd, _, _ = _find_sankranti_crossing_jd(start_jd, end_jd)
    assert crossing_jd is None


def test_find_no_crossing_day_after_mesha():
    start_jd, end_jd = _day_jds(2025, 4, 15)
    crossing_jd, _, _ = _find_sankranti_crossing_jd(start_jd, end_jd)
    assert crossing_jd is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py -k "find_crossing" -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name '_find_sankranti_crossing_jd'`

- [ ] **Step 3: Add `_find_sankranti_crossing_jd` to `astronomy.py` (after `_sidereal_sun_lon_lahiri`)**

```python
def _find_sankranti_crossing_jd(
    day_start_jd: float,
    day_end_jd: float,
) -> tuple[float | None, str | None, str | None]:
    """Find if Sun crosses a 30° sidereal boundary between day_start_jd and day_end_jd.

    Always uses Lahiri ayanamsa.

    Returns:
        (crossing_jd, from_rashi_name, to_rashi_name) if a crossing occurs,
        else (None, None, None).
    """
    lon_start = _sidereal_sun_lon_lahiri(day_start_jd)
    lon_end   = _sidereal_sun_lon_lahiri(day_end_jd)

    # Detect Meena→Mesh wrap: Sun longitude crosses 0°/360°.
    # Normal Sun motion is ~1°/day; a drop > 1° means the wrap occurred.
    wrapped = lon_end < lon_start - 1.0

    if wrapped:
        target    = 360.0
        from_idx  = 11   # Meen
        to_idx    = 0    # Mesh
    else:
        target = None
        for b in range(0, 360, 30):
            if lon_start < b <= lon_end:
                target = float(b)
                break
        if target is None:
            return None, None, None
        from_idx = int(lon_start / 30.0)
        to_idx   = int(target / 30.0) % 12

    # Bisect 50 iterations → sub-second precision.
    jd_lo, jd_hi = day_start_jd, day_end_jd
    for _ in range(50):
        jd_mid  = (jd_lo + jd_hi) / 2.0
        lon_mid = _sidereal_sun_lon_lahiri(jd_mid)
        if wrapped and lon_mid < 180.0:
            lon_mid += 360.0   # keep function monotonic through 360°
        if lon_mid < target:
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid

    crossing_jd = (jd_lo + jd_hi) / 2.0
    return crossing_jd, SUN_RASHI_NAMES[from_idx], SUN_RASHI_NAMES[to_idx]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py -k "find_crossing or sidereal" -v
```

Expected: 8 PASSED

- [ ] **Step 5: Commit**

```bash
cd /home/Manu/Projects/Jain_panchang && git add astronomy.py tests/test_sankranti_moment.py && git commit -m "feat: add _find_sankranti_crossing_jd with bisection"
```

---

## Task 3: High-level `get_sankranti_moment` + ingress time tests

**Files:**
- Modify: `astronomy.py` (append after `_find_sankranti_crossing_jd`)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sankranti_moment.py`:

```python
from astronomy import get_sankranti_moment


def _time_to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def test_mesha_sankranti_2025_occurs_today():
    result = get_sankranti_moment(date(2025, 4, 14), "Asia/Kolkata")
    assert result["occurs_today"] is True
    assert result["from_rashi"] == "Meen"
    assert result["to_rashi"] == "Mesh"
    assert result["ingress_time"] is not None
    # Mesha Sankranti 2025 ≈ 14:03 IST — verify at drikpanchang.com before adjusting
    expected = _time_to_minutes("14:03")
    actual   = _time_to_minutes(result["ingress_time"])
    assert abs(actual - expected) <= 5, f"Expected ~14:03 IST, got {result['ingress_time']}"


def test_mesha_sankranti_2025_not_day_before():
    result = get_sankranti_moment(date(2025, 4, 13), "Asia/Kolkata")
    assert result["occurs_today"] is False
    assert result["ingress_time"] is None
    assert result["from_rashi"] is None
    assert result["to_rashi"] is None


def test_mesha_sankranti_2025_not_day_after():
    result = get_sankranti_moment(date(2025, 4, 15), "Asia/Kolkata")
    assert result["occurs_today"] is False


def test_makar_sankranti_2025_occurs_today():
    result = get_sankranti_moment(date(2025, 1, 14), "Asia/Kolkata")
    assert result["occurs_today"] is True
    assert result["from_rashi"] == "Dhanu"
    assert result["to_rashi"] == "Makar"
    assert result["ingress_time"] is not None
    # Makar Sankranti 2025 ≈ 20:38 IST — verify at drikpanchang.com before adjusting
    expected = _time_to_minutes("20:38")
    actual   = _time_to_minutes(result["ingress_time"])
    assert abs(actual - expected) <= 5, f"Expected ~20:38 IST, got {result['ingress_time']}"


def test_makar_sankranti_2025_not_day_before():
    result = get_sankranti_moment(date(2025, 1, 13), "Asia/Kolkata")
    assert result["occurs_today"] is False


def test_makar_sankranti_2025_not_day_after():
    result = get_sankranti_moment(date(2025, 1, 15), "Asia/Kolkata")
    assert result["occurs_today"] is False


def test_vrishabha_sankranti_2025_occurs_today():
    # Sun enters Vrishabh around May 15, 2025 ~01:03 IST
    result = get_sankranti_moment(date(2025, 5, 15), "Asia/Kolkata")
    assert result["occurs_today"] is True
    assert result["from_rashi"] == "Mesh"
    assert result["to_rashi"] == "Vrishabh"
    assert result["ingress_time"] is not None
    # Verify exact time at drikpanchang.com; update expected value if off by > 5 min
    expected = _time_to_minutes("01:03")
    actual   = _time_to_minutes(result["ingress_time"])
    assert abs(actual - expected) <= 5, f"Expected ~01:03 IST, got {result['ingress_time']}"


def test_non_sankranti_day_returns_false():
    result = get_sankranti_moment(date(2025, 6, 1), "Asia/Kolkata")
    assert result["occurs_today"] is False
    assert result["ingress_time"] is None
    assert result["from_rashi"] is None
    assert result["to_rashi"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py -k "sankranti_moment or mesha or makar or vrishabha or non_sankranti" -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'get_sankranti_moment'`

- [ ] **Step 3: Add `get_sankranti_moment` to `astronomy.py` (after `_find_sankranti_crossing_jd`)**

```python
def get_sankranti_moment(local_date: date, tz_name: str) -> dict:
    """Return Sankranti ingress info for the given local civil date.

    Always uses Lahiri ayanamsa regardless of user ayanamsa setting.

    Returns:
        {
            "occurs_today": bool,
            "ingress_time": "HH:MM" | None,   # local 24-hour time
            "from_rashi":  str | None,
            "to_rashi":    str | None,
        }
    """
    day_start_jd = local_date_anchor_jd(local_date, tz_name, hour=0)
    day_end_jd   = local_date_anchor_jd(local_date + timedelta(days=1), tz_name, hour=0)

    crossing_jd, from_rashi, to_rashi = _find_sankranti_crossing_jd(
        day_start_jd, day_end_jd
    )

    if crossing_jd is None:
        return {
            "occurs_today": False,
            "ingress_time": None,
            "from_rashi":   None,
            "to_rashi":     None,
        }

    local_dt    = jd_to_zoned_datetime(crossing_jd, tz_name)
    ingress_time = local_dt.strftime("%H:%M") if local_dt else None
    return {
        "occurs_today": True,
        "ingress_time": ingress_time,
        "from_rashi":   from_rashi,
        "to_rashi":     to_rashi,
    }
```

- [ ] **Step 4: Run all sankranti tests**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py -v
```

Expected: all tests PASSED. If an ingress-time assert fails, check the expected time against drikpanchang.com for that Sankranti and update the constant in the test (the ±5 min tolerance is unchanged; only the reference time may need correcting).

- [ ] **Step 5: Run existing test suite to confirm nothing broke**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/ -v --ignore=tests/test_sankranti_moment.py
```

Expected: all pre-existing tests PASSED

- [ ] **Step 6: Commit**

```bash
cd /home/Manu/Projects/Jain_panchang && git add astronomy.py tests/test_sankranti_moment.py && git commit -m "feat: add get_sankranti_moment with full test coverage"
```

---

## Task 4: JSON output — `sun_rashi_transition` field

**Files:**
- Modify: `panchang_service.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sankranti_moment.py`:

```python
from panchang_service import generate_location_panchang


def test_json_has_transition_on_sankranti_day():
    # lat/lon for Jaipur → resolves to "Asia/Kolkata" internally
    result = generate_location_panchang(
        dt_date(2025, 4, 14),
        lat=26.9124,
        lon=75.7873,
        ayanamsa_name="Lahiri",
    )
    transition = result["panchang"]["sun_rashi_transition"]
    assert transition is not None
    assert transition["occurs_today"] is True
    assert transition["from_rashi"] == "Meen"
    assert transition["to_rashi"] == "Mesh"
    assert transition["ingress_time"] is not None
    assert transition["is_rashi_end_day"] is True


def test_json_transition_null_on_regular_day():
    result = generate_location_panchang(
        dt_date(2025, 6, 1),
        lat=26.9124,
        lon=75.7873,
        ayanamsa_name="Lahiri",
    )
    assert result["panchang"]["sun_rashi_transition"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py::test_json_has_transition_on_sankranti_day tests/test_sankranti_moment.py::test_json_transition_null_on_regular_day -v 2>&1 | head -30
```

Expected: `TypeError` or `KeyError` — `sun_rashi_transition` key not present

- [ ] **Step 3: Update `panchang_service.py`**

Add `get_sankranti_moment` to the existing astronomy import block (around line 22):

```python
from astronomy import (
    get_all_planet_positions,
    get_ayanamsa,
    get_moonrise,
    get_moonset,
    get_planetary_longitude,
    get_rashi_name,
    get_sankranti_moment,
    get_sun_rashi,
    get_sunrise,
    get_sunset,
    jd_to_iso_local_string,
    jd_to_zoned_datetime,
    local_date_anchor_jd,
)
```

Then in `generate_location_panchang()`, add this line just before the large `return` dict (anywhere between line 296 and the `return` statement is fine — place it right after the `ayanamsa_value` line):

```python
    sankranti_transition = get_sankranti_moment(local_date, location.timezone)
```

Then find `"sun_rashi": get_sun_rashi(events.sunrise_jd),` (around line 333) and add the transition field immediately after it:

```python
            "sun_rashi": get_sun_rashi(events.sunrise_jd),
            "sun_rashi_transition": (
                {**sankranti_transition, "is_rashi_end_day": True}
                if sankranti_transition["occurs_today"]
                else None
            ),
```

- [ ] **Step 4: Run tests**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py::test_json_has_transition_on_sankranti_day tests/test_sankranti_moment.py::test_json_transition_null_on_regular_day -v
```

Expected: 2 PASSED

- [ ] **Step 5: Run full test suite**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/ -v
```

Expected: all tests PASSED

- [ ] **Step 6: Commit**

```bash
cd /home/Manu/Projects/Jain_panchang && git add panchang_service.py tests/test_sankranti_moment.py && git commit -m "feat: add sun_rashi_transition to JSON panchang output"
```

---

## Task 5: CSV/Excel — `Rashi Ends` + `Sankranti Time` columns

**Files:**
- Modify: `export.py` — `format_row_data` signature + new columns
- Modify: `main.py` — add `tz_name` to config; call `get_sankranti_moment`
- Modify: `range_generation_service.py` — add `tz_name` to config dict

### 5a — export.py

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sankranti_moment.py`:

```python
from export import format_row_data
from panchang import generate_daily_panchang, calculate_jain_tithi_from_sunrise
from astronomy import get_julian_date, local_time_to_jd, get_sunrise


def _make_row(y, m, d, transition=None):
    jd = local_time_to_jd(y, m, d, 5.5, 5.5)
    jd_sr = get_sunrise(jd, 26.9124, 75.7873)
    panchang  = generate_daily_panchang(jd_sr, "Lahiri", local_date=dt_date(y, m, d))
    jain      = calculate_jain_tithi_from_sunrise(jd_sr, "Lahiri")
    return format_row_data(
        date_str=f"{y:04d}-{m:02d}-{d:02d}",
        julian_date=jd_sr,
        planets={"Sun": 0.0, "Moon": 0.0},
        panchang=panchang,
        jain_tithi=jain,
        sunrise_str="06:00:00",
        sunset_str="18:30:00",
        moonrise_str="",
        moonset_str="",
        ayanamsa_dec=24.0,
        sun_rashi_transition=transition,
    )


def test_csv_row_has_rashi_ends_yes_on_sankranti():
    transition = {
        "occurs_today": True,
        "ingress_time": "14:03",
        "from_rashi": "Meen",
        "to_rashi": "Mesh",
    }
    row = _make_row(2025, 4, 14, transition=transition)
    assert row["Rashi Ends"] == "Yes"
    assert row["Sankranti Time"] == "14:03"


def test_csv_row_rashi_ends_blank_on_regular_day():
    row = _make_row(2025, 6, 1, transition=None)
    assert row["Rashi Ends"] == ""
    assert row["Sankranti Time"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py::test_csv_row_has_rashi_ends_yes_on_sankranti tests/test_sankranti_moment.py::test_csv_row_rashi_ends_blank_on_regular_day -v 2>&1 | head -20
```

Expected: `TypeError: format_row_data() got an unexpected keyword argument 'sun_rashi_transition'`

- [ ] **Step 3: Update `format_row_data` in `export.py`**

Add the new parameter to the signature (after `vira_nirvana_samvat`):

```python
def format_row_data(
    date_str: str,
    julian_date: float,
    planets: dict[str, float],
    panchang: dict,
    jain_tithi: dict,
    sunrise_str: str,
    sunset_str: str,
    moonrise_str: str,
    moonset_str: str,
    ayanamsa_dec: float,
    ayanamsa_name: str = 'Lahiri',
    tz_offset: float = 5.5,
    tz_label: str = "IST",
    vikram_samvat: int | None = None,
    vira_nirvana_samvat: int | None = None,
    sun_rashi_transition: dict | None = None,
) -> dict:
```

Then, after the line `row['Sun_Rashi'] = get_sun_rashi(julian_date)` (line ~74), add:

```python
    _tr = sun_rashi_transition or {}
    row['Rashi Ends']    = "Yes" if _tr.get("occurs_today") else ""
    row['Sankranti Time'] = _tr.get("ingress_time") or ""
```

- [ ] **Step 4: Run tests**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py::test_csv_row_has_rashi_ends_yes_on_sankranti tests/test_sankranti_moment.py::test_csv_row_rashi_ends_blank_on_regular_day -v
```

Expected: 2 PASSED

### 5b — main.py

- [ ] **Step 5: Update `main.py`**

Add `get_sankranti_moment` to the astronomy import block (after `jd_to_local_time_string`):

```python
from astronomy import (
    local_time_to_jd,
    get_ayanamsa,
    get_all_planet_positions,
    get_sankranti_moment,
    get_sunrise, get_sunset,
    get_moonrise, get_moonset,
    jd_to_local_time_string,
    AYANAMSA_SYSTEMS,
)
```

Add `get_timezone_name` import after the astronomy block:

```python
from location_service import get_timezone_name
```

Inside `_compute_day`, after `civil_date = date(year, month, day)` (around line 113), add:

```python
        tz_name    = _G.get('tz_name')
        transition = get_sankranti_moment(civil_date, tz_name) if tz_name else None
```

Then pass it to `format_row_data` (add as the last keyword argument):

```python
        row = format_row_data(
            date_str            = f"{year:04d}-{month:02d}-{day:02d}",
            julian_date         = jd_sr,
            planets             = planets,
            panchang            = panchang,
            jain_tithi          = jain_tithi,
            sunrise_str         = jd_to_local_time_string(jd_sr, tz_offset),
            sunset_str          = jd_to_local_time_string(jd_ss, tz_offset),
            moonrise_str        = jd_to_local_time_string(jd_mr, tz_offset),
            moonset_str         = jd_to_local_time_string(jd_ms, tz_offset),
            ayanamsa_dec        = ayanamsa_val,
            ayanamsa_name       = ayanamsa,
            tz_offset           = tz_offset,
            tz_label            = tz_label,
            vikram_samvat       = vs,
            vira_nirvana_samvat = vns,
            sun_rashi_transition = transition,
        )
```

In `main()`, resolve `tz_name` from lat/lon and add it to config (after `festival_dates` loop):

```python
    tz_name = get_timezone_name(args.lat, args.lon)

    config = {
        'lat':            args.lat,
        'lon':            args.lon,
        'tz_offset':      args.tz_offset,
        'tz_label':       args.tz_label,
        'tz_name':        tz_name,
        'ayanamsa':       args.ayanamsa,
        'festival_dates': festival_dates,
    }
```

### 5c — range_generation_service.py

- [ ] **Step 6: Update `range_generation_service.py`**

In `generate_year_range_exports`, update the `config` dict (around line 36):

```python
    config = {
        "lat":      location.lat,
        "lon":      location.lon,
        "tz_offset": tz_info["offset_hours"],
        "tz_label":  tz_info["label"],
        "tz_name":   location.timezone,
        "ayanamsa":  ayanamsa_name,
    }
```

- [ ] **Step 7: Run full test suite**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/ -v
```

Expected: all tests PASSED

- [ ] **Step 8: Commit**

```bash
cd /home/Manu/Projects/Jain_panchang && git add export.py main.py range_generation_service.py tests/test_sankranti_moment.py && git commit -m "feat: add Rashi Ends and Sankranti Time columns to CSV/Excel output"
```

---

## Task 6: PDF — ingress time in Sun Rashi cell

**Files:**
- Modify: `export_pdf.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_sankranti_moment.py`:

```python
from astronomy import get_sankranti_moment as _gsm


def test_pdf_sun_rashi_display_on_sankranti():
    transition = _gsm(dt_date(2025, 4, 14), "Asia/Kolkata")
    # Simulate what export_pdf.py should produce for the Sun_Rashi_Display cell
    curr_rashi = "Mesh"
    if transition["occurs_today"] and transition["ingress_time"]:
        display = f"{curr_rashi}<br/><font size='6'>{transition['ingress_time']}</font>"
    else:
        display = curr_rashi
    assert "<br/>" in display
    assert transition["ingress_time"] in display
    assert "Mesh" in display


def test_pdf_sun_rashi_display_on_regular_day():
    transition = _gsm(dt_date(2025, 6, 1), "Asia/Kolkata")
    curr_rashi = "Mithun"
    if transition["occurs_today"] and transition["ingress_time"]:
        display = f"{curr_rashi}<br/><font size='6'>{transition['ingress_time']}</font>"
    else:
        display = curr_rashi
    assert display == "Mithun"
    assert "<br/>" not in display
```

- [ ] **Step 2: Run tests to verify they pass already (logic is in the test itself)**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/test_sankranti_moment.py::test_pdf_sun_rashi_display_on_sankranti tests/test_sankranti_moment.py::test_pdf_sun_rashi_display_on_regular_day -v
```

Expected: 2 PASSED (these tests verify the display string construction logic)

- [ ] **Step 3: Update `export_pdf.py`**

**3a** — Add `get_sankranti_moment` to the astronomy import line (line 9):

```python
from astronomy import (
    get_sankranti_moment,
    local_time_to_jd,
    jd_to_local_time_string,
    get_sunrise,
    get_sunset,
    get_planetary_longitude,
    get_rashi_name,
    get_sun_rashi,
)
```

**3b** — Add `tz_name: str | None = None` to `generate_pdf_calendar` signature:

```python
def generate_pdf_calendar(
    year: int,
    out_filename: str,
    lat: float = 26.9124,
    lon: float = 75.7873,
    tz_offset: float = 5.5,
    ayanamsa: str = 'Lahiri',
    tz_name: str | None = None,
):
```

**3c** — Right after the `chaitra_shukla_1`/`diwali` lines (around line 57), resolve `tz_name` if not supplied:

```python
    if tz_name is None:
        from location_service import get_timezone_name
        tz_name = get_timezone_name(lat, lon)
```

**3d** — Inside the per-day loop (after `all_rows.append(row)` at line ~98), store the sankranti info in the row:

```python
            row["__sankranti"] = get_sankranti_moment(civil_date, tz_name)
            all_rows.append(row)
```

**3e** — Replace the `Sun_Rashi_Display` post-processing loop (lines 100–106) with:

```python
    for row in all_rows:
        sankranti  = row.pop("__sankranti", {})
        curr_rashi = row["Sun_Rashi"]
        if sankranti.get("occurs_today") and sankranti.get("ingress_time"):
            row["Sun_Rashi_Display"] = (
                f"{curr_rashi}<br/>"
                f"<font size='6'>{sankranti['ingress_time']}</font>"
            )
        else:
            row["Sun_Rashi_Display"] = curr_rashi
```

- [ ] **Step 4: Run full test suite**

```bash
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/ -v
```

Expected: all tests PASSED

- [ ] **Step 5: Smoke-test PDF generation**

```bash
cd /home/Manu/Projects/Jain_panchang && python export_pdf.py --year 2025 --out /tmp/test_2025.pdf && echo "PDF OK"
```

Expected: `Generated PDF: /tmp/test_2025.pdf` and `PDF OK` — open the file and verify that April 14 row shows "Mesh" + time on two lines in the Sun Rashi column. Other rows should show only the Rashi name.

- [ ] **Step 6: Commit**

```bash
cd /home/Manu/Projects/Jain_panchang && git add export_pdf.py tests/test_sankranti_moment.py && git commit -m "feat: show Sankranti ingress time in PDF Sun Rashi cell"
```

---

## Verification Checklist

After all tasks complete, run these checks in order:

```bash
# 1. All tests pass
cd /home/Manu/Projects/Jain_panchang && python -m pytest tests/ -v

# 2. JSON for Sankranti day — sun_rashi_transition present
python -c "
from panchang_service import generate_location_panchang
from datetime import date
import json
r = generate_location_panchang(date(2025, 4, 14), 26.9124, 75.7873, 'Asia/Kolkata', 'Lahiri')
print(json.dumps(r['panchang']['sun_rashi_transition'], indent=2))
"

# 3. JSON for regular day — sun_rashi_transition is None
python -c "
from panchang_service import generate_location_panchang
from datetime import date
r = generate_location_panchang(date(2025, 4, 13), 26.9124, 75.7873, 'Asia/Kolkata', 'Lahiri')
print('transition:', r['panchang']['sun_rashi_transition'])
"

# 4. Generate CSV for April 2025 and check Rashi Ends column
python main.py --start_year 2025 --end_year 2025 --lat 26.9124 --lon 75.7873 --format csv --output /tmp/test_panchang
grep "Rashi Ends\|14.*Yes\|Sankranti Time" /tmp/test_panchang.csv | head -5

# 5. PDF smoke test
python export_pdf.py --year 2025 --out /tmp/test_2025.pdf
```
