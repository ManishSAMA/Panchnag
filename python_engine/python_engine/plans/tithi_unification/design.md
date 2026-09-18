# Tithi Unification: 6-Ghati as the Single Day-Identity Anchor

Status: design approved in chat, pending spec review before implementation planning.
Scope: Architectural (brainstorming skill classification).
No production code has been changed as of this document. See `snapshot_festival_dates.py`
and `festival_dates_2026.xlsx` in this directory for the pre-refactor baseline.

## Problem

The engine currently mixes three different "which tithi governs this civil day"
rules across files that are supposed to agree with each other:

1. **Udaya (sunrise) tithi** — `panchang.py`'s `find_chaitra_shukla_1`,
   `_find_tithi_in_range`, `find_diwali`, `is_kshaya_month`, and the base
   `tithi`/`paksha`/`tithi_in_paksha` fields on every snapshot in
   `festival_service.py::_build_snapshots`.
2. **Jain 6-ghati tithi** (sunrise + 2h24m) — `panchang.py`'s
   `calculate_jain_tithi_from_sunrise`, and the `jain_tithi`/`jain_paksha`/
   `jain_tithi_in_paksha` fields on the same snapshots, used only by
   `_sixghati_pullback` / `_kalyanak_first_active_day` in `festival_rules.py`.
3. **Pradosh (sunset) tithi** — `evening_tithi` on the same snapshots, used by
   `day_rule="pradosh"` festivals (Diwali, Mahavir Nirvana, Dhanteras, Ahoi Ashtami).

`_build_snapshots` computes `hindu_month` from the 6-ghati reference point but
`tithi`/`paksha`/`tithi_in_paksha` from plain sunrise. On a civil day where the
6-ghati tithi has already rolled over past midnight-adjacent boundaries that
sunrise hasn't, those two fields disagree — this is the confirmed root cause of
the `parva_tithi_amavasya` double-fire on 18/19 Mar 2026 (see prior diagnostic
turn in this conversation; verified against the live engine, not re-derived here).

## Decision: go "Full Jain" — 6-ghati is the only day-identity anchor

Confirmed with the user, one question at a time, evidence shown before each
final call:

| Question | Decision | Evidence considered |
|---|---|---|
| How does the Kalyanak weak/strong pullback survive collapsing sunrise-tithi and 6-ghati-tithi into one field? | Keep a **private, internal-only** `_sunrise_tithi()` helper used solely inside `_sixghati_pullback` / `_kalyanak_first_active_day`'s comparison. It is never exposed as a snapshot field or a public "Tithi" value anywhere. | — |
| Should pradosh (sunset) tithi survive for evening festivals? | ~~**No** — pradosh is eliminated too.~~ **SUPERSEDED 2026-09-13 — pradosh MUST survive. See "Superseded decisions" below.** | Computed 2026 Mumbai data: 8 Nov sunset = Amavasya (pradosh), but 8 Nov sunrise AND 6-ghati = Krishna Chaturdashi; 9 Nov sunrise/6-ghati = Amavasya. Diwali/Mahavir Nirvana move from **8 Nov → 9 Nov 2026**, one day later than every published Jain/Hindu panchang for that year. User confirmed this explicitly, twice, after seeing the number. Recorded here so it is never mistaken for an unnoticed regression later. |
| What's the source of truth for the new expected dates in tests? | **User verifies each changed date** against an external reference (printed panchang / acharya-approved calendar) before that test's expectation is updated. Not "whatever the new code outputs." | — |
| Do the Vrat provider modules (`jain_observances/vrats/*.py`) get unified too? | **Yes**, included in scope. They run their own `SwissEphTithiProvider`/`SwissEphPanchangProvider` (`jain_observances/vrats/provider.py`), independently of `festival_rules.py`'s snapshots — leaving them out would just relocate the hybrid-state bug rather than remove it. | `provider.py` is a single choke point (`get_sunrise`, `get_tithi_at_time`, `is_adhik_month`, `get_hindu_month_name`), but each Vrat module (`daslakshan.py`, `ratnatraya.py`, `shodashkaran.py`, `ravivara.py`, `ashtahnika.py`) supplies its own `cutoff_time` expression to `get_tithi_at_time` — **not yet individually audited**. That audit is a required first step of the implementation plan for this part, not assumed here. |

## Superseded decisions

### Pradosh elimination — REVERSED (2026-09-13)

The table above records "eliminate pradosh" as confirmed, on the strength of Diwali /
Mahavir Nirvana moving 8 Nov -> 9 Nov 2026. **That premise was wrong and the decision
must not be acted on.** The calendar owner has since ruled, and the ephemeris confirms:

* **Diwali 2026 is 8 Nov** — it is the Amavasya *night*, a pradosh observance.
* **Mahavir Swami Moksha Kalyanak 2026 is 9 Nov** — it is the Amavasya *morning*,
  taken at the 6-ghati anchor.

Amavasya runs **08 Nov 11:28 -> 09 Nov 12:32** at Delhi: it begins one afternoon and
ends the next midday, so the night falls on one Gregorian date and the morning anchor
on the next. The two observances legitimately fall on DIFFERENT dates, and no rule may
force them onto the same one. Eliminating pradosh would permanently fix Diwali on the
wrong day.

What was actually broken was not that pradosh existed, but that it was unreachable:
`day_rule` appeared **zero times** in `registry.py`, so every entry silently took the
`"udaya"` default and the `"pradosh"` branch in `SingleTithiFestival.resolve` could
never run. Fixed by resolving Diwali on the pradosh Amavasya day in
`DiwaliChaturmasNishthapan`, and by making an unknown `day_rule` raise at construction
instead of falling back in silence.

