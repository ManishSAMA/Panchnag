# Mobile UI design (Android first, Flutter)

Status: **final design**, 2026-10-27. Earlier drafts were 2026-10-22 and 2026-10-26 (scope review, see [`mobile-app-flutter.md`](mobile-app-flutter.md) §1a). On 2026-10-27 pachchakkhan moved into the beta, and the look was redone in the **Navpad Colours** direction, chosen from a direction round. No Flutter code yet. This covers Phase 4 (screens), Phase 5 (Festivals screen) and Phase 6 (Hindi + polish) of [`mobile-app-flutter.md`](mobile-app-flutter.md). The design system's own record (tokens and rules) is the repo-root `DESIGN.md`.

**Clickable mockup:** https://claude.ai/artifact/8JWvZ895oyUo9rqdM2Tix9 (private until you share it from the page's Share menu). It has 13 artboards:
- Row 1: onboarding, Today, Month, Pachchakkhan, Festivals, Choghadiya, Settings.
- Row 2: Today in dark theme, Today at 1.3× text, a vriddhi day, a tithi-boundary day, and the reminder plus share card.
- Row 3: the errors and limits states.

Every value in it is real engine output for **Delhi**: Thursday 22 Oct 2026 with the clock fixed at 10:52, plus 19 Oct 2026, 27 Nov 2026 and 31 Dec 2040 for the state boards. The sources are `generate_location_panchang`, `calculate_choghadiya_slots`, and `generate_jain_festivals` with the Tapagachchha profile. The mockup is shown in Hindi mode.

---

## 1. Decisions

| Topic | Decision |
|---|---|
| Visual direction | **Navpad Colours** (chosen 2026-10-27 over "Upashraya Board", "The Day Line" and plain Material 3). The Siddhachakra's five colours are the app's only colour language, and each has exactly one job: white is the ground, navy is ink plus tithi and choghadiya, red is parva and kalyanak, yellow is pachchakkhan now/next, and green is vrat. Colour appears as solid full-bleed **bands** on Today, filled rows, or small marks in lists. It is never decorative. Material 3 governs structure and components. Brand palette only, with no Material You dynamic colour. This replaces the 2026-10-22 maroon/saffron look. |
| Navigation | Bottom `NavigationBar` with 4 tabs: **आज · माह · पच्चक्खाण · पर्व** (Today · Month · Pachchakkhan · Festivals). Choghadiya is a full screen opened from its navy band on Today. Settings opens from a gear in each tab's top bar, and the location chip on Today opens it too. (Changed 2026-10-27, when pachchakkhan moved into beta; see `mobile-market-screens.md`.) |
| Audience | Mixed, elders included. Body text is at least 16 sp, primary values 19–26 sp, the hero tithi 40 sp. Every touch target is at least 48 dp (44 dp minimum for chips). Nothing relies on swipes alone, and every swipe has a button too. |
| Language | Follows the phone: English if the phone is set to English, otherwise Hindi. It can be changed in onboarding and in Settings. Numerals stay Latin (Hindi digits are a Phase 6 option). Gujarati is **out of scope** (decided 2026-10-27). |
| Time format | 12-hour with Hindi period words: सुबह / दोपहर / शाम / रात (morning, afternoon, evening, night). English uses AM/PM. |
| Pachchakkhan | **In the beta**, with its own tab and a yellow band plus a times list on Today (decided 2026-10-27, after market research showed every major Jain app has it; this reverses the 2026-10-26 "not in beta" call). The times are calculated in Dart only, from sunrise and sunset; see §3 · Pachchakkhan. There is never an empty "coming soon" placeholder. |
| Extras in scope | First-run onboarding, festival reminders (local notifications), sharing a day as an image, and reporting a wrong date. A home-screen widget is **not** designed. |
| Date range | 2016–2040 is a hard limit: date arrows, the Month header and the year chip stop at the edges. |
| Icon | To be designed in the Navpad language: a white mark on navy. The siddhashila mark (crescent + dot) is still the candidate. |

## 2. Design tokens

Write these as a `ThemeExtension` (the Navpad roles) plus a hand-built `ColorScheme` (no `fromSeed`, no dynamic colour). Dark mode is **in the beta** as a first-class scheme. Full rules are in the repo-root `DESIGN.md`.

