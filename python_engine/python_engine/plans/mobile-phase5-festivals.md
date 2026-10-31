# Phase 5: Festival engine port to Dart (L4)

**Status:** Audit agreed 2026-10-30 (decisions in §6). Build not started: see §7.
**Parent plan:** [`mobile-app-flutter.md`](mobile-app-flutter.md) §1a ("Festival port") and Phase 5.
**Python reference:** `jain_observances/festival_service.py`, `festival_rules.py`, `vriddhi.py`, `vrats/`.
**Dart target:** `mobile/packages/panchang_engine/lib/src/festivals/`, exported through `lib/panchang_engine.dart`.

---

## 1. Main finding

The §1a decision assumed most rules were data that a Dart interpreter could run from
`shared/festival_registry.json`. The audit shows this is only half true:

- **150 of the 207 registry entries are `SingleTithi`.** These are fully data-driven: month,
  paksha, tithi, category, `vriddhi_rule` and `origin_pullback` are all in the JSON. One
  interpreter covers them. They make up **4,272 of 9,876 fixture rows** per profile (Delhi,
  2016–2040), about 43%.
- **The other 57 entries each have their own `rule_type`** (56 types, 1–3 entries each). For
  these the JSON carries only an id, a name and sometimes a month. The real rule (which tithi,
  kshaya fallback, vriddhi day, Adhik handling) **and the ids of every event they emit**
  (`badi_panchami_{year}`, `paryushan_parv_day_3_{year}`, …) live in Python code. No Dart
  interpreter can produce them from the JSON as it stands.
- Four of those types are Digambar-only and never run for the three Shwetambar profiles (§3, F).
  **52 types need porting for the beta.**

The good news is that the 52 special types are built from a small set of shared shapes (§4), so
the hand port is mostly a table of parameters per type on top of 6–7 Dart primitives, not 52
independent algorithms.

`MultiDay`, `Relative` and `NavpadOli` exist in `RuleFactory` but **no registry entry uses them**.
They are not ported.

---

## 2. How Python builds the festival year (what Dart must reproduce)

`generate_jain_festivals(year, lat, lon, profile, sunrise_rule)`:

1. **Rejects** an unknown `sunrise_rule` or `profile`. `FESTIVAL_PROFILES` = `all`, `digambar`, and
   the three Shwetambar profiles.
