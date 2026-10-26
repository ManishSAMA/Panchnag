# Mobile UI design (Android first, Flutter)

Status: design draft, 2026-10-22, revised 2026-10-26 after the scope review (see [`mobile-app-flutter.md`](mobile-app-flutter.md) §1a). No Flutter code yet. The mockup predates the revision: it still shows the Pachchakkhan card and has no report action. This covers Phase 4 (screens), Phase 5 (Festivals screen) and Phase 6 (Hindi + polish) of [`mobile-app-flutter.md`](mobile-app-flutter.md).

**Clickable mockup:** https://claude.ai/artifact/8JWvZ895oyUo9rqdM2Tix9 (private until you share it from the page's Share menu). The mockup has seven artboards: onboarding, Today, Month, Festivals, Choghadiya, Settings, and the reminder plus share card. Every value in it is real engine output for **Delhi, Thursday 22 Oct 2026**, with the clock fixed at 10:52 (`generate_location_panchang`, `calculate_choghadiya_slots`, `generate_jain_festivals` with the Tapagachchha profile). The mockup is shown in Hindi mode.

---

## 1. Decisions

| Topic | Decision |
|---|---|
| Visual direction | Material 3, traditional-modern: warm paper ground, maroon primary, saffron accent. Ornament is limited to the siddhashila mark (crescent + dot) on the logo, onboarding and the share card. |
| Navigation | Bottom `NavigationBar` with 4 tabs: **आज · माह · पर्व · चौघड़िया**. Settings opens from a gear in each tab's top bar. The location chip on Today also opens Settings. |
| Audience | Mixed, elders included. Body text is at least 16 sp, primary values 19–26 sp, the hero tithi 40 sp. Every touch target is at least 48 dp (44 dp minimum for chips). Nothing relies on swipes alone, and every swipe has a button too. |
| Language | Follows the phone: English if the phone is set to English, otherwise Hindi. It can be changed in onboarding and in Settings. Numerals stay Latin (Hindi digits are a Phase 6 option). |
| Time format | 12-hour with Hindi period words: सुबह / दोपहर / शाम / रात (morning, afternoon, evening, night). English uses AM/PM. |
| Pachchakkhan | **Not shown in the beta.** The engine does not compute these times yet, and an empty "coming soon" card reads as broken to elders. The card returns once the engine function exists. |
| Extras in scope | First-run onboarding, festival reminders (local notifications), sharing a day as an image, and reporting a wrong date. A home-screen widget is **not** designed. |
| Date range | 2016–2040 is a hard limit: date arrows, the Month header and the year chip stop at the edges. |
| Icon | The siddhashila mark (crescent + dot) on maroon. |

## 2. Design tokens

Write these as a `ThemeExtension` plus `ColorScheme.fromSeed` overrides. Dark mode comes in Phase 6, but it should be defined as tokens from day one.

| Token | Light | Use |
|---|---|---|
| `ground` | `#FBF6EE` | Scaffold background |
| `surface` | `#FFFFFF` | Cards, sheets |
| `navSurface` | `#F4ECE0` | Bottom nav |
| `line` | `#E8DCCB` | Card borders, dividers |
| `ink` | `#2B1D14` | Primary text |
| `inkMuted` | `#6E5A4A` | Secondary text (≈6:1 on ground) |
| `primary` | `#8A1C2B` | Hero card, selected states, primary buttons |
| `primaryContainer` | `#F2D3D7` | Nav indicator pill, tonal buttons |
| `accent` | `#E08A2E` | Kalyanak dot, current-slot ring, progress |
| `accentContainer` | `#FCEBD3` / text `#6B3A00` | Ongoing-parva banner |
| `good` | `#2D6236` on `#E3F0E1` | Good choghadiya (अच्छा), vriddhi |
| `neutral` | `#5B4A3C` on `#EEE7DC` | Neutral choghadiya (सामान्य) |
| `avoid` | `#9B2C1F` on `#F8E0DA` | Choghadiya to avoid (टालें), kshaya |
| `vrat` | `#2F6F8F` | Vrat dot/label |

