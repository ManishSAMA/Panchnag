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
- **Left:** the festival parity harness with id attribution and the year orchestrator (land with
  step 1), then §5 steps 1–13.
