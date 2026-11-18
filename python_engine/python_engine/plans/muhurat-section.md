# Plan: Muhurat section for the mobile app

## Context

The user wants the day data of the mobile app divided into two groups:

1. **Panchang data**: the elements that change each day. The Today "आज का पंचांग" card shows some of them. The Full Panchang screen shows all of them (tithi, nakshatra, yoga, karana, vara, month, paksha, gata, samvats, Rashis, sun times, pachchakkhan, festivals).
2. **Muhurat data**: time windows that are good or bad for an action. This group is new in the app.

The mobile app has no Panchak section now (no "Panchak" or "पंचक" in `mobile/`). The Python web app has a Panchak page. So this work adds a new "मुहूर्त" section. The section is a grid of tiles. Each tile opens a detail screen.

`plans/mobile-app-flutter.md:20` put Rahu Kaal and Dainika Muhurta after the beta. This work changes that decision. The user asked for it.

## Decisions from the user (2026-11-10)

| Topic | Decision |
|---|---|
| Location | A "मुहूर्त" tile on Today **and** a "मुहूर्त" group on Full Panchang. Both open the same `/muhurat` screen. |
| Choghadiya | Remove the Choghadiya tile from Today. Choghadiya is in the Muhurat grid. Its tile opens the existing `/choghadiya` screen. Today gets the Muhurat tile in that place. |
| Tiles | Panchak, Yoga, Abhijit, Rahu Kaal (with Yamaganda and Gulika), Gandmool, Bhadra, Chandra Bal, Choghadiya, Agni Vaas. Jwalamukhi is on the Yoga screen. |
| Yoga tile | Nitya yoga at the top, then the Dainika, Aanandadi, Ravi and Jwalamukhi yogas. |
| Chandra Bal | Show the 6 Rashis with good Chandra Bal today (positions 1, 3, 6, 7, 10, 11 from the Moon Rashi). No birth Rashi setting. |
| Abhijit | Show it on every weekday. No Wednesday rule. |
| Tile face | The name, today's time (or "none today") and a good/bad mark. |
| Reference | The Python engine stays the reference. Add each missing item to Python first, with tests. Export it to the parity fixtures. Then port it to Dart. |

## Data grouping

| Group | Items | Where shown |
|---|---|---|
| Panchang (daily elements) | tithi, nakshatra (pada), yoga (nitya), karana, vara, month, paksha, gata, samvats, Moon/Sun Rashi, sunrise/sunset, pachchakkhan, festivals | Today card (short), Full Panchang (all) |
| Muhurat (time windows) | Rahu Kaal, Yamaganda, Gulika, Abhijit, Panchak, Bhadra (+ residence), Gandmool, Choghadiya, Agni Vaas, Chandra Bal, Dainika/Aanandadi/Ravi/Jwalamukhi yogas | `/muhurat` grid and detail screens |

Nitya yoga is in both groups: the Panchang section keeps it, and the Yoga detail screen repeats it at the top (user decision).

## Calculation rules

| Item | Rule | Python now |
|---|---|---|
| Rahu Kaal | Daylight in 8 parts. Part by weekday: Sun 8, Mon 2, Tue 7, Wed 5, Thu 6, Fri 4, Sat 3 | `panchang.calculate_rahu_kaal` (`panchang.py:499`), **no tests** |
| Yamaganda | Same 8 parts: Sun 5, Mon 4, Tue 3, Wed 2, Thu 1, Fri 7, Sat 6 | missing (DB column only) |
| Gulika | Same 8 parts: Sun 7, Mon 6, Tue 5, Wed 4, Thu 3, Fri 2, Sat 1 | missing |
| Abhijit | Daylight in 15 parts. The 8th part | missing |
| Panchak | Moon sidereal longitude 300°–360°. Entry, exit and next period | `calculate_panchak_kaal` (`panchang.py:1196`) |
| Bhadra | Vishti karana windows from sunrise to next sunrise. Split at a Moon Rashi change. Residence from the Moon Rashi (Earth = high risk) | `calculate_bhadra_kaal` (`panchang.py:958`) |
| Gandmool | Moon in Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati | `yoga_service._gandmool` (`yoga_service.py:446`) |
| Choghadiya | Exists in Dart already | `choghadiya_service.py` |
| Agni Vaas | (tithi + weekday + 1) mod 4 | `calculate_agni_vaas` (`panchang.py:1050`) |
| Chandra Bal | Count from each Rashi to the Moon Rashi. Good at 1, 3, 6, 7, 10, 11. If the Moon changes Rashi in the day, show both lists with the change time | missing |
| Dainika / Aanandadi / Ravi / Jwalamukhi | `yoga_rules.py` + `yoga_engine.py`, entry `detect_all_yogas_for_day` (`yoga_service.py:66`) | exists, tested |