2. **Snapshots:** one per civil day from **1 Dec of `year-1` to 31 Jan of `year+1`** (~427 days),
   with `clock="standard"` midnight anchors:
   - `_sunrise_tithi` (at sunrise), `jain_tithi` = `tithi` (at sunrise + 144 min), `evening_tithi`
     (at sunset), each with paksha and in-paksha number;
   - `hindu_month` + `is_adhika`: the **amanta** month at the Jain reference instant;
   - `purnimanta_month` + `purnimanta_is_adhika` (`_assign_purnimanta`: a Krishna paksha takes the
     next Shukla paksha's month, which flips the Adhik tag in an Adhik year);
   - `sunrise_jd` (only `RaviVrat` reads it).
3. **Vrat view** (`vrat_view_of_snapshots`): on two consecutive days with the same `jain_tithi`, the
   first day is relabelled as the previous tithi. A rule gets the vrat view when
   `takes_second_day_of_vriddhi(id, category)`: category in `vrat, monthly_vrat, tap_vrat,
   parva_vrat, mahaparv_vrat` and id not in `KEEPS_OWN_VRIDDHI_RULE`
   (`karma_nirjara_vrat, kartika_nandishwar_ashtami, kartika_purnima_ashtahnika_purna,
   phalguna_purnima_ashtahnika_purna, ravi_vrat, ravivara, kartika_shukla_panchami`).
4. Runs every rule that matches the profile (`profile in profiles or "all" in profiles`), in
   registry order, then keeps occurrences whose `start_date` is in `year`, then sorts by
   `start_date` (stable).
5. Post-processing (month/paksha/tithi labels, the `[Dwadashi]` name tag, `upcoming`,
   `panchang_tithi_map`, multi-day collapsing) **does not affect the fixtures**, which keep only
   `id, occurrence_id, start_date, end_date, status` (status is always `confirmed`).

So the effective vriddhi rule of a type is the product of three things: its category (vrat view or
not), the `KEEPS_OWN_VRIDDHI_RULE` list, and the first/last choice inside its own code. The table
in §3 records the result.

---

## 3. Audit: every rule type

Rows = fixture rows per profile, Delhi, 2016–2040 (all three profiles have the same counts).
"View" = which snapshots the rule reads: **S** plain snapshots, **V** vrat view, **P** its own
provider loop (`SwissEphTithiProvider` / `SwissEphPanchangProvider`), **E** direct ephemeris calls.
"Vriddhi / kshaya" is the effective rule after §2 step 3.

### A. Data-driven: `SingleTithi` (150 entries, 4,272 rows)

Python: `SingleTithiFestival.resolve` with `_matches_purnimanta_target`, `_sixghati_pullback`,
`_kshaya_backshift`, `_first_of_two_jain_daystart_days`, `_pradosh_days`, `_origin_pullback_day`.

| Variant | Entries | Selection field | Vriddhi | Kshaya |
|---|---|---|---|---|
| Kalyanak (`kalyanak`, `janam_kalyanak`), annual | 136 | sunrise tithi | **first** (two Jain day-starts → first; else first sunrise day, then 6-ghati pull-back) | last day of tithi−1 in the purnimanta fortnight (`_kshaya_backshift`) |
| Kalyanak with `origin_pullback` | 2 | as above | as above, then Day-1 anchor to the previous day if the tithi was active by its sunset | as above |
| `mahaparv` / `festival`, annual | 6 | sunrise tithi | first, then 6-ghati pull-back | `_kshaya_backshift` |
| Samvatsari (`festival`, `vriddhi_rule: second_day`), profile-specific | 2 | sunrise tithi | **second** | `_kshaya_backshift` |
| `parva`, annual (`jain_month` set) | 2 | Jain day-start tithi | **both days** | `_kshaya_backshift` |
| `parva`, monthly (no `jain_month`), grouped by amanta month | 2 | Jain day-start tithi | **both days** | `_kshaya_backshift` |

All variants use `pradosh` only if `day_rule` says so; no current entry does, but the field is
validated and the code path exists.

### B. Single anchor, fixed list of events (hand port, shared primitive)

One target (amanta month, paksha, tithi). Adhik: if the month repeats in the year, **only the Adhik
month** counts. Then 1–4 events with fixed ids on that day.

| Rule type | Entries | Rows | Category / view | Target | Vriddhi | Kshaya → | Events |
|---|---|---|---|---|---|---|---|
| ShravanaPurnimaRakshabandhan | 1 | 75 | mahaparv / S | Shravana S15 | second | S14 | 3 |
| PhalgunaPurnimaAshtahnikaPurna | 1 | 75 | mahaparv_vrat (kept) / S | Phalguna S15 | second | S14 | 3 |
| MaghaShuklaPanchamiTri | 1 | 75 | shastra / S | Magha S5 | first | S4 | 3 |
| TalaDharTapShantisagarPunyatithi | 1 | 50 | punyatithi / S | Bhadrapada S2 | first | S1 | 2 |
| BadiPanchamiMeruSthapana | 1 | 50 | mahaparv / S | Bhadrapada S5 | first | S4 | 2 |
| NihshalyaAshtamiManchinTithi | 1 | 50 | vrat / **V** | Bhadrapada S8 | first (of V) | S7 | 2 |
| SugandhDashami | 1 | 50 | mahaparv / S | Bhadrapada S10 | first | S9 | 2 |
| VeerShasanJayanti | 1 | 50 | jayanti / S | Shravana K1 | first | Ashadha S15 | 2 |
| GyanDhanTrayodashi | 1 | 50 | mahaparv_vrat / **V** | Kartika K13 | first (of V) | K12 | 2 |
| KartikaAmavasyaMahaviraNirvana | 1 | 50 | mahaparv / S | Kartika K15 | first | K14 | 2 |
| KartikaShuklaEkamNewYear | 1 | 50 | mahaparv / S | Kartika S1 | first | K15 | 2 |
| KartikaShuklaPanchami | 1 | 50 | mahaparv_vrat (kept) / S | Kartika S5 | first | S4 | 2 |
| KartikaPurnimaAshtahnikaPurna | 1 | 50 | mahaparv_vrat (kept) / S | Kartika S15 | second | S14 | 2 |
| JeevDayaAshtami | 1 | 25 | mahaparv_vrat / **V** | Ashwin S8 | first (of V) | S7 | 1 |
| KartikaNandishwarAshtami | 1 | 25 | mahaparv_vrat (kept) / S | Kartika S8 | first | S7 | 1 |
| BhaiDooj | 1 | 25 | mahaparv / S | Kartika S2 | first | S1 | 1 |
| MargashirshaSheetalnathStotram | 1 | 25 | mahaparv / S | Margashirsha S9 | first | S8 | 1 |
| ChaitraAmavasyaKalyanakVarshant | 1 | 25 | kalyanak / S | Chaitra K15 | second (only the Varsha-ant event is emitted) | K14 | 1 |
| AkshayaTritiya | 1 | 25 | mahaparv / S | Vaishakha S3 | first + 6-ghati pull-back | S2 | 1 |
| DiwaliChaturmasNishthapan | 1 | 50 | festival / S | Kartika K15 | Nirvana: last udaya; Diwali: **pradosh** (last evening) | K14 | 2 |
| SplitDayAhoiKarwaDampatya | 1 | 75 | vrat / **V** | Kartika K4 (Karwa), K8 (Ahoi **pradosh**, Dampatya udaya) | per event | K3 / K7 | 3 |

"(kept)" = in `KEEPS_OWN_VRIDDHI_RULE`, so it reads plain snapshots despite a vrat category.

### C. Two anchors: a Prarambh event and a Purna event

Same primitive as B, called twice. Start usually takes the first day of a vriddhi and the end the
second.

| Rule type | Entries | Rows | Category / view | Start (vriddhi, kshaya →) | End (vriddhi, kshaya →) |
|---|---|---|---|---|---|
| ChaitraLabdhiVidhan | 1 | 50 | mahaparv_vrat / V | Chaitra K15 (first, K14) | Chaitra S4 (last, S3) |
| MaghaLabdhiVidhan | 1 | 50 | mahaparv_vrat / V | Magha K15 (first, K14) | Magha S4 (last, S3) |
| SaptaRishiVrat | 1 | 50 | vrat / V | Ashadha S15 (6-ghati, S14) | Shravana K5 (second, K4) |
| SaptaParamsthanVrat | 1 | 50 | vrat / V | Shravana S1 (first, K15) | Shravana S7 (second, S6) |
| RakshabandhanVrat | 1 | 50 | vrat / V | Shravana S13 (first; any kshaya in 13–15 → S12) | Shravana S15 (second, S14) |
| AkshayaNidhiVrat | 1 | 75 | vrat / V | Shravana S10 (first, S9) | Bhadrapada K10 (second, K9) |
| AnantChaturdashiVrat | 1 | 50 | mahaparv / S | Bhadrapada S11 (first, S10) | Bhadrapada S14 (second, S13) |
| RatnatrayaSankatHaranVrat | 1 | 50 | mahaparv_vrat / V | Bhadrapada S13 (first, S12) | Bhadrapada S15 (second, S14); 4 events |
| ShraddhaVrat | 1 | 50 | vrat / V | Ashwin S1 (first, K15) | Kartika K1 (second, Ashwin S15) |
| NavapadOliVrat | 1 | 100 | mahaparv_vrat / V | Chaitra and Ashwin S7 (first, S6) | S15 (second, S14) |
| MonthlyVrat (Pratham Jeth Jinvani) | 1 | 50 | monthly_vrat / V | Jyeshtha K1 (first) | Jyeshtha S15 (last, S14) |
| LabdhiVidhanVrat | 1 | 48 | vrat / V | Bhadrapada K15 | **Samvatsari day** (reads Paryushan-50 result) |

The row counts are taken from the fixtures: when a count is below 25 per event, some years have no
occurrence (e.g. LabdhiVidhanVrat, 48 of 50). Dart must miss the same years.

### D. Anchored in a purnimanta fortnight (`_purn_month_tithi_day`)

| Rule type | Entries | Rows | View | Rule |
|---|---|---|---|---|
| BhadrapadaKrishnaEkamMultiVrat | 1 | 150 | V | purnimanta Bhadrapada K1 (first; kshaya → previous tithi); 6 events, two end on Bhadrapada S15, four on Ashvin K14 |
| TeenChaubisiVrat | 1 | 25 | V | Bhadrapada K3 (first, K2); end Ashvin K14 |
| BhayaHaranVrat | 1 | 25 | V | Bhadrapada K4 (first, K3); end Ashvin K14 |

### E. Recurring or counted

| Rule type | Entries | Rows | View | Rule |
|---|---|---|---|---|
| BhaktambarVrat | 1 | **1,215** | V | every paksha block: S/K 8 (kshaya → 7) and 14 (kshaya → not observed); first day of the (vrat-view) tithi |
| Namokar35Vrat | 1 | **866** | V | a 35-step table (month, paksha, tithi, fallback tithi); first day, kshaya → last day of fallback |
| PushpanjaliVrat | 1 | 403 | V | Chaitra, Bhadrapada, Magha S5–S9 spans emitted per day; kshaya at start → S4 |
| RaviVrat | 1 | 225 | S + **E** | last Sunday of non-Adhik Ashadha Shukla, then 9 Sundays; title from tithi and nakshatra at sunrise and sunrise + 0.1 d (titles not in fixtures, so only the dates matter) |
| ShvetambaraParyushan50Day | 1 | 216 | S | anchor = **last** non-Adhik Ashadha S14; emits day 1, days 43–49, day 50 (= start + 49). Profile list is all three Shwetambar profiles |
| KarmaNirjaraVrat | 1 | 100 | S (kept) | Ashadha–Ashwin S14; Adhik month only if present; two Jain day-starts → first, else first udaya, else first Jain day-start, else last S13 |
| AshtahnikaVrat | 1 | 75 | S | Ashadha, Kartika, Phalguna S8–S15 span; Ashtami kshaya → S7; end = last Purnima |

### F. Provider-based (own day loop, not the snapshots)

These call `SwissEphTithiProvider` (or Rohini's `SwissEphPanchangProvider`) day by day, with their
own time-zone lookup (`get_timezone_name(lat, lon)`) and `jain_day_tithi` (which applies the
second-day rule when the rule takes the vrat view). In Dart they can read the same per-day values
as the snapshots, **provided** the provider's numbers equal the snapshot's (they should: same
clock, same instants). Each also has `except Exception: pass`, which turns any error into "no
occurrence that year".

| Rule type | Entries | Rows | Vriddhi | Python |
|---|---|---|---|---|
| RohiniVrat | 1 | 334 | n/a (nakshatra) | `vrats/rohini.py` `evaluate_rohini_vrat`: Rohini at sunrise, or a Rohini span touching no sunrise → next day; skips 20 days after a hit. **See §6.1 (time-zone bug).** |
| RatnatrayaVrat | 2 | 148 | second (provider) | `vrats/ratnatraya.py`; Prarambh + Purna events |
| DaslakshanVrat | 3 | 75 | second (provider) | `vrats/daslakshan.py`; Bhadrapada, Magha, Chaitra |
| ShodashkaranVrat | 3 | 74 | second (provider) | `vrats/shodashkaran.py`; one year has none |
| RavivaraVrat | 1 | 25 | first (kept) | `vrats/ravivara.py` |

### G. Not needed for the beta (Digambar-only, no fixtures)

`KshamavaniMahaparv`, `SharadPurnimaJayantis`, `PanditJainiJiyalalPunyatithi`,
`PanditJainiJiyalalJanmaDivas` (profile `digambar`). Ported only when Digambar is added.

---

## 4. Dart design

```
lib/src/festivals/
  registry.dart        FestivalRegistry.fromJson (schema_version check), FestivalEntry
  snapshots.dart       FestivalDay (date, sunrise/jain/evening tithi, amanta + purnimanta month,
                       sunrise jd) and the 14-month window builder; vratView()
  primitives.dart      the shared selectors: purnimantaTarget, sixGhatiPullback, kshayaBackshift,
                       firstOfTwoJainDayStarts, pradoshDays, anchorDay (B/C), paksha blocks
  single_tithi.dart    the SingleTithi interpreter
  rules/*.dart         one file per family (B, C, D, E, F), each a table of parameters + a resolver
  festivals.dart       the year orchestrator: profile check, rule order, vrat view, year filter, sort
```

Public API (sketch):

```dart
final registry = FestivalRegistry.fromJson(jsonString);   // the app reads the asset; tests read shared/
final List<FestivalOccurrence> rows = PanchangEngine().festivals(
  location: location, year: 2026, profile: 'shwetambar_sthanakvasi',
  sunriseRule: SunriseRule.modern, registry: registry,
);
// FestivalOccurrence: id, occurrenceId, ruleId, category, start, end (CivilDate), status
```

- Unknown profile → `ArgumentError` naming the three accepted profiles (§6.3).
- The snapshot builder uses the cheap pieces directly (rise/set, `tithiAt`, `lunarMonthsBetween` +
  `amantaLookup` once per window), not the full `PanchangEngine.day` with choghadiya. Target: one
  festival year in well under 1 s on a phone. A year is computed once and cached by the app
  (§1a "Computation"), so the Month tab's dots read the cache and do not add to its 1 s budget.

---

## 5. Test strategy and build order

### Parity test

One parity file, `test/parity/festivals_test.dart`. For each core location × sunrise rule × fixture
year, build the snapshots **once**, run every ported rule type for all three profiles, and compare
to the fixture rows **attributed to those types** (§6.4). A rule type is done when it matches on
every location, both rules and all three profiles. The last step makes the comparison the whole
fixture year, with no attribution.

Unit tests (test-first, through the public API) cover: unknown profile rejected, the year filter,
sorting, the vrat-view relabelling, each primitive's kshaya and vriddhi branches on hand-built
days.

Expected cost: 3 locations × 25 years + 14 × 2 years = 103 location-years per sunrise rule, 206 in
all. Run in the background.

### Build order (most rows first, shared machinery early)

| Step | What | Rows/profile (Delhi) | Running % |
|---|---|---|---|
| 0 | Registry loader, snapshots (+ parity of snapshot labels against `days.json.gz`), vrat view, orchestrator, profile check, parity harness | – | – |
| 1 | `SingleTithi` (kalyanak → mahaparv/festival → Samvatsari → parva annual + monthly → origin pullback) | 4,272 | 43% |
| 2 | `BhaktambarVrat` | 1,215 | 56% |
| 3 | `Namokar35Vrat` | 866 | 64% |
| 4 | `PushpanjaliVrat` | 403 | 68% |
| 5 | `RohiniVrat` (reproducing the §6.1 bug) | 334 | 72% |
| 6 | `RaviVrat` | 225 | 74% |
| 7 | `ShvetambaraParyushan50Day`, then `LabdhiVidhanVrat` (depends on it) | 264 | 77% |
| 8 | Family B primitive + its 21 types | 1,050 | 87% |
| 9 | Family C (12 types) | 723 | 94% |
| 10 | Family D (3 types) | 200 | 96% |
| 11 | `KarmaNirjaraVrat`, `AshtahnikaVrat` | 175 | 98% |
| 12 | Family F provider vrats: Ratnatraya, Daslakshan, Shodashkaran, Ravivara | 322 | 100% |
| 13 | Whole-year equality, no attribution; performance check | – | – |

Each step is one commit, after your approval.

---

## 6. Decisions (settled with the user, 2026-10-30)

1. **Rohini time-zone bug in Python: port it as is, fix later.** `SwissEphPanchangProvider.get_sunrise`
   returns *local* naive time, but `get_nakshatra_spans` reads naive times as *UTC* and returns UTC,
   so `evaluate_rohini_vrat` really asks "is Rohini current at the sunrise clock reading taken as
   UTC" (06:00 UTC = 11:30 IST). Dart reproduces this, in one clearly named place, so parity passes.
   The fix lands in Python first later (test-first), the fixtures are regenerated, and Dart follows.
2. **Occurrences carry ids and registry names only.** `FestivalOccurrence` has id, occurrenceId,
   ruleId, category, start, end, status, and the registry entry's `name` / `name_hindi`. The
   hard-coded titles of special events (e.g. "Paryushan Parv Day 3") come in Phase 6.
3. **Only the three Shwetambar profiles are accepted.** Anything else, including Python's `all` and
   `digambar`, is an `ArgumentError`. Family G is ported when Digambar is added.
4. **Row attribution by id patterns in the Dart test.** The parity test keeps an id-pattern table
   per rule type; the fixtures and their schema are unchanged.
5. **Hand-port the special types now** behind the shared primitives in §4. A Python-first move of
   families B–D into registry data is revisited after the beta.
6. **L4 boundary rule as in L3.** A festival date difference is a failure unless a snapshot label
   (sunrise, Jain day-start or evening tithi, or month) in the days around either date sits within
   10 s of its transition; those cases are printed for a person to check, never silently passed.

Also found during the audit: Python's `swisseph` DLL is blocked by Windows Application Control in
the session sandbox, so fixtures can only be regenerated on the user's own shell.

---

## 7. Progress and what is left

- **Step 0 (part):** done. `FestivalRegistry.fromJson` (schema and `day_rule` checks), the profile
  check on `PanchangEngine.festivals`, `festivalDays` (the 14-month window of sunrise, Jain
  day-start and evening tithis, Amanta and Purnimanta months) at L3 parity with `days.json.gz` for
  every core location and both sunrise rules, `vratView` and `takesSecondDayOfVriddhi`.
  `festivals()` returns an empty list until rule types land.
- **Boundary cases (L3, festival readings):** Delhi traditional 2022-11-23 sunrise tithi (1.02 s from
  the transition) and Ahmedabad traditional 2025-04-21 evening tithi (0.61 s). Any L4 difference
  near these dates traces back to them. The full readings parity takes about 18 min with `-j 4`.
- **Performance note:** one window costs about 1.7 s on desktop (JIT), mostly the ~850 sunrise and
  sunset solves. To revisit in step 13 (e.g. one solve per day for both, or the app's cache).
- **Step 1, `SingleTithi`:** done. Shared selectors in `festivals/primitives.dart` (month aliases,
  Purnimanta target, 6-ghati pull-back, kshaya back-shift, first of two Jain day-starts, pradosh
  days), the interpreter in `festivals/single_tithi.dart`, and the year orchestrator
  (`festivalsFromDays`: profile filter, vrat view per rule, year filter, date order with registry
  order kept for ties). `test/parity/festivals_test.dart` compares every ported type: SingleTithi
  matches exactly for all 17 locations, both sunrise rules and all three profiles (12.8k rows per
  rule for each of Delhi, Ahmedabad, Mumbai), with no boundary cases. The run takes ~8 min with `-j 4`.
- **Step 2, `BhaktambarVrat`:** done (`festivals/rules/bhaktambar.dart`, with `pakshaBlocks` and
  `jainMonthName` added to the primitives). Exact parity everywhere, no boundary cases (16.4k rows
  per rule for each long-range city with SingleTithi). Gotcha: Python repeats a Bhaktambar
  occurrence id within a year (the Pausha fortnight falls at both ends), with different dates, so
  the harness compares multisets and the orchestrator test checks (occurrence id, date) uniqueness.
- **Step 3, `Namokar35Vrat`:** done (`festivals/rules/namokar.dart`, with `amantaMonthInYear` in
  the primitives: the year's days of one Amanta month by name, Adhik-only when it repeats, which
  most family B/C rules also use). Exact parity everywhere, no boundary cases (19.0k rows per rule
  for each long-range city). Mutation check: parity alone does not exercise a kshaya with a doubled
  fallback tithi or an Adhik month for these steps; the unit tests do.
- **Step 4, `PushpanjaliVrat`:** done (`festivals/rules/pushpanjali.dart`). Shukla 5–9 of
  Chaitra, Bhadrapada and Magha, one occurrence per civil day, the start moved to the first
  Chaturthi (or the day before Panchami) when Shukla 5–14 have a kshaya and no doubled tithi. Exact
  parity everywhere, no boundary cases (about 17 more rows per profile and year). Mutation check: parity
  never sees a doubled Chaturthi before such a kshaya; a unit test pins the first-day choice.
- **Step 5, `RohiniVrat`:** done (`festivals/rules/rohini.dart`), with the §6.1 bug kept in one
  function (`_clockReadAsUtc`). `FestivalDay` gained `standardOffset`, the zone's standard UTC
  offset on that date, which the provider-based vrats of step 12 also read their local clock on.
  Exact parity everywhere, no boundary cases, London and New York included (about 13.5 more rows
  per profile and year). Mutation check: parity alone misses the 20-day skip, the 15 Dec start, the
  31 Dec end and the touches-no-sunrise end test; the unit tests kill them all. Python's 0.01-day
  step past each nakshatra's end is an equivalent mutant (it only decides whether a Rohini that
  begins just before the next sunrise is seen, and such a Rohini gives no day either way).
- **Step 6, `RaviVrat`:** done (`festivals/rules/ravi_vrat.dart`). Nine Sundays from the last
  Sunday of the year's non-Adhik Ashadha Shukla (paksha read at the Jain day-start), on the raw
  days since `ravi_vrat` keeps its own vriddhi rule. Occurrence ids join with `_`, not `:`. Python's
  per-day titles (Ravi Pushya, Ravi Saptami) are left for Phase 6. Exact parity everywhere (9 rows
  per profile and year). Mutation check: parity misses the Jain-vs-sunrise paksha reading, the year
  filter and the window check; the unit tests kill them.
- **Step 7, `ShvetambaraParyushan50Day` + `LabdhiVidhanVrat`:** done (`festivals/rules/paryushan.dart`,
  one anchor for both: the last day of the year holding non-Adhik Ashadha Shukla 14). Python names
  the anchor's month from the Amanta reading in one rule and the Purnimanta one in the other; a
  Shukla day has the same month in both, so the port reads it once. Labdhi Vidhan starts on the
  first Purnimanta Bhadrapada Krishna Amavasya (Adhik days only when there are any; on a kshaya the
  last Krishna 14) and ends on Samvatsari. `CivilDate.plusDays` added. Exact parity everywhere
  (11 rows per profile and year). Mutation check: parity misses the second-day anchor, the Adhik
  and year filters, the Amavasya first/K14 last choice and Labdhi's category; the unit tests kill them.
- **Step 8, family B (21 types):** done (`festivals/rules/anchored.dart`). 17 types are one table
  row each (month, Amanta or Purnimanta naming, paksha, tithi, first or second day on a vriddhi,
  fallback tithi, events); Akshaya Tritiya, Diwali + Chaturmas Nishthapan, Veer Shasan Jayanti
  and Karwa / Ahoi / Dampatya are written out. `purnimantaMonthInYear` joins `amantaMonthInYear`
  in the primitives (Labdhi Vidhan now uses it too), and the orchestrator's rule map is a public
  `FestivalRule` typedef. Exact parity everywhere (40 rows per profile and year). Python quirks
  kept: the Purnimanta month filter reads the Amanta Adhik flag; Dampatya Ashtami lands on the Ahoi
  (pradosh) day though its comment says udaya; Veer Shasan's kshaya fallback reaches outside its
  month to Amanta Ashadha Purnima, but only when Purnimanta Shravana has any days. Akshaya
  Tritiya's 6-ghati pull-back is a no-op in Python (its input day already holds Tritiya at the
  Jain day-start) and is left out. Mutation check: parity misses the vriddhi first/second choice,
  the fallback's last day, the Adhik filter, both year filters, Diwali's last pradosh and
  Nishthapan's last udaya, Veer Shasan's Adhik and empty-month checks, and Karwa's first day; the
  unit tests kill them all.
- **Step 9, family C (11 types; Labdhi Vidhan Vrat came in step 7):** done
  (`festivals/rules/paired.dart`). Written out rule by rule over two new primitives,
  `firstHolding` / `lastHolding` (the first or last day whose Jain day-start holds a tithi), which
  family B's selector now uses too; fallbacks chain with `??`. Exact parity everywhere (26 rows
  per profile and year). Python quirks kept: Sapta Paramsthan's and Shraddha's kshaya fallbacks to
  Amavasya take the Amanta month's own Amavasya, at its far end; a third fallback, and
  Rakshabandhan Vrat's, is the window's previous day (Python `snapshots[idx - 1]`); Shraddha's end
  falls back to Ashwin Purnima outside Kartika; `MonthlyVrat` reads Jyeshtha whatever the entry's
  month and emits its start and end independently. Sapta Rishi's 6-ghati pull-back is a no-op as in
  Akshaya Tritiya: Python's vrat view relabels every Jain day-start field together, so the day it is
  given holds Purnima for the pull-back too. Mutation check: parity misses nearly every first/last
  choice on a doubled tithi; 28 mutants, all killed by the unit tests.