The good, neutral and avoid states never rely on colour alone. Each one also has a glyph (✓ / – / ✕) and a text label.

**Type:** Mukta (400/500/600/700) for UI, since it covers both Devanagari and Latin. Tiro Devanagari Hindi is for display only: the hero tithi, month title and share card. Bundle the fonts as assets because the app is offline, and never fetch them from Google Fonts at runtime. Respect the system `textScaler` up to 1.6× and test layouts at 1.3×.

## 3. Screens

### 0 · Onboarding (first run only)
These are three steps, each with Back and Next (पीछे / आगे) and progress dots:
1. **Language:** हिन्दी / English as large radio cards.
2. **Location:** a "GPS से पता लगाएँ" button (find by GPS), or one of the 11 preset city chips. The copy states that everything is calculated on the phone, offline.
3. **Tradition:** the three Shwetambar profiles (Murtipujak Tapagachchha, Sthanakvasi, Terapanthi). The choice is saved as the profile's string ID, so more traditions can be added later.

"शुरू करें" ("Start") saves the choices and opens Today. Right after this, a one-line prompt asks whether to send crash reports. The default is off, and Settings can change it.

States: GPS permission denied → show an inline message and keep the city chips usable. GPS fix outside India → accept it. A GPS fix takes the phone's current time zone; each preset city carries its own. There is no extra prompt.

### 1 · Today (default tab)
The page scrolls from top to bottom:
1. **Top bar:** location chip (pin + city + ▾), share, gear.
2. **Date row:** ‹ previous day, the full date (weekday, day, month, year), next day ›. When the user is not on today, an "आज" ("Today") chip appears to jump back.
3. **Hero card (primary):** the label "जैन तिथि · {month} मास" (Jain tithi · {month}), the tithi in display type, VNS · VS, then "{end time} तक · फिर {next tithi}" ("until {end time} · then {next tithi}"). A kshaya or vriddhi day adds a chip inside the card.
4. **Ongoing-parva banner:** shown only when a multi-day observance spans today, e.g. Navapad Oli 17–26 Oct. It links to Festivals.
5. **Sun and nakshatra tiles:** sunrise and sunset in a 2-column grid, then a full-width nakshatra tile with pada, end time and the next nakshatra.
6. **Current choghadiya card:** name, nature chip, end time, a progress bar, and "अगला: X · N घं M मि में" ("Next: X · in N h M min"). It links to the Choghadiya tab.
7. **Upcoming festivals:** the next 4 dates, plus "सभी देखें" ("See all").
8. **Report action:** a text button, "गलत लगे तो बताएँ" ("Report if something looks wrong"). See §3.6.

(The Pachchakkhan card is left out of the beta; see §1.)

The Jain tithi is the one at the reference instant (sunrise + 2 h 24 m), matching the engine's `jain_tithi`.

### 2 · Month
- The beta has the Gregorian grid only. A lunar-month view, laid out by tithi like a printed panchang, comes after the beta.
- The header has ‹ month ›, plus a subtitle with the lunar months it spans and VS.
- A 7-column grid starts on Sunday (रवि). Each cell shows the day number, the short Jain tithi (`शु 11`, `कृ 5`, `पूर्णिमा`, `अमावस`), up to 3 category dots, and a corner flag: **क्ष** for kshaya, **वृ** for vriddhi. Today has a maroon ring, and the selected day is filled maroon.
- A legend for the dots and flags sits under the grid.
- **The day bottom sheet** is always docked on Android under the grid. A modal sheet is used only on small screens. It shows the date, the full tithi, and a kshaya/vriddhi explanation. The vriddhi text states the house rule: kalyanaks fall on the first day and vrats on the second (see `plans/vrat-vriddhi-second-day.md`). After that come the festival list, "पूरा दिन खोलें" ("Open full day"), which opens Today at that date, and the report action (§3.6).
- The real October 2026 data in the mockup has kshaya days on the 3rd and 27th and a vriddhi on 18th–19th. It is a good test month.