| Token | Light | Dark | Use |
|---|---|---|---|
| `ground` | `#FFFFFF` | `#0E131E` | Scaffold |
| `surface` | `#F4F5F8` | `#161D2B` | Nav bar, notes, docked sheet |
| `hair` | `#E1E4EB` | `#283044` | 1 px dividers. Lists are hairline rows, never cards. |
| `ink` | `#1F2A44` | `#ECEEF3` | Primary text |
| `ink2` | `#4A5570` | `#B0B7C8` | Secondary text |
| `ink3` | `#646D82` | `#8F98AC` | Past/done times, outlines |
| `navy` / `onNavy` | `#1F2A44` / `#FFF` | `#2A3A60` / `#FFF` | Ink, choghadiya band, current choghadiya row, filled button, today ring |
| `red` / `onRed` | `#B3261E` / `#FFF` | `#C0362C` / `#FFF` | Parva and kalyanak: ongoing-parva band, mahaparva rows, red marks |
| `yellow` / `onYellow` | `#E9B44C` / `#1F2A44` | `#D4A03F` / `#1F2A44` | **Only** the next pachchakkhan, and only on today |
| `green` / `onGreen` | `#2E7D4F` / `#FFF` | `#2B7A4C` / `#FFF` | Vrat band and marks |
| `pill` | `#DDE2EE` | `#2E3A57` | Nav indicator and every selection (filter chip and segment with a ✓, selected Month day), per Material 3 |

List marks: a filled red dot is parva, a red ring is kalyanak, a red square is mahaparva, and a filled green dot is vrat.

Choghadiya quality (अच्छा / सामान्य / टालें) is **not** coloured, because red and green already have jobs. It is shown by glyph (✓ / – / ✕), label and weight: good slots are bold.

Kshaya and vriddhi are flagged with ink letters **क्ष** / **वृ** plus a note, never with colour.

**Type:** Mukta (400/500/600/700) for UI, since it covers both Devanagari and Latin. Tiro Devanagari Hindi is for display only: the hero tithi (44 sp), the Pachchakkhan and Choghadiya hero names (36 sp), the month title, Festivals month and date headings, and the share card. Every number is tabular and sits in one right-aligned time column. Bundle the fonts as assets because the app is offline, and never fetch them from Google Fonts at runtime. Respect the system `textScaler` up to 1.6× and test layouts at 1.3×; the mockup has a 1.3× Today board.

**Motion:** there is one signature moment. When a time passes, the yellow band advances in place with a 200 ms cross-fade. Tapping a band grows it into the next screen's header (a Material container transform). With "Remove animations" on, both are instant.

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
3. **Hero (no card, no label above it):** the tithi in 44 sp display type. Under it: "**{month}** · {end time} तक, फिर {next tithi}" ("{month} · until {end time}, then {next tithi}"), then VNS · VS.
4. **Notes (only when needed):** a hairline note box under the hero.
   - **Vriddhi:** "वृद्धि तिथि · पहला/दूसरा दिन" ("vriddhi tithi · first/second day"), stating the house rule (vrats on the second day, kalyanaks on the first).
   - **Kshaya:** names the skipped tithi.
   - **Boundary:** shown when the tithi change falls within 45 min of the reference instant. It reads "तिथि बदलने का समय पास है" ("the tithi changes close to the reference time"), gives both times, and has the report action inline. The 45-minute threshold is a proposal; tie it to the parity L2 tolerance once that is fixed.
5. **The four bands**, full-bleed, 58 dp, in a fixed order. Each appears only when it has content, and each opens its screen:
   - **red:** ongoing or today's parva, e.g. Navapad Oli · day 6, completes 26 Oct. Opens Festivals.
   - **yellow:** the next pachchakkhan with its time and countdown. Today only. Opens Pachchakkhan.
   - **green:** today's vrat, or the next vrat with its date. Opens Festivals.
   - **navy:** the current choghadiya with its quality, the next slot and its end time. Opens Choghadiya.
6. **आज का समय** ("Today's times"): hairline rows for sunrise, sunset and nakshatra (with pada, end time and the next nakshatra).
7. **पच्चक्खाण** ("Pachchakkhan"): all six times as rows.
   - Past times are muted and ticked.
   - The next one is a yellow row.
   - The section links to the Pachchakkhan tab.
8. **Upcoming festivals:** the next 4 dates, plus "सभी पर्व" ("All festivals").
9. **Report action:** a text button, "गलत लगे तो बताएँ" ("Report if something looks wrong"). See §3 · Extras.

On any date other than today, the yellow band and yellow row are not shown. Past and future days have no "next".

**Built 2026-10-31 (festival display decisions):** the ongoing-parva banner became DESIGN.md's red band, shown for any parva, kalyanak or mahaparva on the date shown (single-day or span), with a green band for vrats; each names its first festival, adds "+N और" for the rest, shows a span's dates and opens Month on that date. The upcoming list skips vrats, which fall on nearly every date, and has no "सभी देखें" link until the Festivals tab exists. Every vrat category goes green in the marks, including `parva_vrat` and `mahaparv_vrat` (Navapad Oli, the Namokar chain), so the mahaparva square stays rare; the Festivals filter chips may still group them as the category mapping below says.