- **Step 10, family D (3 types):** done (`festivals/rules/fortnight.dart`). Python
  `_purn_month_tithi_day` is ported once, as `_fortnightDay`: the year's days of the Purnimanta
  fortnight a registry-style Amanta month and paksha name (Adhik Purnimanta fortnights skipped),
  the first day of the tithi, else the last day of the tithi before. These are the first spans
  (end after start), and a missing end gives a one-day span. Exact parity everywhere (8 rows per
  profile and year). Python quirk kept: on a kshaya Bhadrapada Krishna 1 the fallback looks for
  "tithi 0", so all six multi-vrats vanish that year. Mutation check: 17 mutants, all killed by
  the unit tests except `const []` → `[]` (equivalent).
- **Step 11, `KarmaNirjaraVrat` + `AshtahnikaVrat`:** done (`festivals/rules/seasonal.dart`).
  Both read the year's Amanta month (Adhik-only when it repeats) on the raw days, as neither takes
  the second day of a vriddhi. Karma Nirjara is Shukla 14 of Ashadha, Shravana, Bhadrapada and
  Ashwin (kshaya: the last Shukla 13), with an id named by month (`adhik_` for an Adhik month)
  and an occurrence id named by date. Python tries the first of two consecutive Chaturdashi days
  and then the first one, twice; within one month's days these are all the first Chaturdashi, so
  the port reads it once. Ashtahnika runs from the first Shukla 8 (kshaya: the first Shukla 7,
  else the day before the first of Shukla 8–15) to the last Purnima (kshaya: the last of
  Shukla 8–14) in Ashadha, Kartika and Phalguna. Exact parity everywhere (7 rows per profile and
  year). Mutation check: 18 mutants; the unit tests kill all but the hardcoded categories, which
  equal the registry's.
