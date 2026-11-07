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

## Settled follow-ups (2026-11-07)

- Times use the app's 12-hour clock with period words; an end on a later day is dated ("8 नवंबर, सुबह 11:28 तक"). English Rashi names carry the western sign ("Tula (Libra)"); gata reads "Tula (Libra), day 21".
- The Moon Rashi's next sign is shown without an end (it lasts two days or more), as in the mockup.
- Engine: the section is a separate `PanchangEngine().section()` read. On it, `month()` would go from ~220 ms to ~590 ms (desktop JIT) for fields the Month tab never shows.
- The Tithi lines lead with the **Jain tithi** (at sunrise + 6 ghati, as the
  hero shows), then the tithi after it, each with its end.
- Karana lists **every** Karana holding during the sunrise-to-sunrise day:
  usually 2–3, and 4 when a fast Moon fits one more in.
- This lifts "Karana, Yoga" out of the beta's Deferred row in
  `mobile-app-flutter.md` §1.
