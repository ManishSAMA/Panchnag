# Jain Panchang Mobile App — Flutter + Pure-Dart Engine

**Status:** Approved direction; Phases 0–1 done, Phase 2 at M2. Scope and release decisions settled in review on 2026-10-26 (§1a).
**Supersedes:** [`mobile_app_conversion_plan.md`](mobile_app_conversion_plan.md) (precomputed-SQLite approach)
**Date:** 2026-10-07

---

## 1. Decisions (locked)

| Topic | Decision | Why |
|---|---|---|
| Platforms | One Flutter codebase. **The beta is Android only**; iOS builds start once the Android beta is stable. | Avoids Apple fees, signing without a Mac, and iOS notification quirks until the app itself is proven. The code stays iOS-ready. |
| Engine | **Pure-Dart astronomy written from published algorithms** (Meeus, VSOP87 / ELP2000 truncations), permissive license | Swiss Ephemeris is AGPL. Embedding it would force the whole app to be AGPL open source, and the iOS App Store's terms are widely considered incompatible with GPL-family licenses. Writing our own code avoids both. |
| Reference engine | Existing `python_engine` (Swiss Ephemeris) stays on the dev machine as the **test reference** | It is already corrected against the physical panchang (e.g. the 15-day Maha offset fix). It never ships inside the app. |
| Data | Calculated on the phone, fully offline, **any GPS location** | No city packs, no server, no network clause |
| Date range | 2016-01-01 → 2040-12-31 | Supported and fully checked against Python |
| Preset cities | Delhi, Ahmedabad, Mumbai, Surat, Palitana, Jaipur, Udaipur, Indore, Kolkata, Bengaluru, Chennai | Quick-pick list in the app, and the core of the parity tests |
| Beta scope | Today, Month grid, Choghadiya, Festivals (all 3 Shwetambar profiles), Settings; English + Hindi | Same as the earlier plan's §1 |
| Deferred | Karana, Yoga, Hora, Rahu Kaal, Dainika Muhurta, PDF export, audio, vow trackers, accounts | Post-beta |
| Repo layout | Same repo, new `mobile/` folder next to `python_engine/` | One CI run compares the two engines |
| iOS builds (after the beta) | Cloud macOS (Codemagic or GitHub Actions macOS runner); a friend's Mac only for occasional Simulator checks | No Mac owned |

---

## 1a. Decisions from the 2026-10-26 review

### Product
| Topic | Decision |
|---|---|
| Name and ID | Display name **Jain Panchang** / **जैन पंचांग**. Package `io.github.manishsama.jainpanchang`; it can never change after the first Play upload. |
| Traditions | The three Shwetambar profiles only. The profile is stored as an open string ID, not a fixed enum, so Digambar can be added later without a migration. |
| Price | Free, with no ads, accounts or analytics. A one-page privacy policy. |
| Date range | A hard limit of 2016–2040 in every picker, arrow and year chip. Widen it later by regenerating the fixtures. |
| Minimum Android | Flutter's default `minSdk`. Test on the oldest phone a tester owns. |
| Default settings | Modern sunrise rule (matches the web app and engine), Purnimanta month. Sangh testers are asked to compare both sunrise rules. |
| Icon | The siddhashila mark (crescent + dot) on maroon. |

### Architecture
| Topic | Decision |
|---|---|
| Backend | None. Calculation is fully offline. The only network use is Sentry crash reporting, **off by default**, switched on in Settings or from a one-line prompt on first launch, and wired in Phase 7 only. Data bugs are fixed by shipping app updates. |
| Source of truth | The Python engine stays canonical. A rule change lands in Python first, then the fixtures are regenerated, then Dart must pass parity again. Revisit after launch. |
| Festival location | Festivals use the sunrise at the **user's** location, as the engine and parity fixtures already do. Sangh testers are asked specifically about this. |
| Time zone | A GPS fix uses the phone's time zone; each preset city carries its own. No coordinate-to-time-zone lookup in the beta. |
| Computation | On demand in a background isolate, plus a disk cache keyed by (engine version, registry hash, location, profile, sunrise rule, year). An app update invalidates it. |
| Reminders | Inexact alarms (`inexactAllowWhileIdle`), so no exact-alarm permission is needed. A rolling 60-day schedule, rescheduled when settings change and after a reboot. |
| Festival port | A Dart **interpreter** for the rule types declared in `festival_registry.json`, not a line-by-line port. Phase 5 starts with an audit of which registry rules are pure data and which are special-case code; only the special cases are ported by hand. |