### 3 · Festivals
- Top row: a profile chip (opens Settings › Tradition) and a year chip (2016–2040).
- Filter chips: सभी (all) · महापर्व (mahaparv) · पर्व (parva) · कल्याणक (kalyanak) · व्रत (vrat). They are single-select, and the selection is remembered.
- The list is grouped by Gregorian month. Each row is one date: a date block with weekday, then the tithi line, then one line per festival with a category label and a **bell toggle** for that festival's reminder. Multi-day observances show a range (e.g. 17–24).
- Search (top bar) works over Hindi and English names.
- Category mapping from the registry: `mahaparv` and `mahaparv_vrat` → महापर्व; `parva` and `parva_vrat` → पर्व; `kalyanak` → कल्याणक; `vrat` → व्रत; `festival` → महापर्व.

### 4 · Choghadiya
- The hero shows the current slot, its time range, a progress bar, and a **live countdown** to the next slot. The countdown ticks every second and updates on resume. Use `aria-live`-style semantics: `Semantics(liveRegion: true)`.
- A segmented control switches between दिन (day) and रात (night).
- There are 8 rows per period: glyph badge, name, nature (अच्छा / सामान्य / टालें, meaning good / neutral / avoid), and time. The current row has an accent ring.
- A footnote explains how slots are built: daytime and night are each split into 8 equal parts.
- The nature labels are deliberately **not** "शुभ/अशुभ" (auspicious/inauspicious), because "शुभ" is also a slot name.

### 5 · Settings
These sections appear in order:
- **Location:** the current location (name, lat/lon, tz), plus a "use current GPS location" action.
- **Tradition:** the 3 profiles as radios.
- **Language:** हिन्दी / English.
- **Month system:** Purnimanta / Amanta.
- **Sunrise rule:** Modern (upper limb + refraction, **the default**) / Traditional (disc centre, no refraction). Help text: Traditional matches the printed Laghu panchang, and the choice can move a festival by a day.
- **Theme:** Light / Dark / System.
- **Reminders:** a master switch, a time (default the evening before at 19:00), and default categories (mahaparv, parva, kalyanak on; vrat off).
- **Crash reports:** a switch, off by default. Help text: only crash details are sent, never your location or settings.
- **About:** offline calculation, the verified range 2016–2040, a note that font size follows the phone, and a link to the privacy policy.

The `clock` setting (standard/daylight) is left out for beta because it only matters outside India. Add it under an "उन्नत" (advanced) section if testers abroad need it.

### 6 · Extras
- **Reminder notification:** one notification per date, even when the date has several festivals. Title: "कल {main festival}" ("Tomorrow: {main festival}"). Body: the date, the tithi and the other festivals. Actions: "देखें" (View) and "इस पर्व की सूचना बंद" (Turn off reminders for this festival). Use `flutter_local_notifications` with **inexact** alarms (`inexactAllowWhileIdle`, which can fire up to about 15 minutes late) scheduled for the next 60 days, rescheduled when settings change and on boot. This needs only `POST_NOTIFICATIONS`, not the exact-alarm permissions that Play restricts. No server is involved.
- **Share card:** a 1080×1350 PNG built from a widget with `RepaintBoundary`, shared through `share_plus`. It contains "जय जिनेन्द्र", date, tithi, VNS · VS, sunrise and sunset, any ongoing parva, and a plain-text footer: city and "Jain Panchang · Play Store". There is no QR code until the store listing has a stable URL.
- **Report a wrong date:** "गलत लगे तो बताएँ" on Today and in the Month day sheet. It opens a share (email or WhatsApp) pre-filled with the date, coordinates, time zone, profile, sunrise rule, app version and engine version. The destination address or number is still open.

## 4. Flutter structure (mobile/app)

