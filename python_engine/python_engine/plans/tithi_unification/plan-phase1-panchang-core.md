# Tithi Unification — Phase 1: Core panchang.py Primitives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a single `get_prevailing_tithi_index()` primitive (sunrise + 2h24m / 6 ghati) in `panchang.py` and rewire the two functions that currently determine month/Amavasya boundaries at plain civil sunrise (`_find_tithi_in_range`, `find_diwali`) to use it instead.

**Architecture:** Add one new pure function built on the existing `get_tithi_at_jd` + `JAIN_TITHI_OFFSET_DAYS`. Replace the inline `get_planetary_longitude` + `get_tithi` calls at plain `sunrise_jd` inside `_find_tithi_in_range` and `find_diwali` with calls to the new primitive. No snapshot/festival-registry code changes in this phase. Tasks are ordered so the "before" diff snapshot is captured against unmodified code, ahead of the rewiring tasks — do not reorder.

**Tech Stack:** Python 3.14, pyswisseph, unittest (matching `tests/test_samvat.py` style).

**Spec:** `plans/tithi_unification/design.md`

## Global Constraints

- 6-ghati (sunrise + 2h24m / 144 minutes, `JAIN_TITHI_OFFSET_DAYS` in `panchang.py`) is the sole day-identity anchor being introduced — not sunrise, not sunset/pradosh.
- `get_tithi(sun_lon, moon_lon)` and `calculate_jain_tithi_from_sunrise()` are NOT removed — they remain the low-level primitives the new function is built from.
- No test's expected date is asserted as "religiously correct" — tests in this phase pin the *mechanism* (evaluates at sunrise+144min, not sunrise+0min) using facts already verified live against the engine (see design.md), not claims about which date a real Jain panchang would print. Confirming real-world correctness of `find_chaitra_shukla_1`/`find_diwali` output happens via the manual diff workflow in Task 1/5, gated on the user, per design.md's confirmed decision.
- Commits wait for explicit user approval per project CLAUDE.md — each task's commit step is proposed, not auto-run.

## Out of scope for this plan (tracked in design.md, each needs its own plan)

- `jain_observances/festival_service.py` / `festival_rules.py` snapshot field unification. This is NOT a simple find-and-replace: `_sixghati_pullback` and the Kalyanak day-selection logic work by *comparing* a sunrise-tithi value against a 6-ghati value, and the candidate-selection step that feeds them must keep matching on the (to-be-private) sunrise field specifically so that comparison stays meaningful — switching that matching to the new public 6-ghati field silently makes the comparison a tautology and the pullback machinery a no-op, changing already-verified Kalyanak dates. This needs its own brainstorming pass on exactly which call sites keep the private sunrise field, not just a mechanical rename.
- `panchang_service.py` display fields (`jain_tithi`/`Jain_Tithi_Name`, `primary_day_rule` label).
- `db_generator.py` — **already calls `get_hindu_month`/`is_kshaya_month` at a `ref_jd = sunrise_jd + 2.4/24` reference (db_generator.py:204,248,250)**, i.e. it's already on 6-ghati for month/kshaya detection. Needs its own audit, not an assumption that it's broken.
- `export.py` — likewise already uses `get_hindu_month(julian_date + (2.4/24.0), ...)` (export.py:88). Already correct.
- The Hindi calendar PDF generators (`generate_hindi_calendar_pdf*.py`) call `get_hindu_month(jd_sr, ayanamsa)` at plain sunrise (e.g. `generate_hindi_calendar_pdf.py:287`) — these DO need fixing, but as their own plan once this phase's primitive exists to build on.
- `jain_observances/vrats/provider.py` (`is_adhik_month`/`get_hindu_month_name` call `get_hindu_month(sunrise_jd, ...)` at plain sunrise) and the five Vrat modules that supply their own `cutoff_time` to `get_tithi_at_time` — flagged in design.md as needing a per-module audit before unifying.
- `is_kshaya_month()` itself needs **no code change** — it's already a pure function of whatever `jd` its caller passes; correctness is entirely the caller's responsibility (confirmed: `db_generator.py` already passes it a 6-ghati `ref_jd`).

---

### Task 1: Samvat-anchor BEFORE snapshot (run against unmodified code)

**Files:**
- Create: `plans/tithi_unification/snapshot_samvat_anchors.py`
- Create (by running the script): `plans/tithi_unification/samvat_anchors.xlsx`

**Interfaces:**
- Consumes: `find_chaitra_shukla_1()`, `find_diwali()` from `panchang.py` (current, unmodified signatures — both stay the same after Tasks 3-4 rewire their internals).
- Produces: an `.xlsx` file with `Before_Date` filled, `After_Date` blank, consumed by Task 5.