### Build order
1. **Python and CI first:**
   - GitHub Actions on Linux with three jobs on every push: `pytest tests` (including the registry freshness test), `dart test` with the full core parity suite, and `flutter analyze` + `flutter test`. `tests_ui` and fixture regeneration stay local.
   - A fixture freshness test: `manifest.json` records a hash of the Python engine sources the fixtures depend on, and a Python test fails when it is stale.
   - `generate_jain_festivals` raises on an unknown profile; Dart rejects unknown profiles from the start.
   - Generate the missing Hindi kalyanak names in `registry.py`, and investigate the duplicate Neminath omniscience kalyanak (see [`mobile-ui-design.md`](mobile-ui-design.md) §6).
2. Engine M3, then M4 ([`mobile-phase2-dart-engine.md`](mobile-phase2-dart-engine.md)).
3. Phase 3: a Today-only app on the Play **internal** track.
4. After that, alternate one screen with one festival rule type, so that neither blocks the other for weeks.
5. Hindi review, then the sangh closed beta. The closed beta waits for full festival (L4) parity.

### Release
| Topic | Decision |
|---|---|
| Play account | Personal ($25). The sangh closed beta doubles as the rule for new personal accounts (currently 12 testers for 14 days); re-check the numbers at Phase 7. |
| Signing | Play App Signing. The upload keystore and its password live in a password manager plus one offline backup, never in the repo. Release builds are uploaded by hand; CI never signs. |
| Repo | Private through the beta. Decide on open source after launch. |
| Wrong-date reports | Every day view has a "गलत लगे तो बताएँ" ("Report if something looks wrong") action. It opens an email or WhatsApp share pre-filled with date, coordinates, time zone, profile, sunrise rule, app version and engine version. The destination address or number is still to be chosen. |
| Hindi review | Every Hindi string (ARB files and registry names) is checked by the maintainer plus one sangh elder before the closed beta. |

### Launch gate (closed beta → production)
- At least 14 days of closed testing with 12 or more testers.
- No open wrong-date reports: each is fixed, or confirmed as a boundary case against a physical panchang.
- A crash-free session rate of 99% or more.
- Today renders in under 100 ms on the slowest tester phone.
- The full parity suite passes in CI on the release commit.

### Revisit after the beta
Festival dates against a fixed reference city · the default sunrise rule · offline time-zone lookup from coordinates · over-the-air registry updates · open source · iOS.

---

## 2. Architecture

```
Jain_Panchang/
├── python_engine/                  # existing — reference engine
│   └── scripts/export_parity_fixtures.py   # NEW: writes fixtures for Dart tests
├── shared/
│   └── festival_registry.json      # NEW: single source for the 215 festival definitions
└── mobile/
    ├── packages/panchang_engine/   # pure Dart, NO Flutter dependency → `dart test`
    │   ├── lib/src/astro/          # Julian day, Sun, Moon, ayanamsa, rise/set
    │   ├── lib/src/panchang/       # tithi, nakshatra, month, samvat, choghadiya
    │   ├── lib/src/festivals/      # rule types ported from festival_rules.py
    │   └── test/fixtures/          # generated by the Python exporter (gzip JSON)
    └── app/                        # Flutter UI (Riverpod, freezed, intl ARB en/hi)
```

