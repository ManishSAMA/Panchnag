# Plan: Adhik-Maas purnimanta resolution for Krishna-paksha rules

## Problem

In an Adhik-Maas year (VS 2083 = Adhika Jyeshtha, amanta ~17 May–15 Jun 2026), a Krishna
paksha's **adhik/nija status is opposite** in amanta vs purnimanta reckoning:

| Physical paksha (2026) | amanta (`hindu_month` / `is_adhika`) | purnimanta (book) |
|---|---|---|
| 2–16 May Krishna | Vaishakha / **False** | **Adhik** Jyeshtha Krishna |
| 1–15 Jun Krishna | Adhika Jyeshtha / **True** | **Nija** Jyeshtha Krishna |

`SingleTithiFestival` filters `s["hindu_month"] == self.jain_month and not s["is_adhika"]`
on the **amanta** fields. For a Krishna Kalyanak whose `jain_month` is stored amanta
(= purnimanta − 1, per KALYANAK_AUDIT_NOTES.md), this picks the **May** paksha
(purnimanta *Adhik* Jyeshtha Krishna) instead of the **June** one (purnimanta *Nija*).

Confirmed against Pt. Jaini Jiyalal Panchang:
- Anantnath Janma & Tapa: app 14 May → should be **12 Jun**
- Shantinath Janma-Tapa-Moksha: app 16 May → should be **14 Jun**
- Display: app "Adhika Ashadha Krishna" → should be "Nija Jyeshtha Krishna"

Only bites in adhik-maas years (next after 2026: 2029). Non-adhik years must be unaffected.

## Core mechanism

Add to every snapshot in `festival_service.generate_jain_festivals`:
- `purnimanta_month: str`  (base name, no "Adhika " prefix)
- `purnimanta_is_adhika: bool`

Rule (purnimanta month of a paksha = the month of the Shukla paksha it shares with,
which ends at that month's Purnima):
- **Shukla** snapshot: `purnimanta_month = hindu_month`, `purnimanta_is_adhika = is_adhika`
- **Krishna** snapshot: copy from the **next chronological Shukla** snapshot.
- Trailing Krishna snapshots with no following Shukla (window edge): fall back to naive
  amanta+1 / `is_adhika`.

Implemented as a reverse pass over the already-sorted snapshot list.

## STATUS: increments 1-4 done (commit pending). Increment 5 (custom-class audit) deferred;
## increment 6 (KALYANAK_AUDIT_NOTES) done. See that file for the outcome writeup.
## Bonus: this also fixed the Krishna-paksha half of "snapshot-timing" issue #2 (Diwali 2027
## 09-30 -> 10-29; ChaitraAmavasyaKalyanakVarshantTest now green) and the Margashirsha/
## Agrahayana spelling mismatch (~16 previously-dropped registry entries now resolve).

## Increments (TDD, run suite between each)

1. **Snapshot fields only.** Add the two fields + reverse pass. New unit test:
   2026-05-14 → purnimanta Jyeshtha / adhika=True; 2026-06-12 → purnimanta Jyeshtha /
   adhika=False; 2027 (normal) sanity. No consumer changes → full suite unchanged.

2. **`get_jain_month(s)` → `s["purnimanta_month"].upper()`.** No-op for non-adhik
   (purnimanta_month == amanta+1 there). Full suite green.

3. **`SingleTithiFestival` + `MultiDayFestival` Krishna matching.** For `self.paksha ==
   "Krishna"`: match `s["purnimanta_month"] == _plus1(self.jain_month)` and
   `not s["purnimanta_is_adhika"]`. Shukla path unchanged. Monthly-recurring branch
   groups by `get_jain_month(s)`. RED→GREEN test: Anantnath 2026-06-12, Shantinath
   2026-06-14.

4. **Display.** `festival_service` post-processing (lines ~119-127) and
   `panchang_tithi_map` (lines ~171-177): use `purnimanta_month` / `purnimanta_is_adhika`
   instead of the naive shift. Test label "Nija Jyeshtha Krishna" for 2026-06-12.

5. **Custom rule classes.** Audit each class that filters `s["hindu_month"].upper() in
   [...]` + `is_adhika`. Krishna-targeting ones → `get_jain_month(s)` +
   `purnimanta_is_adhika`. Shukla-only → leave. One class / small group per step.

6. **Update KALYANAK_AUDIT_NOTES.md.**

## Regression guards
- `test_jain_festivals.py` + `test_tirthankara_kalyanaks.py` green (modulo the 2 already
  documented as failing — re-check both, ChaitraAmavasyaKalyanakVarshant may interact).
- Run 2026 (adhik) AND 2027 (normal) — diff the full festival list for 2027, expect zero change.
- KalyanakAmantaMonthCorrectionTest / KartikaKrishnaMonthResolutionTest stay green.
