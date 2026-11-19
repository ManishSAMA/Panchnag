# Plan: Muhurat band, date picker, Full Panchang button, red crosses, "now" highlight

Status: **built 2026-11-19** (Phases 1–6; approved the same day). The user's answers to Q1–Q7 are below the questions table; they win over the table where the two differ.

## Context

The user checked the Muhurat section on the phone (2026-11-19) and asked for these changes:

1. Today: a navy **मुहूर्त band** goes where the navy चौघड़िया band is now. The मुहूर्त tile stays. चौघड़िया opens from inside the Muhurat grid (its tile is already there).
2. A **calendar button** in the top bar of every screen. A push opens a date picker. The selected date applies to the full app.
3. The **"पूरा पंचांग देखें"** button becomes a filled red pill in the middle of the Today card.
4. The **✕ marks are red**.
5. A window that **runs now** gets a **light-green** row, not only the word "अभी".

Decisions already made by the user: band + keep tile; band text "now + next"; calendar icon in the top bar of every screen; red pill, centered.

Fact found: all screens already share one date (`selectedDateProvider`, `features/today/today_state.dart:54`). A change on one screen changes every screen. The problem is that `DateNavigator` (`shared/date_navigator.dart`) moves only one day for each push. The date picker solves this.

## Open questions (my recommendation first)

| # | Question | Recommendation |
|---|---|---|
| Q1 | Many windows can run at the same time. Which one does the band show as "now"? | Bad first: Rahu Kaal, then Bhadra on Earth, then Yamaganda, then Gulika. If none runs, the current चौघड़िया slot with its mark. |
| Q2 | Which windows count as the "next good time"? | The earliest of: Abhijit, or a चौघड़िया slot that is Amrit, Shubh or Labh, that starts after now. |
| Q3 | Which date picker? | The standard Material date picker (`showDatePicker`), in the app language, from `firstDay` to `lastDay`, with large text. Not our own tithi grid (the Month tab already has that). |
| Q4 | Must ✓ also get a colour? | Yes: ✓ green (`navpad.green`), ✕ red (`navpad.red`), "–" stays `ink2`. |
| Q5 | Where does the light-green "now" row show? | Every Muhurat detail row that runs now (Rahu Kaal, Yamaganda, Gulika, Abhijit, Panchak, Bhadra, Gandmool, yogas) and the Muhurat grid tile whose window runs now. The yellow "next" rows on Today and Pachchakkhan stay yellow. The चौघड़िया screen's current slot also becomes light green, so "now" has one colour in the app. |
| Q6 | Month and Festivals: do they get the calendar button? | Month: yes, for one look; it moves the grid to the month of the date. Festivals: no for now, because its list (today to 31 Dec) does not use the selected date. |
| Q7 | Commit the "पूरे दिन" fix (uncommitted, all tests pass) before this work? | Yes, as its own commit. |

### The user's answers (2026-11-19)

- **Q1 / Q5 (now):** every row and tile that shows a time window gets the light-green "now" look while the window runs: Rahu Kaal, Yamaganda, Gulika, Abhijit, Panchak, Bhadra, Gandmool, the yogas and the चौघड़िया slots. The band looks at all these windows: a running bad window first, else the current चौघड़िया slot.
- **Band, later decision:** Panchak and Gandmool are not in the band, because they run for days and would hide the चौघड़िया. The band names Rahu Kaal, Bhadra on Earth, Yamaganda and Gulika, in that order.
- **Q2 (next good):** from चौघड़िया: the next slot that is Amrit, Shubh or Labh.
- **Q3:** the standard phone date picker.
- **Q4:** ✕ red, ✓ green.
- **Q6 (calendar):** every screen with the ‹ date › row: Today, Pachchakkhan, चौघड़िया, Muhurat grid, each Muhurat detail, Full Panchang. Not Month or Festivals (no date row).
- **Q7:** the "पूरे दिन" fix was committed (01a0854) and all commits were pushed.

## Phases

Each phase is TDD (RED, GREEN, REFACTOR) in `mobile/app`. Mutation testing runs once at the end (user rule: batch mutation at the end of a feature). Each phase ends with a commit after the user approves it.

### Phase 1 — Red crosses and green ticks (small)

- `features/muhurat/muhurat_grid.dart`: `_MuhuratTile` draws the mark in a colour from the `Mark`: avoid → `n.red`, good → `n.green`, plain → `n.ink2`. Today all marks are `n.ink`.
- `features/muhurat/muhurat_screen.dart`: the detail rows give the mark the same colour. The mark is in the row's subtitle or suffix text now, so `TimeRow` needs a way to colour it (a new optional `mark` part, or a coloured `suffix`).
- The text "✕ टालें" stays, so the meaning is not only in colour.
- Tests: the mark's `TextStyle.color` equals `Navpad.red` (and green for ✓), in day and night. `theme_test.dart` checks red and green text at 4.5:1 on `ground` and `surface`. If one fails, use a darker red or green for text only.

### Phase 2 — Light-green "now" row

- `shared/navpad_widgets.dart`: a new `RowState.now`. Background a light green; text in `ink`.
  - Day: about `#DCE9D6` (now `onGreen2`). Night: a dark green tint, about `#24392B`. Both are new `Navpad` tokens (`nowFill`), and DESIGN.md gets them.
  - A 3 dp green bar at the row's start edge, so the row is easy to see also for colour-blind users. The word "अभी" stays.