This must run **before** Tasks 2-4 change any code, so it captures the true "before" baseline — do this task first, in this position, even though it will feel more natural to write the primitive first. Mirrors `snapshot_festival_dates.py`'s Before/After pattern (design.md's confirmed workflow: no test's expected date changes without the user verifying it against an external source), but for the two whole-year anchor dates that sit outside the festival registry entirely.

- [ ] **Step 1: Write the script**

```python
"""
snapshot_samvat_anchors.py -- Before/After sheet for find_chaitra_shukla_1()
and find_diwali(), the two whole-year Samvat-boundary anchors that sit
outside the festival registry (see plans/tithi_unification/design.md).

Usage:
    # Run BEFORE this plan's Tasks 2-4 change any panchang.py code:
    .venv-linux/bin/python plans/tithi_unification/snapshot_samvat_anchors.py --mode before

    # ... Tasks 2-4 happen here ...

    # Run AFTER, against the same file, to fill After_Date and light up the
    # diff formulas:
    .venv-linux/bin/python plans/tithi_unification/snapshot_samvat_anchors.py --mode after
"""
import argparse
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from panchang import find_chaitra_shukla_1, find_diwali  # noqa: E402

YEARS = [2025, 2026, 2027, 2028]
LAT, LON, TZ_OFFSET = 19.0760, 72.8777, 5.5  # Mumbai -- matches main.py's sample coords
AYANAMSA = "Lahiri"

OUT_PATH = Path(__file__).resolve().parent / "samvat_anchors.xlsx"
HEADERS = ["year", "anchor", "Before_Date", "After_Date", "Days_Diff", "Status"]


def collect_rows() -> list[dict]:
    rows = []
    for year in YEARS:
        cs1 = find_chaitra_shukla_1(year, LAT, LON, TZ_OFFSET, AYANAMSA)
        diwali = find_diwali(year, LAT, LON, TZ_OFFSET, AYANAMSA)
        rows.append({"year": year, "anchor": "chaitra_shukla_1", "date": cs1})
        rows.append({"year": year, "anchor": "diwali", "date": diwali})
    return rows


def write_before(rows: list[dict]) -> None:
    if OUT_PATH.exists():
        print(f"Refusing to overwrite existing {OUT_PATH}.", file=sys.stderr)
        sys.exit(1)
    wb = Workbook()
    ws = wb.active
    ws.title = "Samvat_Anchors"
    ws.append(HEADERS)
    for r, row in enumerate(rows, start=2):
        ws.cell(row=r, column=1).value = row["year"]
        ws.cell(row=r, column=2).value = row["anchor"]
        c = ws.cell(row=r, column=3)
        c.value = row["date"]
        c.number_format = "yyyy-mm-dd"
        ws.cell(row=r, column=5).value = f'=IF($D{r}="","", $D{r}-$C{r})'
        ws.cell(row=r, column=6).value = (
            f'=IF($D{r}="","PENDING",IF($C{r}=$D{r},"SAME","CHANGED"))'
        )
    wb.save(OUT_PATH)
    print(f"Wrote {len(rows)} baseline rows to {OUT_PATH}")


def write_after(rows: list[dict]) -> None:
    if not OUT_PATH.exists():
        print(f"{OUT_PATH} does not exist -- run --mode before first.", file=sys.stderr)
        sys.exit(1)
    wb = load_workbook(OUT_PATH)
    ws = wb.active
    by_key = {(r["year"], r["anchor"]): r["date"] for r in rows}
    for r in range(2, ws.max_row + 1):
        key = (ws.cell(row=r, column=1).value, ws.cell(row=r, column=2).value)
        if key in by_key:
            c = ws.cell(row=r, column=4)
            c.value = by_key[key]
            c.number_format = "yyyy-mm-dd"
    wb.save(OUT_PATH)
    print(f"Filled After_Date for {len(rows)} rows in {OUT_PATH}. "
          f"Open it and check Status != SAME against your reference panchang.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["before", "after"], required=True)
    args = parser.parse_args()
    rows = collect_rows()
    (write_before if args.mode == "before" else write_after)(rows)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run in `--mode before`**

Run: `.venv-linux/bin/python plans/tithi_unification/snapshot_samvat_anchors.py --mode before`
Expected: `Wrote 8 baseline rows to .../samvat_anchors.xlsx` (4 years x 2 anchors)

- [x] **Step 3: Commit**

Note: `.gitignore:13` ignores `*.xlsx` project-wide (matches the existing convention for `festival_dates_2026.xlsx`) — `samvat_anchors.xlsx` is a regenerable local artifact, not tracked in git. Only the script is committed:

```bash
git add plans/tithi_unification/snapshot_samvat_anchors.py
git commit -m "Add Before/After diff tool for Chaitra Shukla 1 / Diwali Samvat anchors"
```

---

### Task 2: `get_prevailing_tithi_index()` primitive

**Files:**
- Modify: `panchang.py` (add function after `JAIN_TITHI_OFFSET_DAYS` at panchang.py:236, before `_get_karana_name_from_index`)
- Test: `tests/test_prevailing_tithi.py` (new)

**Interfaces:**
- Consumes: `get_tithi_at_jd(jd: float, ayanamsa_name: str) -> int` (existing, panchang.py:363), `JAIN_TITHI_OFFSET_DAYS: float` (existing, panchang.py:236)
- Produces: `get_prevailing_tithi_index(sunrise_jd: float, ayanamsa_name: str = 'Lahiri') -> int` — used by Task 3 and Task 4 in this plan, and by every later phase in design.md.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_prevailing_tithi.py`:

```python
"""
tests/test_prevailing_tithi.py -- Unit tests for get_prevailing_tithi_index(),
the single day-identity Tithi anchor introduced by the tithi-unification
refactor (see plans/tithi_unification/design.md).
"""
import unittest

from astronomy import get_sunrise, local_time_to_jd
from panchang import get_prevailing_tithi_index, get_tithi_at_jd, JAIN_TITHI_OFFSET_DAYS

LAT, LON, TZ = 19.0760, 72.8777, 5.5  # Mumbai -- matches main.py's sample coords
AYANAMSA = "Lahiri"


class GetPrevailingTithiIndexTests(unittest.TestCase):
    def test_evaluates_at_sunrise_plus_144_minutes_not_at_sunrise(self):
        """18 Mar 2026, Mumbai: the tithi AT sunrise is Krishna Chaturdashi (29),
        but it has already rolled to Amavasya (30) by sunrise + 144 min.
        get_prevailing_tithi_index must report the LATER (6-ghati) value, not
        the sunrise-instant one."""
        jd0 = local_time_to_jd(2026, 3, 18, 0.0, TZ)
        sunrise_jd = get_sunrise(jd0, LAT, LON)

        sunrise_instant_tithi = get_tithi_at_jd(sunrise_jd, AYANAMSA)
        self.assertEqual(sunrise_instant_tithi, 29, "sanity check on the sunrise-instant value")

        self.assertEqual(get_prevailing_tithi_index(sunrise_jd, AYANAMSA), 30)

    def test_offset_applied_is_exactly_the_jain_tithi_offset(self):
        """The prevailing tithi at sunrise_jd must equal the plain tithi
        evaluated at sunrise_jd + JAIN_TITHI_OFFSET_DAYS -- no other offset."""
        jd0 = local_time_to_jd(2026, 3, 19, 0.0, TZ)
        sunrise_jd = get_sunrise(jd0, LAT, LON)

        expected = get_tithi_at_jd(sunrise_jd + JAIN_TITHI_OFFSET_DAYS, AYANAMSA)
        self.assertEqual(get_prevailing_tithi_index(sunrise_jd, AYANAMSA), expected)

    def test_default_ayanamsa_is_lahiri(self):
        jd0 = local_time_to_jd(2026, 3, 20, 0.0, TZ)
        sunrise_jd = get_sunrise(jd0, LAT, LON)
        self.assertEqual(
            get_prevailing_tithi_index(sunrise_jd),
            get_prevailing_tithi_index(sunrise_jd, "Lahiri"),
        )


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_prevailing_tithi_index' from 'panchang'`

- [ ] **Step 3: Implement the minimal function**

In `panchang.py`, immediately after the `JAIN_TITHI_OFFSET_DAYS = 144.0 / 1440.0` line (panchang.py:236):

```python
def get_prevailing_tithi_index(sunrise_jd: float, ayanamsa_name: str = 'Lahiri') -> int:
    """The single day-identity Tithi anchor: the Tithi index (1-30) prevailing
    at sunrise + 2h24m (6 ghati / 144 minutes) -- the classical Jain day-start
    moment. This is the function any caller should use to decide which Tithi
    "owns" a civil day (month rollovers, Amavasya/Purnima detection, Samvat
    boundaries, festival triggers). It deliberately does NOT evaluate at civil
    sunrise itself -- see plans/tithi_unification/design.md for why, and for
    the narrow, explicitly-flagged exception (festival_rules.py's Kalyanak/
    vriddhi pullback machinery, unaffected by this phase).
    """
    reference_jd = sunrise_jd + JAIN_TITHI_OFFSET_DAYS
    return get_tithi_at_jd(reference_jd, ayanamsa_name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add panchang.py tests/test_prevailing_tithi.py
git commit -m "Add get_prevailing_tithi_index() as the single 6-ghati day-identity anchor"
```