- **Step 12, family F provider vrats (Daslakshan, Ratnatraya, Shodashkaran, Ravivara):** done
  (`festivals/rules/provider_vrats.dart`). Python's day loop over `SwissEphTithiProvider` reads
  the same instants the days hold (Jain day-start tithi, sunrise tithi, Amanta month at the Jain
  day-start), so the port reads the days, in the provider's window: 45 days (Shodashkaran 76) from
  7 days before the first of the Gregorian month `get_greg_month` names, Adhik days skipped. The
  orchestrator hands these rules the raw days, since the provider names a day's month as computed
  while the vrat view moves a relabelled day into the month before; the rules take the vrat view's
  tithi themselves (and in `get_greg_month`, which reads the snapshots) when the entry takes the
  second day. Ravivara alone reads the tithi 84 minutes after sunrise, with `tithiAt`. Python
  quirks kept: Daslakshan's id keeps the registry's month spelling (`daslakshan_Bhadrapada_2026`);
  a Shodashkaran month first found in December of the year before opens its window in December
  of the year itself; the `except Exception: pass` cases become "no vrat". `get_greg_month`'s
  fixed-table fallback, which a 14-month window never reaches, gives no vrat. Exact parity
  everywhere (11 rows per profile and year). Mutation check: 32 mutants; the unit tests kill all
  but the scan's lower tithi bound, Shodashkaran's 76th window day and Ravivara's 84 minutes
  (144 instead), none of which the synthetic days can tell apart; parity covers them.