The Jain tithi is the one at the reference instant (sunrise + 2 h 24 m), matching the engine's `jain_tithi`.

### 2 · Month
- The beta has the Gregorian grid only. A lunar-month view, laid out by tithi like a printed panchang, comes after the beta.
- The header has ‹ month ›, plus a subtitle with the lunar months it spans and VS.
- A 7-column grid starts on Sunday (रवि). Each cell shows the day number, the short Jain tithi (`शु 11`, `कृ 5`, `पूर्णिमा`, `अमावस`), up to 3 category dots, and a corner flag: **क्ष** for kshaya, **वृ** for vriddhi. The grid is hairline cells, not cards. Today has a 2 dp navy inset ring, and the selected day is filled with the `pill` tint. Dots follow the list marks in §2.
- A legend for the dots and flags sits under the grid.
- **The day bottom sheet** is always docked on Android under the grid. A modal sheet is used only on small screens. It shows the date, the full tithi, and a kshaya/vriddhi explanation. The vriddhi text states the house rule: kalyanaks fall on the first day and vrats on the second (see `plans/vrat-vriddhi-second-day.md`). After that come the festival list, "पूरा दिन खोलें" ("Open full day"), which opens Today at that date, and the report action (§3.6).
- The real October 2026 data in the mockup has kshaya days on the 3rd and 27th and a vriddhi on 18th–19th. It is a good test month.

### 3 · Pachchakkhan (tab)
- The header has ‹ date › and a subtitle with the city, sunrise and sunset.
- **Hero:** the yellow band grown into a 132 dp header. It shows the next pachchakkhan in display type, "अगला पच्चक्खाण · {time} के बाद पार सकते हैं" ("next pachchakkhan · can be completed after {time}"), and a live countdown on the right. When no pachchakkhan is left today (after sunset), the hero becomes a quiet ink row: "आज के सभी समय हो गए · कल नवकारसी {time}" ("all of today's times are done · Navkarsi tomorrow at {time}"). On any date other than today there is no hero and no yellow.
- Rows: the done rows are muted with a ✓, the next row is yellow, and the remaining rows are plain. The state is carried by glyph and colour, and the row's semantics label says हो गया / अगला / बाकी (done / next / remaining).
- **Completion times** ("पारने का समय", meaning these may be completed *after* the time). Each row shows the name, its rule and the time.

  | Pachchakkhan | Rule |
  |---|---|
  | नवकारसी (Navkarsi) | sunrise + 48 min |
  | पोरसी (Porsi) | sunrise + ¼ day |
  | साढ़-पोरसी (Sadh-Porsi) | sunrise + ⅜ day |
  | पुरिमड्ढ (Purimaddh) | sunrise + ½ day |
  | अवड्ढ (Avaddh) | sunrise + ¾ day |

  "Day" here is the time from sunrise to sunset.
- **Evening** (these must be done *before* the time): चौविहार · तिविहार · दुविहार (Chauvihar · Tivihar · Duvihar). All three share one time, sunset.
- **Other** (no clock time):
  - मुट्ठीसहियं (Mutthi-sahiyam): no fixed time.
  - एकासणा · बियासणा (Ekasanu · Biyasanu): paired with one of the timed pachchakkhans above, so they get no time of their own.
  - आयंबिल · उपवास (Ayambil · Upvas): show the next day's Navkarsi as the parana time.
- **Rounding:** completion times round **up** to the minute and the evening time rounds **down**, so the app never shows a time that is early or late.
- **Sunrise rule:** follows the Settings sunrise rule (modern/traditional), so this tab always agrees with Today.
- **Same rules for all three profiles.** If a samuday turns out to differ, it becomes a profile parameter later.
- In the mockup (Delhi, 22 Oct 2026, sunrise 06:26:12, sunset 17:44:41), Porsi, Sadh-Porsi, Purimaddh and Avaddh fall within 1 s of choghadiya boundaries 2, 3, 4 and 6. That is expected, since both divide the same day into fractions, and it makes a useful cross-check.