---

### Task 3: Rewire `_find_tithi_in_range` to the prevailing-tithi anchor

**Files:**
- Modify: `panchang.py:644-672` (function `_find_tithi_in_range`)
- Test: `tests/test_prevailing_tithi.py` (append)

**Interfaces:**
- Consumes: `get_prevailing_tithi_index()` from Task 2.
- Produces: `_find_tithi_in_range(year, start_month, start_day, search_days, target_tithi, lat, lon, tz_offset, ayanamsa_name) -> date` — unchanged signature; only its internal tithi source changes. `find_chaitra_shukla_1` (panchang.py:675-698) calls this and needs no changes itself.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_prevailing_tithi.py`:

```python
from datetime import date
from panchang import _find_tithi_in_range


class FindTithiInRangeUsesPrevailingTithiTests(unittest.TestCase):
    def test_finds_amavasya_on_march_18_2026_not_march_19(self):
        """Regression test for the parva_tithi_amavasya double-fire root cause
        (see plans/tithi_unification/design.md): under the OLD sunrise rule
        this returned March 19 (documented in the pre-refactor panchang.py
        docstring). Under the prevailing (6-ghati) rule it returns March 18,
        since Amavasya prevails at sunrise+144min on the 18th but not yet at
        sunrise itself; by the 19th's sunrise+144min it has already advanced
        to Shukla Pratipada.

        NOTE: whether March 18 is the date a real Jain panchang would print
        for this Amavasya is a SEPARATE question, verified via
        plans/tithi_unification/samvat_anchors.xlsx (Task 1/5) with the user,
        not asserted here. This test only pins the function's mechanics."""
        result = _find_tithi_in_range(
            2026, 3, 1, 52, 30, LAT, LON, TZ, AYANAMSA
        )
        self.assertEqual(result, date(2026, 3, 18))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py::FindTithiInRangeUsesPrevailingTithiTests -v`
Expected: FAIL — `AssertionError: date(2026, 3, 19) != date(2026, 3, 18)` (current sunrise-rule code still returns the 19th)

- [ ] **Step 3: Rewire the function**

In `panchang.py`, replace the body of `_find_tithi_in_range` (panchang.py:644-672):

```python
def _find_tithi_in_range(
    year: int,
    start_month: int,
    start_day: int,
    search_days: int,
    target_tithi: int,
    lat: float,
    lon: float,
    tz_offset: float,
    ayanamsa_name: str,
) -> date:
    """Scan a date range and return the first day whose PREVAILING Tithi
    (sunrise + 6 ghati -- see get_prevailing_tithi_index) matches.

    The search windows are chosen so that only one occurrence of the target
    Tithi exists in each window (no month-name filter is required).
    """
    for i in range(search_days):
        d = date(year, start_month, start_day) + timedelta(days=i)
        jd_start = local_time_to_jd(d.year, d.month, d.day, 0.0, tz_offset)
        jd_sr = get_sunrise(jd_start, lat, lon)
        if get_prevailing_tithi_index(jd_sr, ayanamsa_name) == target_tithi:
            return d
    raise ValueError(
        f"Could not find Tithi={target_tithi} in {year}-{start_month:02d}-{start_day:02d} "
        f"+ {search_days} days"
    )