**Rules**
- `panchang_engine` is a separate package with no Flutter dependency. It can be tested in seconds with `dart test`, and the UI cannot reach into its internals.
- **There is one copy of the festival definitions.** `registry.py` is generated into `shared/festival_registry.json`. A Python test checks the two are identical, so they can't drift. Dart loads the JSON as an asset. Later, Python can load from the JSON too, making it the only copy.
- Only *logic* is ported to Dart (`festival_rules.py`, about 5.4k lines). The *data* is shared.
- **Time zones:** Dart's `DateTime` has no IANA time-zone support. Use the `timezone` package with its bundled tz database, because GPS locations outside India must work.

---

## 3. Parity strategy: how Dart is shown to match Python

The Python exporter writes fixtures for **every day 2016–2040 × 11 preset cities**, plus a few edge locations: high latitude (London) and the western hemisphere (New York), to catch time-zone and date-line bugs. That's about 100k rows, a few MB gzipped. The fixtures are used in tests only and never shipped in the app.

| Layer | What is compared | Tolerance |
|---|---|---|
| L1 Astronomy | Sidereal Sun and Moon longitude at sample instants; Lahiri ayanamsa; sunrise and sunset | Sun ≤ 5″, Moon ≤ 15″, ayanamsa ≤ 1″, rise/set ≤ 10 s |
| L2 Times | Tithi and nakshatra end instants, Sankranti instants | ≤ 60 s |
| L3 Labels | Sunrise tithi, Jain tithi (sunrise + 2h24m), paksha, Purnimanta month, Adhik/Kshaya month, VS, VNS, Kshaya/Vriddhi tithi, choghadiya slots | **Exact** |
| L4 Festivals | Date of each festival for each profile and year | **Exact** |

**Boundary rule:** a label (L3/L4) is allowed to differ **only** when Python's transition falls within the L2 tolerance of the reference instant. In that case the case is written to a `boundary_cases` report for a person to check against a physical panchang. It is never silently ignored. Everything else must match exactly, and CI fails otherwise.

This meets the CLAUDE.md rule: we check limits and agreement with the reference rather than hard-coding single numbers. Real-world dates (Paryushan, Kshaya years, Adhik Maas) stay as cited golden tests in both suites.

---

## 4. Phases

Each phase ends in a working, tested state. TDD throughout: Python with pytest, Dart with `dart test` / `flutter test`.

### Phase 0: Tooling + accuracy spike (go/no-go gate)

> **Progress (2026-10-07):**
> - Flutter 3.47.6 / Dart 3.13.5 installed at `C:\dev\flutter`.
> - **Accuracy spike: GO.** Every check is 10–300× inside tolerance. See [`mobile/spikes/astro_accuracy/REPORT.md`](../../../mobile/spikes/astro_accuracy/REPORT.md).
>
> **Progress (2026-10-21): Phase 0 complete.**
> - Android Studio, SDK 36/37, cmdline-tools 23, NDK 28.2.13676358 installed. `flutter doctor` is green for Android.
> - `mobile/spikes/hello_panchang` built (`flutter build apk --debug`), installed and ran on the `Medium_Phone_API_37.0` emulator.
>
> **Setup gotchas:**
> - The emulator only boots reliably with `-gpu swiftshader_indirect`. The default GPU mode died with "UpdateLayeredWindowIndirect failed".
> - Gradle could not auto-install the NDK. Install it manually with `android.exe --sdk=<sdk> sdk install ndk/28.2.13676358`.
> - `sdkmanager.bat` is deprecated and splits `;` package names. Use the new `cmdline-tools\latest\bin\android.exe sdk …`.
> - Physical-phone run deferred: the emulator is enough until performance testing in Phase 2.

- Install the Flutter SDK, Android Studio (SDK and emulator), and VS Code with the Flutter extension. Get `flutter run` working on your Android phone.
- Spike: pure-Dart Sun, Moon, Lahiri ayanamsa and sunrise for 2016–2040 at 2–3 cities, compared with a quick Python dump.
- **Go/no-go gate:** if the Moon and tithi-time error can't get within L1/L2 tolerances, stop and re-decide the engine (§1) before building anything else.

### Phase 1: Python fixture exporter