**Standing conclusion: there is no single day-identity anchor.** Diwali needs sunset,
Kalyanaks need the sunrise day plus the 6-ghati pullback, parva tithis need the
6-ghati anchor. Any future plan that assumes one anchor for everything is wrong.

### Phase 2 snapshot unification — IMPLEMENTED (2026-09-13)

`_build_snapshots` now sources public `tithi`/`paksha`/`tithi_in_paksha` from the
6-ghati `reference_jd`. The plain-sunrise values survive as private `_sunrise_*`
fields, read only by Kalyanak candidate selection, `_sixghati_pullback` and
`_origin_pullback_day`, whose weak/strong comparison needs an udaya day to compare
against. `_kshaya_backshift` takes the field its pool was selected on.

Verified consequence at the Chaitra/Vaishakh 2026 boundary (ruled correct by the
calendar owner, pinned in `tests/test_chaitra_vaishakh_2026_anomalies.py`): Shukla 11
is kshaya and merges onto 28 Mar; Purnima lands on **1 Apr**; Vaishakh Krishna Ekam is
vriddhi across **2 and 3 Apr**.


## New architecture

```
get_prevailing_tithi(sunrise_jd, ayanamsa='Lahiri') -> dict
    # sunrise_jd + 2h24m (6 ghati). THE single source of truth for:
    # month rollovers, Amavasya/Purnima detection, Vikram/Shaka/Vira-Nirvana
    # Samvat boundaries, every festival trigger (parva, kalyanak, vrat,
    # mahaparv), and Vrat-provider cutoffs.
```

- `panchang.py`: `find_chaitra_shukla_1`, `_find_tithi_in_range`, `find_diwali`,
  `is_kshaya_month`, and `get_hindu_month`'s callers switch to this anchor.
  `calculate_jain_tithi_from_sunrise` and the standalone `get_tithi(sun_lon, moon_lon)`
  entry point stay as the low-level primitives `get_prevailing_tithi` is built from —
  they are not removed, just no longer called directly at plain sunrise for
  day-identity purposes anywhere in the tree.
- `festival_service.py::_build_snapshots`: `tithi`/`paksha`/`tithi_in_paksha` and
  `hindu_month` both come from the same `reference_jd` — this is what directly
  removes the double-fire. `evening_tithi`/`evening_paksha`/`evening_tithi_in_paksha`
  fields are removed; `day_rule="pradosh"` festivals are re-pointed at the unified field.
- `festival_rules.py`: `day_rule` loses its `"pradosh"` branch (dead once the
  field is gone — `_pradosh_days` and the pradosh branch in
  `SingleTithiFestival.resolve` are deleted, not left dormant).
  `_sixghati_pullback` keeps its two-value comparison, sourced from
  `_sunrise_tithi()` (new, private, internal-only) vs. the now-unified public tithi.
- `panchang_service.py`: daily API drops the separate `jain_tithi` /
  `Jain_Tithi_Name` display and `reference_checks` payload (there is only one
  Tithi now); `"primary_day_rule"` is relabeled from `"udaya_tithi"` to
  `"6_ghati_tithi"`.
- `jain_observances/vrats/provider.py` + the five Vrat modules: unified once
  each module's `cutoff_time` expression is individually read and accounted for
  (see open item below).
- PDF export / `db_generator.py` / `check_tithi.py` / `export.py` / the
  `generate_hindi_calendar_pdf*.py` scripts: updated to match, since they all
  call into the functions above rather than duplicating tithi math.

## Non-goals / explicitly out of scope for this pass

- Re-deriving whether 6-ghati is the astrologically "more correct" choice in
  general — that determination was made in the prior diagnostic conversation
  and is not re-litigated here.
- Any UI/frontend changes beyond the label rename noted above.
- Silently "fixing" any date without the user's explicit sign-off (see rollout).

## Rollout (detail lives in the implementation plan, not here)

1. Core `get_prevailing_tithi` + `panchang.py` month/Amavasya/Samvat functions,
   TDD from scratch.
2. `festival_service.py` snapshot unification — this alone fixes the
   `parva_tithi_amavasya` double-fire; verify via
   `snapshot_festival_dates.py --mode after` that its 18/19 Mar rows collapse
   from 2 to 1.
3. Registry festival-by-festival diff pass using the same tool: every row
   whose `Status` comes back `CHANGED`/`MISSING_AFTER`/`NEW_AFTER` gets
   presented to the user individually for confirmation against an external
   source before its corresponding test (`test_jain_festivals.py`,
   `test_tirthankara_kalyanaks.py`, `test_samvat.py`, `test_hindu_month.py`,
   `test_month_overview.py`, etc.) is updated. This is expected to be the
   longest step — ~1,780 baseline rows across 4 profiles, most unaffected,
   but the affected subset is not yet known until the diff is run.
4. Vrat provider audit + unification (`jain_observances/vrats/*.py`) — read
   each module's `cutoff_time` expression first, then unify.
5. `panchang_service.py` API/display cleanup, PDF export label updates.

Each step is its own TDD red/green cycle per CLAUDE.md; commits wait for
explicit approval as usual.

## Risk summary

- Known, accepted, user-confirmed regression: Diwali/Mahavir Nirvana/Dhanteras/
  Ahoi Ashtami move one day later than every other published Jain calendar for
  years where pradosh and 6-ghati disagree (2026 is one such year).
- Unknown-until-diffed: how many of the ~60 registry entries and 4 profiles
  shift dates. The baseline sheet exists precisely to bound this before any
  code changes land.
- Vrat provider `cutoff_time` audit is unstarted; unification there could
  surface additional per-module rules not yet accounted for in this document.
