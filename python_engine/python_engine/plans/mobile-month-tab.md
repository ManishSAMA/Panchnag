# Month tab (Phase 4, screen 2)

**Status:** In progress, from 2026-10-29. UI spec: [`mobile-ui-design.md`](mobile-ui-design.md) §3 · Month. Parent plan: [`mobile-app-flutter.md`](mobile-app-flutter.md) Phase 4.

## Decisions (2026-10-29)

| Topic | Decision |
|---|---|
| Festival dots | Done (2026-10-31), after the Phase 5 port: up to three marks per cell (mahaparva square, kalyanak ring, parva dot, vrat dot, in that priority), on every day of a span; the legend gains them and the day panel lists the day's festivals once the year arrives from its own worker. Before that the grid shows only the क्ष / वृ flags, never placeholders. |
| Engine call | A new `PanchangEngine.month(location, year, month, sunriseRule)` that returns the same `PanchangDay`s as calling `day()` for each date. It names lunar months once (`lunarMonthsBetween` + `amantaLookup`), computes each sunrise once, and searches each year's new year and Diwali at most once. Budget: < 1 s for 31 days (M4 open item). |
| Selection | Month keeps its own selected day. Only "पूरा दिन खोलें" ("Open full day") sets Today's `selectedDateProvider` and switches to the Today tab. |
| Day panel | Date; the full tithi with its end time; sunrise and sunset; the same kshaya / vriddhi notes as Today (house rule included); "पूरा दिन खोलें". Docked under the grid in a scrolling page; a modal bottom sheet below 640 dp of height. No report action yet (its destination is still open). |
| Cell tithi | Hindi `शु 11` · `कृ 5` · `पूर्णिमा` · `अमावस`; English `S 11` · `K 5` · `Purnima` · `Amavas`. |
| Header | ‹ month year ›; the subtitle is the Purnimanta months the month spans plus VS, as a range when it changes (`फाल्गुन – चैत्र · वि. सं. 2082–2083`). No VNS. |
| Range | The arrows disable at Jan 2016 and Dec 2040. |
| Swipe | None for now; arrows only (Phase 6 polish). |
| Tab | Second tab, माह / Month, between Today and Pachchakkhan. |

## Increments (TDD)

1. **Engine:** `month()` equals `day()` field by field for every date of a few months (a vriddhi month, a kshaya month, March of an Adhik year, October with Diwali, Dec→Jan edges).
2. **Formatting:** `tithiShort`, `monthTitle`, and the subtitle (month span + VS range) as pure functions.
3. **Grid:** 7 columns from Sunday; day number, short tithi, the क्ष on the day after a skipped tithi and वृ on both days of a repeat; a today ring; the selected day in `pill`; the legend.
4. **Header and range:** the arrows move by month and disable at the limits; the tab opens on the city's current month.
5. **Day panel:** its contents; docked versus modal by height; "Open full day" moves Today.
6. **Emulator check and performance:** time a month read through the worker in profile mode.

## Measured (2026-10-30, profile/AOT, `tool/perf_main.dart`)

| Device | Month call via worker | 31 single `day()` reads | One day, warm |
|---|---|---|---|
| Motorola Edge 70 Fusion (phone) | 493–600 ms ✓ | 941 ms | 32 ms median |
| Emulator, host busy with other sessions | 1.8–2.1 s | 3.7 s | 135 ms median |

The phone meets the < 1 s month budget, which closes the M4 open item. The emulator numbers are about 2× its M4 run, because the host was busy.

Test month: October 2026, Delhi (kshaya days on the 3rd and 27th, vriddhi on the 18th–19th, per the UI spec).
