DO not make changes until you have 95% confidence in what you need to build, ask me followup until you reach the confidence

# Development Guidelines for Claude

> **About this file (v3.0.0-py):** Lean version optimized for context efficiency. Core principles here; detailed patterns loaded on-demand via skills.
>
> **Adapted for this project:** the upstream v3.0.0 guidelines are TypeScript/Vitest-oriented. This project is pure Python (Flask + Swiss Ephemeris + pytest), so the tooling references below are translated. The philosophy — TDD, behavior-driven testing, functional style, small increments — is unchanged.

## Project Context

Jain Panchang is a sunrise-based Panchang generator: a Flask web app plus CLI over Swiss Ephemeris, with Jain festival rules for three Shwetambar profiles.

- **Source root:** `python_engine/` (nested one level below the repo root)
- **Environment:** `python_engine/.venv-win` (Python 3.14). `pyswisseph` has no cp314 wheel — see `docs/setup_and_usage.md`.
- **Tests:** `pytest tests` and `pytest tests_ui` must be run separately.
- **Docs:** `docs/` is long-form and kept accurate; `plans/` holds design docs for in-flight work.
- **Laghu Panchang booklet:** `laghu_panchang.py` (data + cell text) and `laghu_panchang_render.py` (HTML→PDF, Excel); `python main.py laghu --year Y --city X`; `POST /generate-laghu-panchang`; `--school` / `school` (all | vrindavan | uttarapurana | ashadhara) filters kalyanaks via `hindi_calendar_pdf.festivals_for_school`, which the festival export's `source` filter also uses. Times are clock readings from the civil day's midnight (`25:47` = 01:47 next day). Per-day UTC offsets come from `zoneinfo`, unlike `_timezone_snapshot`'s fixed Jan-1 offset, so DST locations are right. `_html_to_pdf(css_page_size=True)` keeps the booklet's 8in×5in `@page`. The first page (and first Excel sheet) carries the place's coordinates (`coordinates_text`); the last page (and last sheet) closes with `made_for_text`, "यह पंचांग <place> (<coordinates>) के लिए बनाया गया है।", using the place name as given (pass a Hindi `city` for an all-Hindi line). `OMITTED_FROM_BOOKLET` drops Parshvanath Jayanti and Jin Murti Sthapana Divas from the booklet only (user directive 2026-10-30); the app calendar keeps them. Design: `plans/laghu-panchang-export.md`.
- **Clock and sunrise settings:** `clock` (`standard` default | `daylight`) and `sunrise_rule` (`modern` default | `traditional`), API field `sunrise`. `astronomy.utc_offset_hours` / `clock_timezone` / `local_date_anchor_jd` / `jd_to_zoned_datetime` take a required `clock`; `get_sunrise` / `get_sunset` take `rule`. `sunrise_rule` is an explicit parameter all the way into the festival engine because `generate_jain_festivals` is `lru_cache`d. The vrat providers always use `clock="standard"`, since their naive-local-time round trip is only exact on uniform 24 h days. Design: `plans/clock-and-sunrise-settings.md`.
- **Vriddhi rule:** vrats (`jain_observances/vriddhi.py`) take the second day of a Jain day-start vriddhi (वृद्धौ उत्तरा); kalyanaks keep the first, parva tithis show both days, Karma Nirjara keeps the first. Vrat rules read `vrat_view_of_snapshots`; provider-based vrats use `vrats.provider.jain_day_tithi`. Design: `plans/vrat-vriddhi-second-day.md`.
- **Kalyanak Hindi names:** `registry.py` derives `name_hindi` for every "Shri X Ji - Y Kalyanak" entry from `TIRTHANKAR_HINDI` + `KALYANAK_HINDI` ("श्री नेमिनाथ जी — केवलज्ञान कल्याणक"; गर्भ/दीक्षा, the Digambar terms of the source texts). A new tirthankar spelling must be added there or `tests/test_kalyanak_hindi_names.py` fails. When festival_service puts a native-tithi tag in front of `name` ("[Ekadashi] …"), it tags `name_hindi` in Hindi too ("[एकादशी] …", via `hindi_observance_map.TITHI_PREFIX_HI`). Schools disagree on some kalyanak tithis (e.g. Neminath Omniscience, Ashwin S1 vs S9); the registry keeps one entry per variant, and only `festivals_for_school` filters them.
- **Vikram Samvat new year:** `find_chaitra_shukla_1` (and Dart `chaitraShuklaPratipada`) returns the first day from 1 March whose 6-ghati reference instant falls in Amanta Chaitra, Adhika Chaitra included (2029 turns over on 16 Mar). It names the month rather than taking the day after the first Amavasya, which went wrong when Phalguna's Amavasya fell before 1 March (2024) or Amavasya prevailed on two days (2028).
- **Mobile app (Flutter, in `mobile/`):** a pure-Dart engine tested against this Python engine as the reference.
  - `parity_fixtures.py` with `scripts/export_parity_fixtures.py` (`--set core|full|custom`, `--workers N`) writes gzip JSON fixtures to `mobile/packages/panchang_engine/test/fixtures/`. Only `core/` is committed; it takes about 1 h on 14 workers, and `full` about 4 h. The files are byte-reproducible, so regenerate them after any engine change and commit the diff. `core/manifest.json` records a code fingerprint (AST, docstrings and comments ignored) of every engine module the exporter imports, found by `modulefinder`; `TestCommittedCoreSet` fails, naming the changed files, until you regenerate. Edits to `hindi_calendar_pdf.py` count, because `festival_rules` imports it.
  - `shared/festival_registry.json` is generated from `registry.py` by `scripts/export_festival_registry.py`. A freshness test fails until you regenerate it.
  - `generate_jain_festivals` raises `ValueError` for a profile outside `FESTIVAL_PROFILES` (`festival_service.py`): every profile the registry names, plus `"all"`. Gotcha: `"all"` selects only the festivals tagged `"all"` (common to every tradition), not the union of every profile.
  - Plans: `plans/mobile-app-flutter.md`, `plans/mobile-phase1-fixtures.md`.
  - **App** (`mobile/app`, Android only, `io.github.manishsama.jainpanchang`): Flutter 3.47.6 at `C:\dev\flutter`, Riverpod 3, go_router, `shared_preferences`, ARB l10n (`hi` template, `en`; the generated `app_localizations*.dart` is gitignored and made by `flutter pub get`). Look and tokens: repo-root `DESIGN.md` (Navpad Colours), as `theme/navpad.dart` (ThemeExtension) + `theme/theme.dart` (hand-built ColorScheme). Fonts are bundled OFL files in `assets/fonts`. A tab appears only once its screen is built, never as a placeholder. The preset cities must match the parity fixtures' core locations (a test checks). The app imports only `package:panchang_engine/panchang_engine.dart` (`PanchangEngine().day(...)`; the `implementation_imports` lint enforces it) and reads days through one long-lived isolate, `engine/engine_worker.dart`. The Month tab reads a whole month with one `PanchangEngine().month(...)` call, which shares lunar months, sunrises and samvat searches and must equal `day()` for each date (0.5–0.6 s on a phone; design `plans/mobile-month-tab.md`); `tool/perf_main.dart` times the engine on a device (`flutter run --profile -t tool/perf_main.dart`). CI: `.github/workflows/flutter-app.yml`.
  - **Release** (`mobile/app/RELEASE.md`, `PRIVACY.md`): release builds sign from the gitignored `android/key.properties` and fall back to the debug key without it (Play rejects those). CI builds the AAB but never signs. Bump the `+N` versionCode in `pubspec.yaml` for every upload. The launcher icon is vector XML (siddhashila on Navpad red), because the root `.gitignore` drops `*.png`: any PNG under `android/.../res` needs an exception or a clean clone cannot build.
  - **Settings** (`features/settings`, `settings/settings_store.dart`, gear in each tab's top bar via `shared/settings_button.dart`; Today's location chip opens it too): every choice is a `shared_preferences` key read synchronously at start. `traditionProvider` saves the registry's profile string ID (`settings.tradition`, default Tapagachchha) for the festival port; `languageProvider` (phone | hi | en) feeds `MaterialApp.locale`; `monthSystemProvider` picks `PanchangDay.month` (Purnimanta) or `.amantaMonth` via `lunarMonthOf`; `sunriseRuleProvider` goes into every `DayRequest`/`MonthRequest`. The location is a sealed `Place`: a `PresetCity` or a `GpsPlace` (one coarse fix via `geolocator`, the phone's IANA zone via `flutter_timezone`, named after a preset city within 50 km, else "My location"); tests replace `gpsLocatorProvider`. Gotcha: `tester.pageBack()` finds only an English "Back" tooltip, so Hindi tests tap `BackButton`.
  - **Festivals on Today and Month** (`features/festivals/festival_state.dart`, `format/festival_text.dart`, `shared/festival_mark.dart`, `shared/festival_icon.dart`): `PanchangEngine().festivals` runs in a **second** `EngineWorker` (`festivalWorkerProvider`), so a 1 s+ festival year never queues ahead of a day or month read. `readFestivals` (`engine/festival_reading.dart`) keeps each (place, profile, sunrise rule, year) in memory per isolate; no disk cache yet. `festivalYear(ref, year)` returns null until the year arrives, and the screens paint without it first. The registry is bundled as `assets/festival_registry.json`, a byte copy of `shared/` (a test fails until it is re-copied). Marks (`kindOf`, drawn by `FestivalIcon` via `festivalGlyph`): mahaparv/festival/utsav → red kalash, kalyanak → red five lights, every `*vrat` category (Navapad Oli and the Namokar chain included) → green diya, everything else → red temple flag; at most 3 per cell, in that priority order. Today has a red band (parva and kalyanak) and a green band (vrat) for the date shown, in DESIGN.md's red-yellow-green-navy order (tap opens Month on that date), plus the next 4 non-vrat dates (into next year in late December), each under a Tiro day-numeral heading ("7 नवंबर · शनिवार · 7 दिन बाद", "कल" for the next day, counted from the date shown). Lines show `name_hindi` in Hindi (English when empty), one line per name, since a rule's events share their entry's name until Phase 6 titles them. No span crosses a year boundary in 2016–2040 (the longest is 72 days), so a date reads only its own year. Tests read festivals on the test isolate through `realFestivals` in `test/support/harness.dart`. Gotcha: in a `Row`, an `Expanded` name beside a `Flexible` value splits the row in half even when the value is short or empty, so `Band` drops an empty value and `FestivalRow` caps its value's width instead.
  - **Icons and moon** (`shared/navpad_icons.dart`, `shared/moon_phase.dart`, `features/today/feature_tiles.dart`; DESIGN.md §Icons): the app's own line icons (`NavpadGlyph`: sunrise, sunset, nakshatra, ghatika, sunpath, kalash, kalyanak, dhvaja, diya, monthcal, siddhashila) are a `CustomPainter` over the approved mockup's SVG path strings (`.impeccable/mocks/icons-refresh.html`), read by a small `svgPath` parser (M L H V A C S Z), with no SVG dependency. Size and colour come from `IconTheme`. `SunPathIcon(fraction:)` puts the sun at `dayFraction(at, day)` of the daylight on pachchakkhan rows, the yellow band and hero. `MoonPhase(tithi:)` lights i/15 waxing on the right; its dark part is `navy`, not `ink`, so dark mode still shows it. `TimeRow(icon:)` and `Band(icon:)` wrap icons in a 36 dp `IconBadge`. Today's `FeatureTiles` show पर्व सूची only when `GoRouter.configuration.findMatch('/festivals')` matches, so the tile appears once the festivals tab lands. Gotcha: give a `Semantics` label on a drawing `container: true`, or it merges into the hero's label. Pixel tests read paintings through `test/support/pixels.dart`.
  - **Festivals tab** (`features/festivals/festivals_screen.dart`, `/festivals`, the fourth destination): the current year from today to 31 Dec via `festivalYear`, with a spinner until it arrives (so tests holding the year must `pump`, not `pumpAndSettle`). `festivalDates` puts each festival on its first day and a span already under way on today. Five wrapped `FilterChip`s (`FestivalFilter`, saved as `festivals.filter`) filter by the merged line's mark. Gregorian month headings and date numerals use `NavpadType.displayGroup`; a mahaparva line is the filled red row. A date opens Month on it. The nav icon is a Material placeholder until the kalash icon lands; year chip, profile chip, search, tithi line and bell come later.
  - **Panchang section** (Full Panchang's first section; design `plans/panchang-section-and-pothi.md`): the Jain tithi, nakshatra and yoga each with the next (both with ends, even past the next sunrise), every karana of the sunrise-to-sunrise day (2–4), the weekday, month (per the month-system setting), paksha, gata (days the Sun has been in its Rashi, the day holding the Sankranti = day 1), Vikram / Vira Nirvana / Shaka Samvat, and the Moon and Sun Rashis. The reference is Python `day_elements.py`; `parity_fixtures.day_row` carries `tithi_next`, `nakshatra_next`, `yoga`, `karana`, `moon_rashi`, `sun_rashi`, `gata`. In Dart they come from a separate `PanchangEngine().section(...)` (`PanchangSection`; app `SectionRequest` / `sectionReadingProvider`), not from `PanchangDay`, because they more than double a day's cost and the Month tab's `month()` never shows them; only `shakaSamvat` (Vikram − 135) is on `PanchangDay`. Rashis are 0-based (0 = Mesha), yoga and karana 1-based. Lines (`shared/panchang_section.dart`) set times in w600 and the connective ("तक", "until", "गते", "day") in Pothi `secondary`; a nakshatra carries the zodiac sign of each Rashi its padas fall in (`nakshatraRashis`), drawn at 1.25× the font size; the current nakshatra carries its pada ("चित्रा (चरण 1)"). The section is the one place these appear: the groups below it no longer repeat the nakshatra, the months, the samvats or the Jain tithi with its end (the hero still shows month and samvats). Today shows a Pothi-ruled "आज का पंचांग" card (`features/today/panchang_card.dart`, "पंचांग" on another date) under the hero: the Jain tithi, nakshatra (pada and signs), the first yoga and karana, each with its end, and the weekday, then the "पूरा पंचांग देखें" button, Today's only way into Full Panchang (the tile is gone, as is the times list's Nakshatra row; the four remaining tiles sit two by two). `PothiHeading` and `SectionRow` in `shared/panchang_section.dart` serve both screens; tests share Delhi's readers and `lineText` through `test/support/section_lines.dart`. Gotcha: Mukta has no "→", so the button's arrow is an icon. Gotcha: times, their period word and तक are joined with non-breaking spaces so a wrap never strands "AM" or "तक"; tests reading line text replace `\u00A0` with a space.
  - **Share card** (`features/share/`, the share icon before the gear on Today only): `ShareButton` reads the date Today shows (with the month system, sunrise rule and tradition the screen uses, awaiting the festival year), builds `shareCardContent`, paints `ShareCard` in its own offscreen pipeline (`renderShareCard`: `RenderView` + `BuildOwner`, no on-screen widget) at 3× to a PNG, and hands it with `shareText` (the caption) to `sharerProvider` (`share_plus`; tests override it via `openApp(sharer:)`, and every other test gets `noShare`, which throws). The card is 360 dp wide and at least 450 dp tall (1080×1350 px), growing taller on a busy day; it is always the light Navpad scheme at text scale 1. It shows: जय जिनेन्द्र (Devanagari on the English card too), the date, the tithi with its end and the next tithi, the month, VNS · VS, Today's red (parva) and green (vrat) strips as first name + kind or "+N", sunrise and sunset, and a footer with the city and app name. There's no "Play Store" in the footer until the listing exists. Gotcha: the test font draws every glyph 1 em wide, so `share_card_test.dart` loads the bundled Mukta and Tiro with `FontLoader` to test the real 1350 px height.
- **Client release:** `python scripts/build_client_bundle.py` writes the gitignored `client_release/` + zip at the repo root (Windows, `start.bat`, Python 3.11–3.14 with bundled wheels). Launcher files live in `client_files/`; see `docs/setup_and_usage.md` §10c.

## Core Philosophy

**TEST-DRIVEN DEVELOPMENT IS NON-NEGOTIABLE.** Every single line of production code must be written in response to a failing test. No exceptions. This is not a suggestion or a preference — it is the fundamental practice that enables all other principles in this document.

I follow Test-Driven Development (TDD) with a strong emphasis on behavior-driven testing and functional programming principles. All work should be done in small, incremental changes that maintain a working state throughout development.

## Quick Reference

**Key Principles:**

- Write tests first (TDD)
- Test behavior, not implementation
- Type hints on public functions; no bare `Any` where a real type exists
- Immutable data only
- Small, pure functions
- Use real domain types in tests, never redefine them

**Preferred Tools:**

- **Language**: Python 3.14, `from __future__ import annotations`, PEP 604 unions
- **Testing**: pytest (+ `pytest-subtests`); Playwright for `tests_ui`
- **State Management**: frozen dataclasses, module-level constants

## Testing Principles

**Core principle**: Test behavior, not implementation. 100% coverage through business behavior.

**Quick reference:**
- Write tests first (TDD non-negotiable)
- Test through public API exclusively
- Use factory functions for test data (no module-level mutable fixtures)
- Tests must document expected business behavior
- No 1:1 mapping between test files and implementation files

Astronomical code has a specific trap: a test that hardcodes an ephemeris output is a change-detector, not a behavior test. Prefer asserting invariants (a Tithi index is 1–30; a window's end follows its start; a cached value equals the uncached one) over golden numbers. Where a golden date is genuinely the specification — a festival's canonical date — cite the source in the test.

For detailed testing patterns and examples, load the `testing` skill.
For verifying test effectiveness through mutation analysis, load the `mutation-testing` skill.

## Python Guidelines

**Core principle**: Explicit types at trust boundaries, plain types for internal logic.

**Quick reference:**
- Type-hint every public function signature
- No `Any` where a real type exists (use `object` if genuinely unknown)
- Prefer `@dataclass(frozen=True)` over dicts for structured data
- Validate at trust boundaries (`request_parsing.py`), trust internal calls
- Never `except Exception: pass` — if a failure is expected, name it and handle it; if it is not, let it raise

## Code Style

**Core principle**: Functional programming with immutable data. Self-documenting code.

**Quick reference:**
- No data mutation — immutable data structures only
- Pure functions wherever possible
- No nested if/else — use early returns or composition
- Comments explain *why*, never *what* — code should be self-documenting
- Prefer keyword arguments over positional parameters
- Use comprehensions and `itertools` over accumulator loops

Domain exception: this codebase's `panchang.py` and `astronomy.py` carry explanatory comments about the underlying astronomy and the classical rules. Those earn their place — a reader cannot derive "Panchak is Moon longitude 300°–360°" from the code. Keep them.

For detailed patterns and examples, load the `functional` skill.

## Development Workflow

**Core principle**: RED-GREEN-MUTATE-KILL MUTANTS-REFACTOR in small, known-good increments. TDD is the fundamental practice.

**Quick reference:**
- RED: Write failing test first (NO production code without failing test)
- GREEN: Write MINIMUM code to pass test
- MUTATE: Run mutation testing to verify test effectiveness, produce a report
- KILL MUTANTS: Address surviving mutants (ask human when value is ambiguous)
- REFACTOR: Assess improvement opportunities (only refactor if adds value)
- **Wait for commit approval** before every commit
- Each increment leaves codebase in working state

For detailed TDD workflow, load the `tdd` skill.
For refactoring methodology, load the `refactoring` skill.
For significant work, load the `planning` skill. Plans live in `plans/` directory.
For CI failure diagnosis, load the `ci-debugging` skill.

## Output Guardrails

- **Write to files, not chat** — When asked to produce a plan, document, or artifact, always persist it to a file. You may also present it inline for approval, but the file is the source of truth.
- **Plan-only mode** — When asked for a plan, design, or document only, produce ONLY that artifact. Do not write production code, test code, or make any implementation changes unless explicitly asked.
- **Incremental output** — When exploring a codebase, produce a first draft of output within 3-4 tool calls. Refine iteratively rather than front-loading all exploration before producing anything.

## Working with Claude

**Core principle**: Think deeply, follow TDD strictly, capture learnings while context is fresh.

**Quick reference:**
- ALWAYS FOLLOW TDD — no production code without failing test
- Assess refactoring after every green (but only if adds value)
- Update CLAUDE.md when introducing meaningful changes
- Ask "What do I wish I'd known at the start?" after significant changes
- Document gotchas, patterns, decisions, edge cases while context is fresh

For detailed TDD workflow, load the `tdd` skill.
For refactoring methodology, load the `refactoring` skill.
For detailed guidance on expectations and documentation, load the `expectations` skill.

## Summary

The key is to write clean, testable, functional code that evolves through small, safe increments. Every change should be driven by a test that describes the desired behavior, and the implementation should be the simplest thing that makes that test pass. When in doubt, favor simplicity and readability over cleverness.