```
lib/
  theme/        tokens.dart (ThemeExtension), typography.dart
  l10n/         app_en.arb, app_hi.arb
  features/
    onboarding/ today/ month/ festivals/ choghadiya/ settings/ share/ reminders/
  shared/       date_header.dart, festival_row.dart, nature_badge.dart, tithi_format.dart
```

- Riverpod providers: `settingsProvider` (persisted with `shared_preferences`), `selectedDateProvider`, `dayPanchangProvider(date)`, `monthProvider(year, month)`, `festivalsProvider(year, profile)`, and `nowProvider` (a 1 s stream used only by the Choghadiya hero and the Today card).
- Engine calls run in a background isolate. Results go into a disk cache keyed by (engine version, registry hash, location, profile, sunrise rule, year), which an app update invalidates. The reminder scheduler reads the same cache.
- Formatting lives in pure functions so plain unit tests can cover it: `tithiShort`, `tithiFull`, `hindiTime` (period word + 12 h), `durationUntil`, `natureOf(slot)`. Widgets only lay the results out.
- Navigation: `go_router` with a `StatefulShellRoute` for the 4 tabs, plus `/settings`, `/onboarding`, and `/day/:date` deep links. Notifications open `/day/:date`.

## 5. Tests that drive the build (TDD)

Write widget tests against real engine types, with no mocked engine. Use a fixed date and city so that tests can assert behaviour without golden numbers.

- Today shows the Jain tithi at the reference instant, not the sunrise tithi, on a day where the two differ.
- Today shows the ongoing-parva banner on each day inside a multi-day observance, and only on those days.
- In the Month grid, a cell carries the kshaya flag exactly when the Jain tithi index skips, and the vriddhi flag on both days of a repeat.
- In the Month sheet, a vriddhi day shows the first-day/second-day rule text that matches the day.
- In Festivals, each filter chip shows only its categories, and the "all" filter shows the union.
- Toggling a festival's bell schedules or cancels exactly one notification for that date.
- Date navigation cannot go before 1 Jan 2016 or after 31 Dec 2040: the arrows are disabled at the edges.
- The report action's text contains every context field (date, coordinates, time zone, profile, sunrise rule, app and engine versions).
- In Choghadiya, exactly one slot is current at any instant from sunrise to the next sunrise, and the countdown reaches 0 at the next slot's start.
- Settings: changing the profile, sunrise rule or month system changes festival dates or month names, and the choice persists across restarts.
- Accessibility: every tappable widget is at least 48×48 dp, there are no clipped texts at a text scale of 1.3, and each icon-only button has a semantics label.

## 6. Data gaps found while designing

1. **Kalyanak entries mostly have no Hindi names.** Only 3 of the 138 `kalyanak` rows in `shared/festival_registry.json` have a `name_hindi`. The mockup's Hindi kalyanak names were written by hand. Generate them as "श्री {tirthankar} जी — {च्यवन/जन्म/दीक्षा(तप)/केवलज्ञान/मोक्ष} कल्याणक", where the parts are the tirthankar and the kalyanak (conception/birth/initiation (austerity)/omniscience/liberation). Do this in the registry, not in the app's ARB files. **Scheduled** before the festival port; all Hindi is reviewed by the maintainer plus one sangh elder before the closed beta.
2. **Shri Neminath Ji – Omniscience Kalyanak appears twice in Oct 2026** for Tapagachchha, on 11 Oct (Ashwin S1) and 20 Oct (Ashwin S9). Check whether this is a school variant that should be filtered out or a registry duplicate. **Scheduled** before the festival port; the finding goes to the maintainer to decide.
3. **Pachchakkhan times** need an engine function before the Today card can come back (post-beta).
4. **Choghadiya nature labels** in Hindi (अच्छा / सामान्य / टालें) are new strings. The engine's `nature` field stays English.

## 7. Open questions

Settled 2026-10-26: Month is the Gregorian grid only in the beta; the share card has a text footer with no QR code; the icon uses the siddhashila mark.

- Where wrong-date reports go: an email address and a WhatsApp number.