```

Also update `find_chaitra_shukla_1`'s docstring (panchang.py:675-698) to remove the now-stale claim that Phalguna Amavasya 2026 is March 19 — replace the final paragraph with:

```python
    The Phalguna Amavasya is the FIRST Tithi=30 (by prevailing/6-ghati Tithi,
    see get_prevailing_tithi_index) in the March 1 - April 22 window (52 days).
    In most years there is only one Amavasya in this range; in years with two,
    the first one is always the Phalguna Amavasya.
    """
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py -v`
Expected: all passed (4 tests)

- [ ] **Step 5: Run the full existing test suite to check for regressions**

Run: `.venv-linux/bin/python -m pytest tests/ test_panchang.py test_ravi_yog.py test_api.py test_bhaktambar.py test_rohini.py -v`
Expected: same pass/fail results as before this task's change, since no existing test calls `_find_tithi_in_range` or `find_chaitra_shukla_1` directly (confirmed by grep during planning — grep for `find_chaitra_shukla_1` across `tests/` and `test_*.py` returns no matches). If anything newly fails, stop and investigate before proceeding — do not assume it's unrelated.

- [ ] **Step 6: Commit**

```bash
git add panchang.py tests/test_prevailing_tithi.py
git commit -m "Rewire _find_tithi_in_range to the 6-ghati prevailing-tithi anchor"
```

---

### Task 4: Rewire `find_diwali` to the prevailing-tithi anchor

**Files:**
- Modify: `panchang.py:701-728` (function `find_diwali`)
- Test: `tests/test_prevailing_tithi.py` (append)

**Interfaces:**
- Consumes: `get_prevailing_tithi_index()` from Task 2.
- Produces: `find_diwali(year, lat, lon, tz_offset=5.5, ayanamsa_name='Lahiri') -> date` — unchanged signature.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_prevailing_tithi.py` (add `from panchang import find_diwali` to the top-level imports):

```python
class FindDiwaliUsesPrevailingTithiTests(unittest.TestCase):
    def test_2026_diwali_unchanged_since_sunrise_and_prevailing_agree(self):
        """For 2026, sunrise-tithi and prevailing(6-ghati)-tithi both name
        Nov 9 as Amavasya (verified live against the engine during design:
        Nov 8 prevailing=Krishna Chaturdashi, Nov 9 prevailing=Amavasya) --
        so find_diwali's OWN (sunrise-based, pradosh is a separate mechanism
        in festival_rules.py, out of scope here) result does not move this
        year. This test locks that invariance so a future change to this
        function is caught if it silently shifts an unrelated case."""
        self.assertEqual(find_diwali(2026, LAT, LON, TZ, AYANAMSA), date(2026, 11, 9))
```

- [ ] **Step 2: Run test to verify it currently passes (invariance baseline)**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py::FindDiwaliUsesPrevailingTithiTests -v`
Expected: PASS already — `find_diwali`'s *current* sunrise-based code already returns Nov 9 for 2026. This is an invariance test, not a red/green pin on new behavior; confirming it passes now (before Step 3's rewire) is what makes Step 4 a verified refactor rather than a blind one.

- [ ] **Step 3: Rewire the function**

In `panchang.py`, replace the body of `find_diwali` (panchang.py:701-728):

```python
def find_diwali(
    year: int,
    lat: float,
    lon: float,
    tz_offset: float = 5.5,
    ayanamsa_name: str = 'Lahiri',
) -> date:
    """Return the Gregorian date of Diwali (Kartik Krishna Amavasya) for the given year.

    The Kartika Amavasya (Diwali) is identified as the first Amavasya (by
    PREVAILING/6-ghati Tithi=30, see get_prevailing_tithi_index) in the
    October 10 - November 25 window where the Sun's sidereal longitude
    (evaluated at the same 6-ghati reference point) is >= 179 degrees. This
    threshold cleanly separates Diwali from the preceding Ashwin Amavasya
    (Mahalaya, max Sun ~178 degrees) and avoids the subsequent Margashirsha
    Amavasya (min Sun ~213 degrees).

    NOTE: this function determines the SUNRISE-DAY-family (prevailing-tithi)
    Diwali date. The registered "Mahavira Nirvana Kalyanak" festival in
    festival_rules.py currently uses a separate PRADOSH (sunset) rule, which
    is out of scope for this phase -- see plans/tithi_unification/design.md.
    """
    for i in range(46):  # Oct 10 - Nov 24 inclusive
        d = date(year, 10, 10) + timedelta(days=i)
        jd_start = local_time_to_jd(d.year, d.month, d.day, 0.0, tz_offset)
        jd_sr = get_sunrise(jd_start, lat, lon)
        reference_jd = jd_sr + JAIN_TITHI_OFFSET_DAYS
        sun_lon = get_planetary_longitude(reference_jd, 'Sun', ayanamsa_name)
        if get_prevailing_tithi_index(jd_sr, ayanamsa_name) == 30 and sun_lon >= 179.0:
            return d
    raise ValueError(f"Could not find Diwali (Kartika Amavasya) for year {year}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py -v`
Expected: all passed (5 tests)

- [ ] **Step 5: Run the full existing test suite to check for regressions**

Run: `.venv-linux/bin/python -m pytest tests/ test_panchang.py test_ravi_yog.py test_api.py test_bhaktambar.py test_rohini.py -v`
Expected: same as Task 3 Step 5 — no existing test calls `find_diwali` directly, so no change expected. Investigate before proceeding if anything newly fails.

- [ ] **Step 6: Commit**

```bash
git add panchang.py tests/test_prevailing_tithi.py
git commit -m "Rewire find_diwali to the 6-ghati prevailing-tithi anchor"
```

---

### Task 5: Samvat-anchor AFTER snapshot + handoff

**Files:**
- Modify (by running the script from Task 1): `plans/tithi_unification/samvat_anchors.xlsx`

**Interfaces:**
- Consumes: `snapshot_samvat_anchors.py` (Task 1), the now-rewired `find_chaitra_shukla_1()`/`find_diwali()` (Tasks 2-4).
- Produces: nothing further downstream — this is the handoff point back to the user.

- [ ] **Step 1: Run in `--mode after`**

Run: `.venv-linux/bin/python plans/tithi_unification/snapshot_samvat_anchors.py --mode after`
Expected: `Filled After_Date for 8 rows...`. Open the file — `chaitra_shukla_1`/2026 is expected to show `CHANGED` (per Task 3's regression test, Phalguna Amavasya moves from Mar 19 to Mar 18, so Chaitra Shukla 1 moves from Mar 20 to Mar 19); `diwali`/2026 is expected to show `SAME` (per Task 4's invariance test). The other years and the `diwali` rows are not predicted in advance — that is the point of generating the sheet.

- [x] **Step 2: Hand the sheet to the user**

Do not update, remove, or reinterpret any `CHANGED` row without the user confirming it against an external reference (printed panchang / acharya-approved calendar), per design.md's confirmed decision. This step has no code artifact — it is the handoff point back to the user, and the natural place to stop and wait rather than press on into the next phase.

**Handoff result (first run, before Task 6):**

| Year | Anchor | Before | After | Status |
|---|---|---|---|---|
| 2026 | chaitra_shukla_1 | Mar 20 | Mar 19 | CHANGED — as predicted (Task 3) |
| 2026 | diwali | Nov 9 | Nov 9 | SAME — as predicted (Task 4) |
| 2028 | chaitra_shukla_1 | Mar 27 | Mar 26 | CHANGED — vriddhi (Amavasya prevails at 6-ghati on Mar 25 *and* 26; scan takes the first). Not a bug; needs user verification against a printed panchang. |
| 2028 | diwali | Oct 18 | **Nov 16** | CHANGED — **BUG**. Kartik Amavasya 2028 is *kshaya* at the 6-ghati anchor (spans Oct 17 ~13:00 → Oct 18 ~08:30, missing both days' sunrise+144min marks). The scan skips it and returns the Margashirsha Amavasya. Fixed by Task 6 below. |
| 2025, 2027 | both | — | — | SAME |

- [x] **Step 3: No commit needed here**

`samvat_anchors.xlsx` is gitignored (`.gitignore:13`, `*.xlsx`) — it's a regenerable local artifact, not tracked in git. Nothing to commit in this step; the file is simply left on disk for the user to open.

---

### Task 6: Kshaya-aware day ownership for `_find_tithi_in_range` / `find_diwali`

Added after the Task 5 handoff surfaced the 2028 Diwali +29-day jump. The strict "prevailing 6-ghati tithi == target" match introduced in Tasks 3-4 silently skips a target tithi that is *kshaya* at the 6-ghati anchor (begins after one day's sunrise+144min and ends before the next day's), and falls through to the following month's occurrence of that tithi.

**Decision:** apply this project's established kshaya convention — the same `-1` rule as `festival_rules.py::_kshaya_backshift` (commit `732e800`): an omitted target tithi merges onto the *preceding* tithi's civil day. For 2028 Diwali this yields Oct 17 (which also matches the old pradosh rule and the published calendars).

**Scope:** kshaya only. Vriddhi (target prevails on two consecutive days) is deliberately left as-is — the forward scan returns the first day; 2028 `chaitra_shukla_1` = Mar 26 stays a user-verification item, not a code change. The Pratipada-kshaya forward-fallback branch of `_kshaya_backshift` is **not** ported: both callers only ever seek Amavasya (30), whose preceding tithi (29) is always present in the search window.

**Files:**
- Modify: `panchang.py` — add `_tithi_owns_civil_day()` near `get_prevailing_tithi_index` (panchang.py:239); rewire the match predicate in `_find_tithi_in_range` (panchang.py:658) and `find_diwali` (panchang.py:712).
- Test: `tests/test_prevailing_tithi.py` (append).

**Interfaces:**
- Consumes: `get_prevailing_tithi_index()` (Task 2), `get_sunrise`, `local_time_to_jd`.
- Produces: `_tithi_owns_civil_day(d: date, target_tithi: int, lat, lon, tz_offset, ayanamsa_name) -> bool` — private; the kshaya-aware replacement for a bare `get_prevailing_tithi_index(jd_sr) == target` check.

- [x] **Step 1: Write the failing tests**

Append to `tests/test_prevailing_tithi.py`:

```python
from panchang import _tithi_owns_civil_day


class TithiOwnsCivilDayTests(unittest.TestCase):
    def test_true_when_target_prevails_at_six_ghati(self):
        """18 Mar 2026: Amavasya (30) prevails at sunrise+144min -> the day owns it."""
        self.assertTrue(_tithi_owns_civil_day(date(2026, 3, 18), 30, LAT, LON, TZ, AYANAMSA))

    def test_true_on_preceding_day_when_target_is_kshaya(self):
        """Kartik Amavasya 2028 is kshaya at the 6-ghati anchor (spans
        17 Oct ~13:00 -> 18 Oct ~08:30, touching neither day's sunrise+144min).
        Under the -1 rule it merges onto 17 Oct, the Chaturdashi day."""
        self.assertTrue(_tithi_owns_civil_day(date(2028, 10, 17), 30, LAT, LON, TZ, AYANAMSA))

    def test_false_on_the_day_after_a_kshaya_target(self):
        """18 Oct 2028: sunrise tithi is Amavasya but by sunrise+144min it has
        rolled to Pratipada; the kshaya Amavasya belongs to the 17th, not here."""
        self.assertFalse(_tithi_owns_civil_day(date(2028, 10, 18), 30, LAT, LON, TZ, AYANAMSA))

    def test_false_on_an_unrelated_day(self):
        self.assertFalse(_tithi_owns_civil_day(date(2026, 3, 10), 30, LAT, LON, TZ, AYANAMSA))


class FindDiwaliKshayaTests(unittest.TestCase):
    def test_2028_kshaya_kartik_amavasya_backshifts_to_oct_17(self):
        """Regression for the Task 5 handoff finding: the strict 6-ghati match
        skipped the kshaya Kartik Amavasya and returned 16 Nov (Margashirsha).
        The -1 kshaya rule lands it on 17 Oct.

        NOTE: 17 Oct 2028 is asserted here as the OUTPUT of this project's
        established kshaya convention, not as independently religiously verified
        -- that check is the samvat_anchors.xlsx re-run + user sign-off."""
        self.assertEqual(find_diwali(2028, LAT, LON, TZ, AYANAMSA), date(2028, 10, 17))
```

Also append a `_find_tithi_in_range` kshaya case:

```python
    def test_find_tithi_in_range_backshifts_a_kshaya_amavasya(self):
        """Same Kartik window, exercised through _find_tithi_in_range directly
        (find_chaitra_shukla_1's own window never hits a kshaya Amavasya in
        2025-2028, so this uses the October window like Task 3's test)."""
        result = _find_tithi_in_range(2028, 10, 10, 46, 30, LAT, LON, TZ, AYANAMSA)
        self.assertEqual(result, date(2028, 10, 17))
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py -v`
Expected: the four `TithiOwnsCivilDayTests` error with `ImportError: cannot import name '_tithi_owns_civil_day'`; once the import resolves, `FindDiwaliKshayaTests` fails `date(2028, 11, 16) != date(2028, 10, 17)` and the `_find_tithi_in_range` case fails similarly.
Actual: collection `ImportError: cannot import name '_tithi_owns_civil_day' from 'panchang'` — RED confirmed.

- [x] **Step 3: Implement**

In `panchang.py`, after `get_prevailing_tithi_index` (panchang.py:246):

```python
def _tithi_owns_civil_day(
    d: date,
    target_tithi: int,
    lat: float,
    lon: float,
    tz_offset: float,
    ayanamsa_name: str,
) -> bool:
    """Whether `target_tithi` (1-30) governs civil day `d` under the 6-ghati
    anchor -- including the kshaya case. `target_tithi` normally owns `d` when
    it is the prevailing tithi at d's sunrise + 6 ghati. When `target_tithi` is
    omitted entirely (it begins after d's 6-ghati mark and ends before d+1's,
    so it prevails on no civil day), it merges onto `d`, the preceding tithi's
    day -- the same -1 rule as festival_rules._kshaya_backshift. Both callers
    (_find_tithi_in_range, find_diwali) only ever pass target_tithi=30, whose
    preceding tithi (29) is always present in their windows, so the Pratipada-
    kshaya forward-fallback is intentionally not implemented here.
    """
    jd_sr = get_sunrise(local_time_to_jd(d.year, d.month, d.day, 0.0, tz_offset), lat, lon)
    prevailing = get_prevailing_tithi_index(jd_sr, ayanamsa_name)
    if prevailing == target_tithi:
        return True
    preceding_tithi = (target_tithi - 2) % 30 + 1
    following_tithi = target_tithi % 30 + 1
    if prevailing != preceding_tithi:
        return False
    d_next = d + timedelta(days=1)
    jd_sr_next = get_sunrise(
        local_time_to_jd(d_next.year, d_next.month, d_next.day, 0.0, tz_offset), lat, lon
    )
    return get_prevailing_tithi_index(jd_sr_next, ayanamsa_name) == following_tithi
```

Then in `_find_tithi_in_range`, replace the loop body's match check:

```python
    for i in range(search_days):
        d = date(year, start_month, start_day) + timedelta(days=i)
        if _tithi_owns_civil_day(d, target_tithi, lat, lon, tz_offset, ayanamsa_name):
            return d
```

And in `find_diwali`, replace the tithi half of the condition (keep the Sun-longitude filter, still evaluated at the 6-ghati `reference_jd`):

```python
    for i in range(46):  # Oct 10 - Nov 24 inclusive
        d = date(year, 10, 10) + timedelta(days=i)
        jd_start = local_time_to_jd(d.year, d.month, d.day, 0.0, tz_offset)
        jd_sr = get_sunrise(jd_start, lat, lon)
        reference_jd = jd_sr + JAIN_TITHI_OFFSET_DAYS
        sun_lon = get_planetary_longitude(reference_jd, 'Sun', ayanamsa_name)
        if _tithi_owns_civil_day(d, 30, lat, lon, tz_offset, ayanamsa_name) and sun_lon >= 179.0:
            return d
    raise ValueError(f"Could not find Diwali (Kartika Amavasya) for year {year}")
```

Update both docstrings to note the kshaya (-1) behaviour.

- [x] **Step 4: Run tests to verify they pass**

Run: `.venv-linux/bin/python -m pytest tests/test_prevailing_tithi.py -v`
Expected: all passed (10 tests).
Actual: 11 passed (the plan under-counted — `TithiOwnsCivilDayTests` 4 + `FindTithiInRangeUsesPrevailingTithiTests` 2 + `FindDiwaliUsesPrevailingTithiTests` 2 + `GetPrevailingTithiIndexTests` 3).

- [x] **Step 5: Full existing suite regression check**

Run (two collision-free invocations — `./test_api.py` and `tests/test_api.py` share a basename and cannot be collected together):
`.venv-linux/bin/python -m pytest tests/ -q`
`.venv-linux/bin/python -m pytest test_panchang.py test_ravi_yog.py test_api.py test_bhaktambar.py test_rohini.py -q`
Expected: same as Task 4 — 2 pre-existing unrelated failures (`test_ravi_yoga_is_always_ashubh_when_present`, `test_panchang KeyError: 'Sun_Dec'`), nothing newly failing.
Actual: `tests/` 583 passed / 2 skipped / 1 failed (`test_ravi_yoga_is_always_ashubh_when_present`); root files 1 failed (`test_panchang KeyError: 'Sun_Dec'`). Both pre-existing (confirmed on `51f0502` with changes stashed). `577 -> 583` passed = the 6 new tests. No new failures.

- [x] **Step 6: Re-run the Samvat AFTER snapshot**

Delete the stale after-columns and re-run:
`.venv-linux/bin/python plans/tithi_unification/snapshot_samvat_anchors.py --mode after`
Expected: `2028 / diwali` row moves from `Nov 16` to `Oct 17` (still `CHANGED` vs the `Oct 18` before-value, now a -1 backshift rather than a +29 skip). Re-hand the sheet to the user; the `2028 / chaitra_shukla_1` -1 (vriddhi) and `2028 / diwali` -1 (kshaya) rows both need external-reference confirmation before any dependent test elsewhere is updated.
Actual: after-snapshot now shows `2028 / diwali` Oct 18 -> Oct 17 (-1). Three CHANGED rows total, all -1d: `2026 / chaitra_shukla_1`, `2028 / chaitra_shukla_1`, `2028 / diwali`. All pending user verification against a printed panchang.

- [x] **Step 7: Commit**

```bash
git add panchang.py tests/test_prevailing_tithi.py plans/tithi_unification/plan-phase1-panchang-core.md
git commit -m "Kshaya-aware day ownership for _find_tithi_in_range / find_diwali"
```

---

## After this plan

Per design.md's rollout order, the next slice is **not** a continuation of this plan — it's `festival_service.py`/`festival_rules.py` snapshot unification, which needs its own brainstorming pass specifically on how `_sixghati_pullback`'s candidate-selection keeps using the (now-private) sunrise field without becoming a no-op once the public field means something different. Do not start that work by extrapolating from this plan's tasks; it has a materially different risk shape (already-verified Kalyanak dates are at stake, not untested boundary functions).