### 4 · Festivals
- Top row: a profile chip (opens Settings › Tradition) and a year chip (2016–2040).
- Filter chips: सभी (all) · महापर्व (mahaparv) · पर्व (parva) · कल्याणक (kalyanak) · व्रत (vrat). They are single-select, sit on one horizontally scrolling row (so they survive 1.3× text), and the selection is remembered.
- The list is grouped by Gregorian month. Each row is one date: a date block with weekday, then the tithi line, then one line per festival with a category label and a **bell toggle** for that festival's reminder. Multi-day observances show a range (e.g. 17–24). Each festival line starts with its mark from §2. A **mahaparva line is a filled red row**, so the big days stand out when scrolling. The selected filter chip uses the `pill` tint and a ✓.
- Search (top bar) works over Hindi and English names.
- Category mapping from the registry: `mahaparv` and `mahaparv_vrat` → महापर्व; `parva` and `parva_vrat` → पर्व; `kalyanak` → कल्याणक; `vrat` → व्रत; `festival` → महापर्व.

### 5 · Choghadiya (full screen, opened from Today; it has a back arrow and no tab)
- The hero is a navy band (it is the Today band grown into the header): the current slot in display type, its quality and time range, and a **live countdown** to the next slot. The countdown ticks every second and updates on resume. Use `aria-live`-style semantics: `Semantics(liveRegion: true)`.
- A segmented control switches between दिन (day) and रात (night).
- There are 8 rows per period: name, glyph and nature (अच्छा / सामान्य / टालें, meaning good / neutral / avoid), and time. The current row is filled navy (navy is choghadiya's colour).
- A footnote explains how slots are built: daytime and night are each split into 8 equal parts.
- The nature labels are deliberately **not** "शुभ/अशुभ" (auspicious/inauspicious), because "शुभ" is also a slot name.

### 6 · Settings
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

### 7 · Extras
- **Reminder notification:** one notification per date, even when the date has several festivals. Title: "कल {main festival}" ("Tomorrow: {main festival}"). Body: the date, the tithi and the other festivals. Actions: "देखें" (View) and "इस पर्व की सूचना बंद" (Turn off reminders for this festival). Use `flutter_local_notifications` with **inexact** alarms (`inexactAllowWhileIdle`, which can fire up to about 15 minutes late) scheduled for the next 60 days, rescheduled when settings change and on boot. This needs only `POST_NOTIFICATIONS`, not the exact-alarm permissions that Play restricts. No server is involved.
- **Share card:** a 1080×1350 PNG built from a widget with `RepaintBoundary`, shared through `share_plus`. It contains "जय जिनेन्द्र", date, tithi, VNS · VS, sunrise and sunset, any ongoing parva, and a plain-text footer: city and "Jain Panchang · Play Store". There is no QR code until the store listing has a stable URL. **Built 2026-11-01:** the footer is the city and "जैन पंचांग" / "Jain Panchang" only, until the store listing exists. The card also has the tithi's end time and Today's green vrat strip, and the greeting stays in Devanagari on the English card. A busy day makes the card taller than 1350 px; it never gets wider. The caption text is sent along with the image.
- **Report a wrong date:** "गलत लगे तो बताएँ" on Today and in the Month day sheet. It opens a share (email or WhatsApp) pre-filled with the date, coordinates, time zone, profile, sunrise rule, app version and engine version. The destination address or number is still open.

### 8 · Errors and limits (mockup board 8)
- **GPS denied** (onboarding step 2 and Settings): a note, "स्थान की अनुमति नहीं मिली" ("location permission was not given"), replaces the GPS button, and the city chips stay usable. There is no dead end and no repeated system prompt.
- **Date limit, 1 Jan 2016 / 31 Dec 2040:** the arrow at the limit is disabled, and a note, "ऐप की आख़िरी तारीख़" ("the app's last date"), explains the verified range. It offers "आज पर लौटें" ("back to today"). The Month header and the year chip stop at the same limits.
- **Notifications denied** (Android 13+ `POST_NOTIFICATIONS`):
  - The Settings › Reminders section shows a note and a filled "फ़ोन की सेटिंग खोलें" ("open phone settings") button.
  - The switch is disabled until permission is granted.
  - The bells in Festivals are inert, and tapping one shows a snackbar with the same action.
- **Empty filter:** a centred empty state, "इस चुनाव में कुछ नहीं" ("nothing for this selection"), with "सभी पर्व दिखाएँ" ("show all festivals") and a link to change the tradition.
- **Large text:** at 1.3× every row grows in height, and nothing truncates. Band right-hand text never wraps; at 1.6× the band stacks the time under the title.

## 4. Flutter structure (mobile/app)

```
lib/
  theme/        tokens.dart (ThemeExtension), typography.dart
  l10n/         app_en.arb, app_hi.arb
  features/
    onboarding/ today/ month/ pachchakkhan/ festivals/ choghadiya/ settings/ share/ reminders/
  shared/       date_header.dart, festival_row.dart, nature_badge.dart, tithi_format.dart
```

- Riverpod providers: `settingsProvider` (persisted with `shared_preferences`), `selectedDateProvider`, `dayPanchangProvider(date)`, `monthProvider(year, month)`, `festivalsProvider(year, profile)`, and `nowProvider` (a 1 s stream used only by the Choghadiya and Pachchakkhan heroes and the Today bands).
- Engine calls run in a background isolate. Results go into a disk cache keyed by (engine version, registry hash, location, profile, sunrise rule, year), which an app update invalidates. The reminder scheduler reads the same cache.
- Formatting lives in pure functions so plain unit tests can cover it: `tithiShort`, `tithiFull`, `hindiTime` (period word + 12 h), `durationUntil`, `natureOf(slot)`. Widgets only lay the results out.
- Pachchakkhan: put a pure function, `pachchakkhanTimes(sunrise, sunset, nextSunrise)`, in `panchang_engine` (Dart only, with no Python reference). It returns instants. The rounding rules (up for completion times, down for the evening time) live in the formatter, not in the engine.
- Navigation: `go_router` with a `StatefulShellRoute` for the 4 tabs, plus `/choghadiya`, `/settings`, `/onboarding`, and `/day/:date` deep links. Notifications open `/day/:date`.

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
- Pachchakkhan engine:
  - The five completion times are strictly increasing and all fall between sunrise and sunset.
  - Navkarsi is exactly 48 min after sunrise.
  - Purimaddh is the midpoint of sunrise and sunset.
  - Porsi, Sadh-Porsi, Purimaddh and Avaddh coincide with the matching choghadiya day-slot boundaries (2, 3, 4, 6).
  - The evening time equals sunset.
  - Ayambil/Upvas parana equals the next day's Navkarsi.
- Pachchakkhan formatting: completion times round up (an exact minute stays the same), and the evening time rounds down.
- Pachchakkhan screen: exactly one row is "next" at any instant from sunrise until Avaddh; after Avaddh none are; before sunrise, Navkarsi is next.
- Golden pachchakkhan dates from the Delhi 2027 laghu booklet (traditional sunrise), cited by page, **once the user provides the pages**.
- In Choghadiya, exactly one slot is current at any instant from sunrise to the next sunrise, and the countdown reaches 0 at the next slot's start.
- Settings: changing the profile, sunrise rule or month system changes festival dates or month names, and the choice persists across restarts.
- Accessibility: every tappable widget is at least 48×48 dp, there are no clipped texts at a text scale of 1.3, and each icon-only button has a semantics label.

## 6. Data gaps found while designing

1. **Kalyanak Hindi names: done.** `registry.py` now derives `name_hindi` for all 135 "Shri X Ji - Y Kalyanak" rows as "श्री {tirthankar} जी — {गर्भ/जन्म/दीक्षा/केवलज्ञान/मोक्ष} कल्याणक", using `TIRTHANKAR_HINDI` and `KALYANAK_HINDI`. Following the Digambar sources, the words are गर्भ, not च्यवन, and दीक्षा, not तप. The other 3 kalyanaks keep their hand-written names. When festival_service tags a kalyanak with its native tithi, it tags `name_hindi` too ("[एकादशी] श्री …"). All Hindi is still reviewed by the maintainer plus one sangh elder before the closed beta; check "अभिनंदन नाथ" in particular.
2. **Shri Neminath Ji – Omniscience Kalyanak appears twice in Oct 2026: a school variant, kept.** Vrindavan and Uttarapurana give Ashwin S1 (11 Oct); Ashadhara gives Ashwin S9 (20 Oct). Every kalyanak has `profiles: ["all"]`, and only the PDF and booklet filter by school (`festivals_for_school`). 13 other kalyanaks are split the same way. The maintainer decided (2026-10-30) to keep both and deal with school variants in the app later (a school tag or a school setting). Unverified: Pushpadanta Austerity has the same S1 vs S9 split, so the Ashadhara ९ may be a misread १ in the source PDF.
3. **Pachchakkhan source:** the Delhi 2027 laghu booklet pages with pachchakkhan times are not in the repo yet. Golden tests wait for them, and invariant tests come first.
4. **Choghadiya nature labels** in Hindi (अच्छा / सामान्य / टालें) are new strings. The engine's `nature` field stays English.

## 7. Open questions

Settled 2026-10-26: Month is the Gregorian grid only in the beta; the share card has a text footer with no QR code; the icon uses the siddhashila mark.

- Where wrong-date reports go: an email address and a WhatsApp number.