> **Progress (2026-10-21): Phase 1 complete.** See [`mobile-phase1-fixtures.md`](mobile-phase1-fixtures.md).
> - The core fixture set is committed under `mobile/packages/panchang_engine/test/fixtures/core/`.
> - `shared/festival_registry.json` is committed (207 festivals).
- `scripts/export_parity_fixtures.py`, written test-first: its schema, determinism, and coverage of all days and cities.
- Generate `shared/festival_registry.json`, with a freshness test.

### Phase 2: Dart engine core (L1–L3)
- Order: Julian day / time → Sun → Moon → ayanamsa → rise/set → tithi and nakshatra instants → sunrise and Jain tithi → Purnimanta month, Adhik/Kshaya → VS/VNS → Kshaya/Vriddhi → choghadiya.
- Each step turns its parity layer green before the next starts.

### Phase 3: First working app on the Play internal track
- The Today screen shows the real engine output for a preset city, plain styling.
- Android: a signed build on the Play Console **internal testing** track.
- iOS is after the beta (§1a). When it starts: a cloud build uploaded to **TestFlight**. Codemagic can manage signing with an App Store Connect API key, so no Mac is needed.
- CI is already in place by now (§1a build order, step 1).

### Phase 4: Screens, one at a time
- Order: Today (full) → Month grid with day bottom sheet → Choghadiya with live countdown → Settings (location by GPS or preset, profile, language, Purnimanta/Amanta).
- For each screen: paper sketch, then widget tests, then build, then use it on the phone for a few days.
- UI design, tokens and the clickable mockup: [`mobile-ui-design.md`](mobile-ui-design.md).

### Phase 5: Festival engine port (L4), the largest phase
- First, audit which registry rules are pure data and which need special-case code (§1a).
- Build the registry interpreter one rule type at a time, hand-porting only the special cases. Each rule type is done when its L4 parity passes for all 3 profiles across 2016–2040.
- Interleaved with Phase 4 screens rather than run after them (§1a build order).
- Then the Festivals screen: list, filter chips, profile selector.

### Phase 6: Hindi + polish
- ARB strings, reusing the Hindi names from the registry and `hindi_observance_map.py`.
- Dark mode, accessibility (font scaling), and Hindi digits if wanted.

### Phase 7: Beta
- Play Console **closed testing**. New personal developer accounts must meet a minimum-tester / minimum-days rule before production; check the current numbers when we get here.
- Opt-in Sentry crash reporting (§1a).
- Testers come from the sangh, since they spot a wrong tithi immediately.
- Production only after the launch gate in §1a is met.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| Our own Moon theory isn't accurate enough near tithi boundaries | Phase 0 go/no-go gate; boundary report; sweph + AGPL open-source app as the fallback |
| Porting the festival rules brings back old bugs | Exact L4 parity over 25 years × 3 profiles; port one rule type at a time |
| Python and Dart drift apart after launch | Shared registry JSON; parity suite in CI; fixture source-hash freshness test; any Python fix must regenerate fixtures and leave Dart green |
| Users see a festival on a different day than their printed panchang | Festivals follow the user's own sunrise; sangh testers check this specifically; a reference-city comparison is on the revisit list |
| Time-zone or date-line bugs outside India | Edge-location fixtures; `timezone` package; tests use UTC instants only |
| iOS signing without a Mac | Codemagic automatic signing; friend's Mac as backup |
| Store rules change | Re-check Play and App Store requirements at Phase 3 and Phase 7 |

---

## 6. Accounts and costs
- Google Play Console: one-time $25 (personal account).
- GitHub Actions: the private repo's free monthly minutes, Linux runners only.
- After the beta, for iOS: Apple Developer Program $99 per year, and the Codemagic free tier or GitHub Actions macOS minutes.

---

## 7. Open items
- Settled 2026-10-26: app name, icon and package ID (§1a). Open source is deferred until after launch.
- Where wrong-date reports go: an email address and a WhatsApp number.
- How the Purnimanta/Amanta setting affects festival naming, matching the web app's current behaviour.