- **Step 13, whole-year equality:** done. `test/parity/festivals_test.dart` now compares every
  fixture row of the year, with no rule-type attribution (the id patterns are gone), and every
  core location, sunrise rule, year and profile matches exactly with no boundary cases. Rows are
  compared as a multiset, not in order: `parity_fixtures.festival_rows` sorts a day's rows by
  occurrence id, so the fixtures do not record the engine's order within a day. A unit test now
  fails when a registry entry an accepted profile reaches has a rule type with no Dart rule, since
  the orchestrator skips unknown types silently.
- **Step 13, performance (desktop, AOT, Delhi):** one profile's year from scratch takes about
  0.9–1.2 s: the day readings about 0.8 s, the rules about 0.15 s, and each further profile on the
  same readings about 0.15 s. Of the readings, the 427 sunrise solves take about 265 ms, the 427
  sunset solves about 290 ms, the three tithi readings per day about 155 ms (0.12 ms each, mostly
  the Moon), the month names about 30 ms. Of the rules, Rohini's nakshatra search takes about
  140 ms; all others together take under 5 ms. A phone is likely to be several times slower, so the
  §4 target of "well under 1 s on a phone" is not met as is; the year runs once, in the engine
  isolate, and is cached by the app (§1a), so it delays the festival dots, not the Month tab.
  Not yet measured on a device (`mobile/app/tool/perf_main.dart` does not time festivals).
