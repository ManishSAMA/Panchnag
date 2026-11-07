# Panchang section (Tithi · Nakshatra · Yoga · Karana · Rashi) and the Pothi look app-wide

Status: agreed with the user 2026-11-07.

## What the user asked for

1. A **पंचांग** section on Full Panchang (its first section) and a compact
   **आज का पंचांग** card on Today, under the hero, with a "पूर्ण पंचांग देखें →"
   button that opens Full Panchang.
2. The Pothi look of Full Panchang (parchment `#F1E5C8` / navy `#171C29`
   grounds, red underlined headings, stitched left margin) and its roomier
   spacing on every screen, checked in Hindi and English.
3. Quieter connective words ("तक", "until", "to", "कल") in a duller colour;
   times slightly bold.

## Content of the section (order fixed by the user)

| Line | Shows |
|---|---|
| तिथि | current, then next, one per line: "द्वितीया **14:32** तक" / "तृतीया **13:10** तक, कल" |
| नक्षत्र | current and next, same form, each with the zodiac glyph(s) of the Rashi(s) it spans (both glyphs when it spans two) |
| योग | current and next |
| करण | every Karana from sunrise to next sunrise, each with its end |
| वार | weekday |
| *(gap)* | |
| मास | lunar month per the Purnimanta/Amanta setting |
| पक्ष | Shukla / Krishna |
| गते | the Rashi the Sun is in and the day count since it entered ("तुला **21** गते"); the sunrise-to-sunrise day holding the Sankranti is day 1 |
| विक्रम संवत / वीर निर्वाण संवत / शक संवत | years |
| *(gap)* | |
| चंद्र राशि | current with its end, then next |
| सूर्य राशि | current (and next, with the change time, on a Sankranti day) |

Not shown: Ritu, Ayana. The Today card shows only the current Tithi,
Nakshatra, Yoga, Karana and the weekday.

Zodiac glyphs are the app's own drawn glyphs (`panchang_symbols.dart`),
not emoji, sized to the text's cap height and coloured like the text accent.

## Engine work (Python is the reference, Dart is tested against it)

Python (`panchang.py` / `panchang_service.py`), TDD:
- `day_sequence` spans for nakshatra, yoga, karana and Moon Rashi from
  sunrise: the element at sunrise and the ones after it, **each with its real
  end even past next sunrise** (the existing `tithis` list stops with a null
  end; the new "next" line needs the end).
- Sun Rashi and `gata` (days since the Sun's latest Sankranti, Sankranti day = 1).
- Shaka Samvat already exists (`get_shaka_samvat`); report it per day.

Dart (`panchang_engine`): port the same, add fields to `PanchangDay`, keep
`month()` equal to `day()` for each date.

Parity: extend `parity_fixtures.day_row` with the new fields, regenerate
`core/` (~1 h on 14 workers), commit the diff.

## Phases (commit approval after each)

0. Commit the existing uncommitted work (Full Panchang, symbol guide, Pothi,
   Laghu changes) as it stands.
1. Engine: Python + Dart + fixtures.
2. Full Panchang section.
3. Today card + button.
4. Pothi palette, stitch and spacing on every screen; dull connective words.
   Built 2026-11-07: the parchment / navy-paper palette (contrast checked in `theme_test.dart`), both bars on the page ground, `PothiPage` (stitch, 22 dp binding) on every screen but the Month grid, `SectionHeading` drawn as a `PothiHeading` (the doubled `ListTop` hairline removed), hairline-edged tiles, and the share card on parchment. The Pachchakkhan hero's countdown is capped at half the row so the narrower page never squeezes the name.

## Settled follow-ups (2026-11-07)

- Times use the app's 12-hour clock with period words; an end on a later day is dated ("8 नवंबर, सुबह 11:28 तक"). English Rashi names carry the western sign ("Tula (Libra)"); gata reads "Tula (Libra), day 21".
- The Moon Rashi's next sign is shown without an end (it lasts two days or more), as in the mockup.
- Engine: the section is a separate `PanchangEngine().section()` read. On it, `month()` would go from ~220 ms to ~590 ms (desktop JIT) for fields the Month tab never shows.
- No duplicates on Full Panchang: Sun & Moon drops its Nakshatra row (the pada moves to the section's current nakshatra, "चित्रा (चरण 1)"); Tithi & Lunar Month drops the Jain tithi's name and end, both month rows and both samvat rows, keeping the reference time, the start and the tithi sequence.
- The Today button reads "पूरा पंचांग देखें" ("See full Panchang"), matching the page title, with an arrow icon.
- Today's card (Phase 3) shows all five lines with the Pothi heading and rows on Today's background (the parchment and stitch wait for Phase 4); the times list's Nakshatra row goes, and the button replaces the Full Panchang tile.
- Built 2026-11-07: the WhatsApp share card becomes the full-day card (Example B: header, sun times + samvats, the day's Panchang, festivals and vrat, Choghadiya Amrit/Shubh/Labh/Chal for day and night), replacing the current card, with the app's 12-hour times. Boxes like the picture (rounded, a red title tab), the greeting and big tithi kept on top, festivals as first name + count, the short caption kept.
- The Tithi lines lead with the **Jain tithi** (at sunrise + 6 ghati, as the
  hero shows), then the tithi after it, each with its end.
- Karana lists **every** Karana holding during the sunrise-to-sunrise day:
  usually 2–3, and 4 when a fast Moon fits one more in.
- This lifts "Karana, Yoga" out of the beta's Deferred row in
  `mobile-app-flutter.md` §1.