- `muhurat_screen.dart` `timed()`: a running window gets `RowState.now` (it now only adds the "अभी" suffix).
- `muhurat_grid.dart`: a tile whose window runs now (only when the date is today) gets the green fill and the word "अभी".
- `choghadiya_screen.dart`: the current slot uses `RowState.now` (Q5).
- Tests: the running row's background is the `nowFill` token; a row that does not run is `ground`; contrast test for `ink` on `nowFill` in both themes; the grid tile for Rahu Kaal at a time inside it is green.

### Phase 3 — मुहूर्त band on Today

- New `features/muhurat/muhurat_band.dart`: `MuhuratBand(date, topGap)`, a navy `Band`, shown only when `date` is today (as `ChoghadiyaBand` is).
  - Title: the "now" window (Q1), for example "राहु काल · ✕ टालें", or "चौघड़िया: लाभ · ✓ अच्छा".
  - Value: "2:46 तक · 40 मि".
  - Subtitle: "अगला शुभ: अभिजित 11:43–12:27" (Q2).
  - Icon: `NavpadGlyph.abhijit` (the Muhurat icon on Today).
  - A push opens `/muhurat`.
- A pure function picks "now" and "next good" from `PanchangMuhurat` + the day's choghadiya slots + `now`, so tests can call it without widgets: `({nowItem, nextGood}) muhuratBandState(...)`.
- `features/today/today_screen.dart:210`: `MuhuratBand` replaces `ChoghadiyaBand`. `ChoghadiyaBand` is not used elsewhere, so it is deleted (its tests move to the band's tests or are deleted).
- ARB strings: band title and "next good" words, in `app_hi.arb` and `app_en.arb`.
- Tests: the band shows Rahu Kaal at a time inside Rahu Kaal; it shows the चौघड़िया slot at a time with no bad window; "next good" is the earliest good window after now; the band is hidden on another date; a push opens the Muhurat grid; text scale 2.0 does not overflow.

### Phase 4 — Calendar button on every screen

- New `shared/date_picker_button.dart`: `DatePickerButton`, an `IconButton` (`Icons.calendar_month`, tooltip "तारीख चुनें" / "Pick a date", 48 dp). A push calls `showDatePicker` with `initialDate` = selected date, `firstDate` = `firstDay`, `lastDate` = `lastDay`, `currentDate` = today in the city's zone, and the app locale. The result goes to `selectedDateProvider` (a new `SelectedDate.select(CivilDate)` if there is none).
- Put it first in `AppBar.actions` on: Today (before share), Pachchakkhan, Muhurat grid, Muhurat detail, Choghadiya, Full Panchang. Not on Month or Festivals (Q6).
- `DateNavigator`: a push on the date text also opens the picker.
- Tests: the button is on each screen; after a pick, the screen and another tab show the new date; dates outside `firstDay`..`lastDay` cannot be picked; Hindi and English; tap target guideline.

### Phase 5 — Red "पूरा पंचांग देखें" pill

- `features/today/panchang_card.dart:111`: the `TextButton.icon` becomes a centered `FilledButton.icon`: `n.red` fill, `n.onRed` text, round ends (StadiumBorder), the arrow icon at the end, min height 52 dp, horizontal padding 28 dp. Key `today-full-panchang` stays.
- Tests: the button is centered in the card, its fill is `Navpad.red`, a push opens Full Panchang, text scale 2.0 does not overflow.

### Phase 6 — Documents and checks

- `CLAUDE.md`: Today item (band, pill), Muhurat item (marks, now row), a date picker note.
- `DESIGN.md`: `nowFill` token, the mark colours, the band, the pill.
- `plans/muhurat-section.md`: a link to this plan.
- Mutation run on the new code (batch).
- Phone check: build `--target-platform android-arm64`, install, look at each change.

## Files to change (main)

- New: `features/muhurat/muhurat_band.dart`, `shared/date_picker_button.dart`, tests for both.
- Change: `shared/navpad_widgets.dart`, `theme/navpad.dart`, `features/muhurat/muhurat_grid.dart`, `features/muhurat/muhurat_screen.dart`, `features/choghadiya/choghadiya_screen.dart`, `features/today/today_screen.dart`, `features/today/panchang_card.dart`, `features/today/today_state.dart`, `shared/date_navigator.dart`, every screen's `AppBar`, `l10n/app_*.arb`, `test/theme_test.dart`.
- Delete: `features/choghadiya/choghadiya_band.dart` (if Today was its only user).

## Verification

1. `flutter analyze` is clean; `flutter test` passes.
2. Phone: Today shows the मुहूर्त band; the pill is red and centered; the calendar opens on each screen and the date changes on all tabs; the Muhurat grid and detail show red ✕, green ✓, and a light-green row for the window that runs now.

## Mutation report (Phase 6, 2026-11-19)

No Dart mutation tool is set up, so 30 hand-made mutants (one changed line each) ran against the feature's tests (`muhurat_band`, `muhurat_screen`, `choghadiya_screen`, `date_picker`, `today_panchang_card`).

- First run: 22 killed, 7 survived, 1 did not apply.
- New tests killed 6 survivors: the running row's 4 dp green bar; the running tile's green edge; a neutral slot is not the "next good" one; the band hides on yesterday's page before sunrise; in a Bhadra on Earth the band counts to the Bhadra's end (Rahu Kaal, Yamaganda and Gulika are each one choghadiya slot, so only Bhadra shows this); the pill stays centred on a wide screen (the test font makes it nearly card-wide on a phone).
- The mutant that did not apply (Rahu Kaal moved after Gulika) was run by hand: killed.
- The last survivor was a dead branch (a "done" row with a mark: no screen makes one). The branch was removed.
- Result: 30 of 30 killed or removed.