Sources: [Drik Panchang Rahu Kalam](https://www.drikpanchang.com/tutorials/panchang-utilities/rahu-kalam.html), [Hindutone weekday table](https://hindutone.com/astrology/rahu-kalam-yamagandam-gulika-kalam-explained/), [Dekho Panchang muhurtas](https://dekhopanchang.com/en/learn/muhurtas), [Shubh Panchang Chandra Balam](https://performance.shubhpanchang.com/panchang/chandra-balam), [Drik Panchang Bhadra Vasa](https://www.drikpanchang.com/panchang/info/bhadravasa/bhadravasa.html).

## Phases

Each phase is TDD (RED, GREEN, MUTATE, KILL MUTANTS, REFACTOR) and ends with a commit after user approval. Before Phase 1, copy this plan to `plans/muhurat-section.md`.

### Phase 1 — Python reference (`python_engine/python_engine/`)

1. Add tests for `calculate_rahu_kaal` (invariants: the window is 1/8 of daylight, the weekday picks the part).
2. Add `calculate_yamaganda`, `calculate_gulika`, `calculate_abhijit` beside it in `panchang.py`. Use one shared helper "part k of n of the daylight". Weekday tables are module constants.
3. Add `chandra_bal_rashis(moon_rashi) -> tuple[int, ...]` (pure function).
4. Add `muhurat_day.py`: one function that collects all muhurat windows of one sunrise-to-sunrise day into frozen dataclasses. It reuses the functions above, `calculate_panchak_kaal`, `calculate_bhadra_kaal`, `calculate_agni_vaas` and `detect_all_yogas_for_day`. It takes `clock` and `sunrise_rule`.
5. Add a `muhurat` part to `parity_fixtures.day_row`. Regenerate the `core` fixtures (about 1 h on 14 workers) and update `core/manifest.json`.
6. Optional, not in this plan: show Yamaganda, Gulika and Abhijit in the Flask web app.

### Phase 2 — Dart engine: windows and simple items (`mobile/packages/panchang_engine/`)

1. Port Rahu Kaal, Yamaganda, Gulika, Abhijit, Panchak (with the next period), Bhadra (with residence), Gandmool, Agni Vaas and Chandra Bal to `src/panchang/muhurat.dart`.
2. Add `PanchangEngine().muhurat(...)` that returns a `PanchangMuhurat`. Keep it apart from `day()` and `month()`, as `section()` is, so the Month tab does not pay for it.
3. Export the new types from `panchang_engine.dart`.
4. Add parity tests against the Phase 1 fixtures, and unit tests for the invariants.

Decision (user, 2026-11-18): the Python Panchak search (`_find_panchak_crossing_jd`) stopped at a 60 s interval, which is more than the 10 s parity tolerance. It now stops at 1e-7 JD (about 0.01 s), as the Dart boundary solver does, so the web app's Panchak times can move up to 1 minute earlier. The core fixtures were regenerated for it.

Done (2026-11-18): `src/panchang/muhurat.dart` (pure JD functions) and `PanchangEngine().muhurat()` → `PanchangMuhurat` (`TimeWindow`, `PanchakReading`, `BhadraWindow` + `BhadraResidence`, `GandmoolWindow`, `ChandraBalSpan`, `AgniVaas`). The Dart Panchak finds the period as the first crossing of 300° from 6 days before sunrise (when the Moon is in Panchak at sunrise) or from sunrise, and the exit as the next crossing of 0° after it. Tests: `test/unit/muhurat_test.dart`, `test/parity/muhurat_test.dart` (windows shorter than the tolerance are left out, because a boundary near a sunrise can make a sliver on one side only).

### Phase 3 — Dart engine: the day's yogas

1. Export the rules of `yoga_rules.py` to `shared/yoga_rules.json` with a new `scripts/export_yoga_rules.py`. Add a freshness test, as for `shared/festival_registry.json`.
2. Port `match_dainika`, the overrides, `match_aanandadi` (with its varjya window), `_detect_ravi_yoga` and Jwalamukhi to Dart. They read the JSON.
3. Add the yogas to `PanchangMuhurat`. Add parity tests.

Done (2026-11-18): `yoga_rules_json.py` + `scripts/export_yoga_rules.py` write `shared/yoga_rules.json` and the engine's `lib/src/panchang/yoga_rules.g.dart` (the same JSON text as a Dart `const String`, like the other Python-generated `.g.dart` files, so the engine needs no asset and `muhurat()` takes no rules argument). JSON has no int keys or tuples: weekday keys are strings, a (ghati, pala) varjya is a list. `tests/test_yoga_rules_json.py` fails while either file is stale. `src/panchang/day_yogas.dart` ports `match_dainika`, the Dusht Tithi / Amrit Siddhi overrides, dosha bhanga and Aanandadi nullification, Aanandadi with varjya, Ravi Yoga (Sunday exceptions) and Jwalamukhi; `daySegments` builds the tithi and nakshatra segments (Gandmool reuses them). `PanchangMuhurat.yogas` is a list of `DayYoga` (`DayYogaKind`, `YogaNature`). Kept as Python has them: a whole-day varjya (`"full_day"`) gives no varjya window, and Jwalamukhi's pairs name Shukla tithis (1-15) only.

### Phase 4 — App: Muhurat screen and detail screens (`mobile/app/`)

1. Add the route `/muhurat` (grid) and `/muhurat/:kind` (detail) in `router.dart`, pushed with `context.push`, as `/choghadiya` is.
2. Add an `EngineWorker` read for `muhurat()` and a `muhuratReadingProvider`, as `sectionReadingProvider` is (`today_state.dart:49`). The screens read `selectedDateProvider`, `locationProvider` and `sunriseRuleProvider`.
3. Grid screen on `PothiPage`: 9 tiles. Reuse the `_Tile` look of `features/today/feature_tiles.dart` (76 dp minimum, 2 or 3 in a row by text scale). Each tile shows the name, the time or "आज नहीं", and a good/bad mark. The Choghadiya tile opens `/choghadiya`.
4. Detail screens (one widget with a part for each kind):
   - Rahu Kaal: Rahu Kaal, Yamaganda, Gulika with times, the current one marked.
   - Abhijit: the time.
   - Panchak: today's window, or the next period.
   - Bhadra: each window, its residence and risk.
   - Gandmool: each window with its nakshatra.
   - Chandra Bal: the 6 good Rashis (with zodiac signs), and the second list after a Moon Rashi change.
   - Agni Vaas: residence and good/bad.
   - Yoga: nitya yoga, then the good yogas, then the bad yogas (nullified ones marked), Ravi Yoga, Jwalamukhi.
5. Today: replace `tile-choghadiya` with `tile-muhurat` in `FeatureTiles`. Today's `ChoghadiyaBand` stays.
6. Full Panchang: add a `muhurat` group with the same grid. Add a jump link in `_SectionLinks`. Update `full_panchang_screen_test.dart:467-480`, which now says "Rahu Kalam" must not show.
7. Add ARB strings in `app_hi.arb` and `app_en.arb`.
8. Icons: the tiles use existing `NavpadGlyph`s where one fits. New glyphs come from an approved mockup in `.impeccable/mocks/`, as the current icons did. Ask the user to approve the mockup before the glyphs go in.
9. Tests by the `harness.dart` pattern: values on screen equal the engine values, English and Hindi, text scale 1.3/1.6/2.0, tap target guidelines.

### Phase 5 — Documents

Update `CLAUDE.md` (a "Muhurat section" item), `plans/mobile-app-flutter.md` (the Deferred row), `docs/calculations.md` (the new rules) and `DESIGN.md` (new icons).

## Files to change (main ones)

- Python: `panchang.py`, new `muhurat_day.py`, `parity_fixtures.py`, new `scripts/export_yoga_rules.py`, new tests in `tests/`.
- Dart engine: new `src/panchang/muhurat.dart`, new `src/panchang/day_yogas.dart`, `src/day.dart`, `panchang_engine.dart`, `test/parity/`, `test/unit/`, `test/fixtures/core/`.
- App: `router.dart`, new `features/muhurat/`, `features/today/feature_tiles.dart`, `features/full_panchang/full_panchang_screen.dart`, `engine/engine_worker.dart`, `engine/day_reading.dart`, `l10n/app_*.arb`, `shared/navpad_icons.dart`, tests.

## Verification

1. `pytest tests` and `pytest tests_ui` (separately) pass in `python_engine/.venv-win`.
2. `TestCommittedCoreSet` passes after the fixture regeneration.
3. In `mobile/packages/panchang_engine`: `dart test` passes, parity tests included.
4. In `mobile/app`: `flutter analyze` and `flutter test` pass.
5. Run the app on a device or emulator. Open Today → मुहूर्त, then each tile. Compare the Delhi values for one date with Drik Panchang (Rahu Kaal, Abhijit, Bhadra, Panchak).
6. Mutation report for each phase.
