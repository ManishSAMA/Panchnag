---
name: Jain Panchang
description: "Navpad Colours for daily navigation, with a stitched Pothi Almanac surface for complete daily reading."
colors:
  pothi-ground: "#F1E5C8"
  pothi-ground-dark: "#171C29"
  pothi-ink: "#243B64"
  pothi-ink-dark: "#F2E8D5"
  pothi-secondary: "#514A3C"
  pothi-secondary-dark: "#C9BFA9"
  pothi-accent: "#A33B2B"
  pothi-accent-dark: "#E8957F"
  pothi-rule: "#C9B98F"
  pothi-rule-dark: "#665B49"
  ground: "#FFFFFF"
  surface: "#F4F5F8"
  surface2: "#E9ECF2"
  hair: "#E1E4EB"
  ink: "#1F2A44"
  ink2: "#4A5570"
  ink3: "#646D82"
  navy: "#1F2A44"
  onNavy: "#FFFFFF"
  onNavy2: "#C9D0E0"
  red: "#B3261E"
  onRed: "#FFFFFF"
  onRed2: "#FBE2DF"
  yellow: "#E9B44C"
  onYellow: "#1F2A44"
  onYellow2: "#4A3A12"
  green: "#2E7D4F"
  onGreen: "#FFFFFF"
  onGreen2: "#DDF0E3"
  pill: "#DDE2EE"
  ground-dark: "#0E131E"
  surface-dark: "#161D2B"
  surface2-dark: "#1E2738"
  hair-dark: "#283044"
  ink-dark: "#ECEEF3"
  ink2-dark: "#B0B7C8"
  ink3-dark: "#8F98AC"
  navy-dark: "#2A3A60"
  onNavy-dark: "#FFFFFF"
  onNavy2-dark: "#CBD3E6"
  red-dark: "#C0362C"
  onRed-dark: "#FFFFFF"
  onRed2-dark: "#FCE0DC"
  yellow-dark: "#D4A03F"
  onYellow-dark: "#1F2A44"
  onYellow2-dark: "#3A2C0A"
  green-dark: "#2B7A4C"
  onGreen-dark: "#FFFFFF"
  onGreen2-dark: "#D7EFDF"
  pill-dark: "#2E3A57"
typography:
  display-pothi:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "30sp"
    fontWeight: 400
    lineHeight: 1.1
  display-pothi-section:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "23sp"
    fontWeight: 400
    lineHeight: 1.2
  display-hero:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "44sp"
    fontWeight: 400
    lineHeight: 1.12
    letterSpacing: "0"
  display-brand:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "40sp"
    fontWeight: 400
    lineHeight: 1.15
  display-band:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "36sp"
    fontWeight: 400
    lineHeight: 1.1
  display-month:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "26sp"
    fontWeight: 400
    lineHeight: 1.2
  display-heading:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "24sp"
    fontWeight: 400
    lineHeight: 1.2
  display-group:
    fontFamily: "Tiro Devanagari Hindi, serif"
    fontSize: "22sp"
    fontWeight: 400
    lineHeight: 1.2
  countdown:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "30sp"
    fontWeight: 700
    lineHeight: 1.1
    fontFeature: "tnum"
  headline:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "24sp"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "0"
  title-section:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "20sp"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0"
  title-band:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "18sp"
    fontWeight: 700
    lineHeight: 1.3
  body-large:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "17sp"
    fontWeight: 400
    lineHeight: 1.35
    fontFeature: "tnum"
  body:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "16sp"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "tnum"
  label-action:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "16sp"
    fontWeight: 600
    lineHeight: 1.3
  label-secondary:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "14sp"
    fontWeight: 500
    lineHeight: 1.3
  label-nav:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "13sp"
    fontWeight: 600
    lineHeight: 1.3
  cell-day:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "19sp"
    fontWeight: 600
    lineHeight: 1.1
    fontFeature: "tnum"
  cell-tithi:
    fontFamily: "Mukta, Noto Sans Devanagari, sans-serif"
    fontSize: "12sp"
    fontWeight: 400
    lineHeight: 1.25
rounded:
  mark: "2dp"
  sm: "4dp"
  md: "8dp"
  tile: "12dp"
  indicator: "16dp"
  chip: "20dp"
  full: "24dp"
spacing:
  band-gap: "2dp"
  xs: "4dp"
  sm: "8dp"
  md: "12dp"
  gutter: "18dp"
  section: "30dp"
  pothi-section: "22dp"
  pothi-left: "30dp"
  pothi-stitch: "14dp"
components:
  pothi-group:
    textColor: "{colors.pothi-accent}"
    typography: "{typography.display-pothi-section}"
  pothi-row:
    backgroundColor: "{colors.pothi-ground}"
    textColor: "{colors.pothi-ink}"
    typography: "{typography.body-large}"
    padding: "8dp 0"
    height: "48dp"
  pothi-section-link:
    textColor: "{colors.pothi-accent}"
    typography: "{typography.label-action}"
    height: "48dp"
  pothi-lunar-seal:
    textColor: "{colors.pothi-accent}"
    size: "54dp"
  band-red:
    backgroundColor: "{colors.red}"
    textColor: "{colors.onRed}"
    typography: "{typography.title-band}"
    padding: "9dp 12dp 9dp 18dp"
    height: "58dp"
  band-yellow:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.onYellow}"
    typography: "{typography.title-band}"
    padding: "9dp 12dp 9dp 18dp"
    height: "58dp"
  band-green:
    backgroundColor: "{colors.green}"
    textColor: "{colors.onGreen}"
    typography: "{typography.title-band}"
    padding: "9dp 12dp 9dp 18dp"
    height: "58dp"
  band-navy:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.onNavy}"
    typography: "{typography.title-band}"
    padding: "9dp 12dp 9dp 18dp"
    height: "58dp"
  band-hero-pachchakkhan:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.onYellow}"
    padding: "16dp 18dp"
    height: "132dp"
  band-hero-choghadiya:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.onNavy}"
    padding: "16dp 18dp"
    height: "120dp"
  list-row:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.body-large}"
    padding: "8dp 18dp"
    height: "52dp"
  list-row-done:
    textColor: "{colors.ink3}"
  list-row-next:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.onYellow}"
  list-row-now:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.onNavy}"
  festival-row-mahaparva:
    backgroundColor: "{colors.red}"
    textColor: "{colors.onRed}"
    rounded: "{rounded.sm}"
    height: "52dp"
  button-filled:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.onNavy}"
    typography: "{typography.body-large}"
    rounded: "{rounded.full}"
    padding: "0 22dp"
    height: "48dp"
  button-outlined:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    padding: "0 20dp"
    height: "48dp"
  button-text:
    textColor: "{colors.ink}"
    typography: "{typography.label-action}"
    padding: "0 18dp"
    height: "48dp"
  icon-button:
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    size: "48dp"
  chip-filter:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.label-action}"
    rounded: "{rounded.chip}"
    padding: "0 16dp"
    height: "40dp"
  chip-filter-selected:
    backgroundColor: "{colors.pill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "0 16dp 0 10dp"
    height: "40dp"
  segmented-selected:
    backgroundColor: "{colors.pill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    height: "48dp"
  switch-on:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.onNavy}"
    rounded: "{rounded.indicator}"
    width: "52dp"
    height: "32dp"
  switch-off:
    backgroundColor: "{colors.surface2}"
    textColor: "{colors.ink3}"
    rounded: "{rounded.indicator}"
    width: "52dp"
    height: "32dp"
  nav-bar:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink2}"
    typography: "{typography.label-nav}"
    height: "80dp"
  nav-indicator:
    backgroundColor: "{colors.pill}"
    textColor: "{colors.ink}"
    rounded: "{rounded.indicator}"
    width: "64dp"
    height: "32dp"
  feature-tile:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.label-action}"
    rounded: "{rounded.tile}"
    height: "76dp"
  icon-badge:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    size: "36dp"
  festival-badge:
    size: "32dp"
  note:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "12dp 14dp"
  month-cell:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.cell-day}"
    height: "64dp"
  month-cell-selected:
    backgroundColor: "{colors.pill}"
    textColor: "{colors.ink}"
  top-app-bar:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.headline}"
    height: "64dp"
---

# Design System: Jain Panchang

## Overview

**Creative North Star: "Navpad Colours"**

The Siddhachakra's five colours, known by heart from Navpad Oli, are the core app's colour language, and each colour has exactly one job. White is the ground. Navy is ink, and it also carries the tithi and choghadiya. Red is parva and kalyanak. Yellow is the next pachchakkhan, only on today. Green is vrat and tapasya. A colour appears in exactly three forms: a solid full-bleed band, a filled list row, or a small festival icon (kalash, five lights, temple flag, diya) in a list or the Month grid. Nothing is tinted for decoration, so when a colour appears the reader already knows what it means.

The system is built for an elder reading in daylight at the start or end of a fast. Type is large: body is 16 sp or more, and the hero tithi is 44 sp Tiro Devanagari. Every touch target is 48 dp. The core pages are flat white with hairline lists and no cards, and the bands are their only weight. Material 3 supplies the structure (app bar, navigation bar, chips, segmented buttons, switches, sheets). Navpad supplies every core colour, through a hand-built `ColorScheme` plus a `ThemeExtension`. Dynamic colour is never used.

Dark mode is a first-class scheme, not an inversion. The core ground becomes a deep navy-black (`ground-dark`), the five meanings keep their hues at slightly adjusted values, and the text on each band keeps its contrast.

Full Panchang and its Symbol Guide form a deliberate surface-specific world, **The Pothi Almanac**. A continuous warm-paper reading surface, indigo ink, vermilion rules, a stitched left edge, and a double-ring lunar seal translate the printed booklet without copying the competitor's red-and-gold tables. It retains Material navigation, bilingual labels, real engine values, and the same bundled typefaces. Dark mode uses deep indigo paper and light vermilion structure.

**Key Characteristics:**
- Five meaning colours, one job each, never decorative on core surfaces.
- Full-bleed 58 dp bands in a fixed order: red, yellow, green, navy.
- Hairline lists: 1 dp `hair` dividers, no cards, no shadows.
- Tiro Devanagari for display, Mukta for everything else.
- One right-aligned column of tabular times on every screen.
- Selection is always the navy-tint `pill` plus a check, never a meaning colour.
- Full Panchang is a stitched Pothi reading surface, not a dashboard of cards.

## Colors

Core screens use a white ground with navy ink and four saturated meaning colours. Full Panchang instead uses its documented Pothi paper, ink, and vermilion roles.

### Primary
- **Siddha Navy** (`navy`, `navy-dark`): ink, the choghadiya band, the current-choghadiya row, the filled button, the "on" switch track, the selected radio dot, onboarding progress dots, the 2 dp ring around today in the Month grid, and the dark part of the moon of the tithi. In light mode it is the same value as `ink`. Text on navy is `onNavy`, and secondary lines are `onNavy2`.
- **Pothi Indigo** (`pothi-ink`, `pothi-ink-dark`): all primary text and reference symbols on Full Panchang and its Symbol Guide.

### Secondary
- **Parva Red** (`red`, `red-dark`): parva and kalyanak only. It appears as the ongoing-parva band, the filled mahaparva row in Festivals, the kalash (mahaparva), five-lights (kalyanak) and temple-flag (parva) icons with their 8 % tinted circles, and the share card's ongoing-parva strip. Text on red is `onRed`, and secondary lines are `onRed2`.
- **Pachchakkhan Yellow** (`yellow`, `yellow-dark`): only the next pachchakkhan, and only on today. It appears as the Today band, the Pachchakkhan hero, and the "next" row in the Pachchakkhan list. Text on yellow is navy (`onYellow`), never white, and secondary lines are `onYellow2`.
- **Pothi Vermilion** (`pothi-accent`, `pothi-accent-dark`): section names, 2 dp group rules, section links, stitching, and the lunar seal on the Pothi surface. It is structural print ink, not a second parva signal.

### Tertiary
- **Vrat Green** (`green`, `green-dark`): vrat and tapasya only. It appears as the vrat band and the diya icon with its 8 % tinted circle. Text on green is `onGreen`, and secondary lines are `onGreen2`.

### Neutral
- **Ground** (`ground`, `ground-dark`): the scaffold, Month cells, and the onboarding footer.
- **Surface** (`surface`, `surface-dark`): the navigation bar, notes, the docked day sheet in Month, Today's feature tiles, the 36 dp circles behind row icons, and the hover/press wash on icon buttons.
- **Surface 2** (`surface2`, `surface2-dark`): the off-state switch track.
- **Hairline** (`hair`, `hair-dark`): 1 dp list dividers, Month grid lines, the note border, the inactive progress dot.
- **Ink** (`ink`, `ink-dark`): primary text and icons.
- **Ink 2** (`ink2`, `ink2-dark`): secondary text: sub-lines, date lines, legends, inactive nav labels.
- **Ink 3** (`ink3`, `ink3-dark`): past or done times, outlines on chips, segmented buttons, outlined buttons and switches, and disabled icon buttons.
- **Pill** (`pill`, `pill-dark`): the navy tint for the navigation-bar indicator and every selection: the selected filter chip, the selected segment, and the selected Month day.
- **Pothi Paper** (`pothi-ground`, `pothi-ground-dark`): the continuous Full Panchang and Symbol Guide field.
- **Pothi Secondary Ink** (`pothi-secondary`, `pothi-secondary-dark`): dates, samvat lines, subtitles, English translations, and the reference-only explanation.
- **Pothi Rule** (`pothi-rule`, `pothi-rule-dark`): quiet 1 dp row dividers against the paper.

### Flutter mapping
Build `ColorScheme` by hand for each brightness: `primary` = navy, `onPrimary` = onNavy, `secondaryContainer` = pill, `onSecondaryContainer` = ink, `surface` = ground, `onSurface` = ink, `onSurfaceVariant` = ink2, `outline` = ink3, `outlineVariant` = hair, `surfaceContainer` = surface, `surfaceContainerHighest` = surface2. With this mapping, the M3 NavigationBar indicator, FilterChip, SegmentedButton, Switch and FilledButton land on the built colours without per-widget overrides. Red, yellow and green and their `on`/`on2` pairs live only in the Navpad `ThemeExtension`. The separate `Pothi` extension carries ground, ink, secondary, accent, and rule in light and dark. `ColorScheme.error` is required, but no widget in the build uses the error role, because denied-permission and limit states are neutral notes.

### Named Rules
**The One Job Rule.** On core surfaces, each of the five colours has one meaning: navy for ink, tithi and choghadiya; red for parva and kalyanak; yellow for the next pachchakkhan; green for vrat. A colour never appears anywhere else on those surfaces, so it is never used for accent, emphasis, selection, error or brand decoration. The explicitly documented Pothi reading surface is the only exception.

**The Pothi Surface Rule.** Warm paper, indigo, secondary ink, vermilion, and quiet rules belong only to Full Panchang and its Symbol Guide. They never recolour Today, Month, Pachchakkhan, Festivals, Choghadiya, or Settings.

**The Today-Only Yellow Rule.** Yellow appears only for the next pachchakkhan, and only when the date shown is today. On any other date there is no yellow band, no yellow row and no hero. After sunset the hero becomes a quiet ink row.

**The Navy-Tint Selection Rule.** Selection never borrows a meaning colour. Every selected state uses the `pill` fill with a ✓: the nav indicator, the filter chip, the segment, and the Month day.

**The Not-By-Colour-Alone Rule.** Choghadiya quality is shown by a ✓ / – / ✕ icon, a label and the weight (good slots are bold), never by red or green. Kshaya and vriddhi are flagged by the ink letters क्ष / वृ plus a note. Festival kinds differ in shape as well as colour: kalash, five lights, temple flag, diya. Every band and mark also carries its words.

**The Moon Rule.** The moon of the tithi is the one drawing that is not a line icon: a disc whose lit part is white and whose dark part is `navy` (not `ink`, which is light in dark mode), with a 1.4-unit `ink` rim. It is lit i/15 on Shukla i and 1 − (i − 15)/15 on Krishna days, on the right while waxing, so पूर्णिमा is a white disc and अमावस a solid navy one.

## Typography

**Display Font:** Tiro Devanagari Hindi (with serif)
**Body Font:** Mukta 400/500/600/700 (with Noto Sans Devanagari, sans-serif)

**Character:** Tiro carries the printed-panchang voice for the few words that name the day. Mukta is a clear, sturdy UI face that covers Devanagari and Latin at every weight. Both are bundled as assets and never fetched at runtime.

### Hierarchy
- **Display hero** (Tiro 400, 44 sp, 1.12): the Today tithi. It has no label above it.
- **Display Pothi** (Tiro 400, 30 sp): the Full Panchang tithi below its lunar seal.
- **Display Pothi section** (Tiro 400, 23 sp): Full Panchang group names; Symbol Guide group names use 24 sp.
- **Display brand** (Tiro 400, 40 sp, 1.15): the onboarding brand line and the share-card greeting.
- **Display band** (Tiro 400, 36 sp, 1.1): the Pachchakkhan and Choghadiya hero names inside their grown bands.
- **Display month / heading / group** (Tiro 400, 26 / 24 / 22 sp): the Month title, the day-sheet title and the Festivals date numerals, and the Festivals month headings. Group (22 sp) is also the day numeral of each upcoming date on Today.
- **Countdown** (Mukta 700, 30 sp; 28 sp on Choghadiya, tabular): the live timer in a hero band.
- **Headline** (Mukta 700, 24 sp): the top-app-bar title.
- **Title section** (Mukta 700, 20 sp): list section headings.
- **Title band** (Mukta 700, 18 sp): the band title. The 18 sp/600 location chip uses the same size.
- **Body large** (Mukta 400, 17 sp, 1.35): list rows, the date line and the hero meta line. In the time column the value is 600.
- **Body** (Mukta 400, 16 sp, 1.45): notes and running text. Action labels use 16 sp/600.
- **Label secondary** (Mukta 500, 14 sp): row sub-lines, band sub-lines, legends. This is the smallest size outside the Month grid and the nav bar.
- **Label nav** (Mukta 600, 13 sp): the navigation-bar labels.
- **Cell day / cell tithi** (Mukta 600 19 sp / 400 12 sp): Month grid cells only. The kshaya/vriddhi corner flag is 11 sp/700.

### Named Rules
**The Display-Is-Few Rule.** Tiro is only for the names of days, tithis, months, hero slots, and Pothi section headings. Buttons, rows, labels and numbers are always Mukta.

**The Time Column Rule.** Every number is tabular, and times sit in one right-aligned column on every screen, with the period word (सुबह, शाम) in a lighter weight before the value.

**The Scale Rule.** Sizes follow the system `textScaler`, with support required through 1.6× and layouts tested at 1.3×. Full Panchang is also tested at 2.0×. No letter-spacing is applied anywhere.

## Layout

The app is a single column, 390 dp wide in the mockup, with an 18 dp gutter on text and lists. Bands and list dividers run full-bleed to both edges. The rhythm on Today is: 28 dp status bar, then the 64 dp top app bar, then the date navigator (48 dp prev/next buttons around a centred two-line date), then the hero (10 dp top, 18 dp bottom), then a wrapping grid of feature tiles (12 dp side margin, 8 dp gaps, 16 dp below), then up to four bands stacked with 2 dp gaps, then sections. Each section starts 30 dp above its 20 sp heading. Lists start with a top hairline, and each row is at least 52 dp with 8 dp × 18 dp padding.

The navigation bar is 80 dp, and the content scrolls under it. The Month grid has 7 equal columns inside a 10 dp side margin, with 64 dp cells drawn by hairlines. The Festivals list is a 58 dp date column next to a flexible festival column, and each festival line ends in a 48 dp bell button. Chip rows wrap, or scroll horizontally for filters, with 8 dp gaps.

Full Panchang has no bottom tab bar. Its stitched rule sits 14 dp from the left; reading groups use a 30 dp left inset, 18 dp right inset, and 22 dp separation. A centred header leads to horizontally scrollable section links and continuous ruled rows with a 48 dp minimum height. The Symbol Guide uses 18 dp page gutters, one column on a phone, and two columns only at 500 dp or more with ordinary text scale.

**The 48 dp Rule.** Every tappable element is at least 48 × 48 dp. Chips are 40 dp tall but add a 4 dp invisible hit extension above and below. Nothing is gesture-only.

## Elevation & Depth

The system is flat. There are no shadows anywhere in the app. On core screens, depth comes from tone only: `surface` sits under `ground` for the navigation bar, notes and the docked day sheet, and a 1 dp `hair` line marks every edge. Pothi uses paper tone and printed rules rather than elevation. The only inset stroke is the 2 dp navy ring around today in the Month grid; it is a marker, not elevation. In Flutter, set `surfaceTintColor` to transparent and elevation to 0 on app bars, nav bars and sheets.

### Named Rules
**The Flat Page Rule.** Lists are hairline rows, never cards or shadows. On core pages the bands are the only weight. Today's feature tiles are flat `surface` blocks with 12 dp corners and no border or shadow. Full Panchang and Symbol Guide remain continuous ruled reading surfaces. Nothing becomes a floating card.

**The Grow-Into-Header Rule.** Motion is the only depth device. When a time passes, the yellow band advances in place with a 200 ms cross-fade. Tapping a band grows it into the next screen's header with a Material container transform. With "Remove animations" on, both are instant.

**The Almanac Wayfinding Rule.** A Pothi section link scrolls its group into view over 350 ms with an ease-out curve and briefly washes the destination in vermilion at 10 % opacity. With animations disabled, the scroll and highlight are instant.

## Shapes

Edges are square wherever a meaning colour sits. Bands, filled rows and hero bands have 0 dp corners and run edge to edge. The one exception is the mahaparva row in Festivals, which is inset and has 4 dp corners. Controls are fully round: buttons and segmented groups are 24 dp, chips 20 dp, and the nav indicator and switch 16 dp. Notes have gentle 8 dp corners, and the focus ring has 4 dp corners. Feature tiles have 12 dp corners. Pothi rows are square and uncarded; its lunar seal is two concentric circular vermilion strokes. Icons are 24 dp line icons with a 1.8 stroke and round caps and joins, drawn as vectors (see Icons).

## Icons

The app draws its own line icons (`shared/navpad_icons.dart`: a `CustomPainter` over the approved mockup's SVG path data, with no icon font or SVG package). They are 24 dp on a 24-unit grid, 1.8 stroke, round caps and joins, and take their size and colour from `IconTheme`. They are silent to screen readers unless given a label, since words always sit beside them.

- **Sunrise / sunset:** a half sun on the horizon with an arrow up or down. Used on the sun rows of Today and the day panel; sunrise is also the आज tab.
- **Nakshatra:** a four-pointed star with three small stars. Used on Today's nakshatra row.
- **Ghatika:** the choghadiya water bowl over a wave. Used on the navy band, the Choghadiya hero and its feature tile.
- **Sunpath:** the sun on its dashed day arc over the horizon. Used on the पच्चक्खाण tab and tile. In pachchakkhan rows and the yellow band and hero, the sun stands where it will be at that time, (time − sunrise) ÷ (sunset − sunrise): Navkarsi's sun has just risen, and Chauvihar's sits on the right-hand horizon. Rows without a time of their own show the plain icon.
- **Kalash** (mahaparva), **five lights in a ring** (kalyanak), **temple flag** (parva) and **diya** (vrat): the festival icons, mapped in one place (`shared/festival_icon.dart`), in red, or green for vrat.
- **Month calendar:** a calendar with a crescent. Used on the माह tab and tile.
- **Full Panchang:** an open almanac. Used on the Full Panchang feature tile; a Material outlined book opens the Symbol Guide.
- **Siddhashila:** the crescent with a dot above it; the app mark.
- **Panchang reference symbols:** 38 custom vector glyphs in `shared/panchang_symbols.dart`: 11 planets/node, 12 zodiac signs, 9 aspects, 4 moon phases, and 2 eclipses. They use a 24-unit grid, 1.55 stroke, round caps and joins, and render at 32 dp in the guide. They are not Unicode text, an icon font, calculated positions, or event markers.

Plain app actions keep their Material shapes: location, settings, back, chevrons and ✓.

**Leading circles.** A list row's icon sits in a 36 dp `surface` circle and takes the row's text colour (`ink3` when done; on the yellow next row the circle is `onYellow` at 8 %). A band's icon sits in a 36 dp circle of the band's text colour at 12 % (8 % on yellow). A festival icon in a list sits in a 32 dp circle of its own colour at 8 %.

## Components

### Bands (signature)
The full-bleed colour band is the system's signature: a 58 dp tappable strip with a bold title and a sub-line on the left, a tabular value and a chevron on the right. They come in a fixed order: red (ongoing parva), yellow (next pachchakkhan with a countdown), green (vrat), navy (current choghadiya). Each appears only when it has content, and each opens its screen. The yellow and navy bands grow into 132 dp and 120 dp hero headers on Pachchakkhan and Choghadiya, with the name in 36 sp Tiro and the countdown right-aligned.

### Feature tiles (Today)
Under the hero sits a wrapping grid of flat `surface` tiles with 12 dp corners, no border and no shadow. Each is at least 76 dp tall, with a 28 dp icon over a centred 14 sp/600 label. In logical order:
- पूरा पंचांग (fullPanchang) opens Full Panchang outside the tabs.
- चौघड़िया (ghatika) opens Choghadiya.
- पच्चक्खाण (sunpath) opens that tab.
- पर्व सूची (kalash) opens the Festivals tab, and appears only once that route exists.
- माह (monthcal) opens Month on the date shown.

Each tile is a button named by its label. Three columns are used at ordinary text and two from 1.3× text, measured at the label's 14 sp because Android scales text non-linearly. A short final row keeps earlier tiles aligned to their columns.

### Moon of the tithi
It is 58 dp beside the Today hero tithi, with the short tithi (12 sp/600, `ink2`) under it, and it is named to screen readers ("कृष्ण षष्ठी का चंद्रमा"). It is 11 dp before the short tithi in each Month cell, and 24 dp in the circle of the day panel's tithi row. On Full Panchang the calculated 40 dp disc sits inside a 54 dp double-ring vermilion seal, centred above the 30 sp tithi, with the same semantic label.

### Pothi Almanac (Full Panchang signature)
A standard Material back app bar carries the Full Panchang title and a labelled book action for the Symbol Guide. The shared date navigator and place sit above the lunar seal, tithi, lunar month, and both samvats. Four underlined section links lead to Sun & Moon, Tithi & Lunar Month, Pachchakkhan, and Choghadiya; festivals follow below. Every supported value appears: both month systems and samvats, every tithi span, Jain start/end/reference, sunrise/sunset/next sunrise, nakshatra/pada/end, all pachchakkhan values, all 16 choghadiya periods, festivals/spans, and kshaya/vriddhi/boundary explanations. Completion times retain their existing rounding rules.

The Symbol Guide groups all 38 drawn reference symbols under planets, zodiac, aspects, moon phases, and eclipses. Aspect degrees sit at the right. Hindi rows include their English names. A visible disclaimer says the guide does not show calculated positions, aspects, or eclipse events; unsupported competitor calculations are not added.

### Buttons
- **Shape:** fully round (24 dp), 48 dp tall.
- **Filled:** navy with onNavy text, 17 sp/600, 22 dp side padding. It is used for a single main action, such as "GPS से पता लगाएँ" or "open phone settings".
- **Outlined:** transparent with a 1 dp ink3 outline, ink text, 20 dp side padding. It is used for "आज" in Month and "back to today".
- **Text:** underlined ink label, 16 sp/600, with a 4 dp underline offset. It is used for "गलत लगे तो बताएँ" (report), section links and Back.
- **Icon:** a 48 dp circle with a 24 dp line icon; hover/press fills it with `surface`. When disabled, it shows ink3 at 45 % opacity.
- **Focus:** a 3 dp ink outline, 2 dp offset, 4 dp corners on every interactive element.

### Chips
- **Style:** 40 dp, 20 dp corners, 1 dp ink3 outline, ink text, 16 sp/600.
- **Selected:** a `pill` fill, the outline matching the fill, and an 18 dp ✓ before the label. The location and tradition chips are action chips with a trailing ▾.

### Segmented buttons
A 48 dp, fully rounded group with a 1 dp ink3 outline and dividers. The selected segment is `pill` with a ✓. It is used for day/night in Choghadiya and in Settings.

### Lists
- **Row:** at least 52 dp, with a 1 dp hair bottom divider, the name and a sub-line on the left, and the time column on the right.
- **Done:** ink3 text and a ✓ icon, weight 500.
- **Next (pachchakkhan, today only):** filled yellow, with navy text.
- **Now (choghadiya):** filled navy, with onNavy text.
- **Mahaparva (Festivals):** a filled red row with onRed text and a white icon.
- **Upcoming festivals (Today):** grouped by date. Each group opens with a heading behind a top hairline: the day numeral in 22 sp Tiro, then "नवंबर · शनिवार · 7 दिन बाद" in label-secondary `ink2`. The next day reads "कल" / "tomorrow", and the count starts from the date shown. Under the heading is one 48 dp row per festival: its icon in a 32 dp tinted circle, then its name and kind.

### Notes
A bordered box: `surface` fill, a 1 dp hair border, 8 dp corners, 12 × 14 dp padding, a 22 dp info or alert icon, a 17 sp bold title and a 16 sp ink2 body. It is used for vriddhi and kshaya explanations, near-boundary warnings (with the report action), and denied-permission states. It is the only bordered container in the system.

### Navigation
An M3 NavigationBar, 80 dp on `surface` with a top hairline: four destinations (आज, माह, पच्चक्खाण, पर्व), 24 dp app icons (sunrise, month calendar, sunpath, kalash: the same drawing whether selected or not, since the pill shows selection), 13 sp/600 labels. The active destination has ink text and icon on a 64 × 32 dp `pill` indicator. Inactive destinations are ink2. The top app bar is 64 dp on `ground`, with a 24 sp/700 title, or on Today the location chip, share and settings.

### Switches
An M3 Switch, 52 × 32 dp. Off: a `surface2` track, a 2 dp ink3 outline and a 16 dp ink3 thumb. On: a navy track and a 20 dp onNavy thumb. The thumb slides in 200 ms on the standard curve.

### Month grid
Seven hairline columns of 64 dp cells: the day number (19 sp/600), the 11 dp moon and the short tithi (12 sp, shrunk rather than wrapped when a cell is narrow), up to three 13 dp festival icons (2.2 stroke, in kalash, five lights, flag, diya order), and a क्ष / वृ corner flag. The legend under the grid shows the four icons at 16 dp with their words. Today has a 2 dp navy inset ring, and the selected day is filled with `pill`. The day sheet below sits on `surface`, with a 32 × 4 dp grab handle and a Tiro title.

## Do's and Don'ts

### Do:
- **Do** give each core colour exactly one job: navy for ink, tithi and choghadiya; red for parva and kalyanak; yellow for the next pachchakkhan on today; green for vrat.
- **Do** show meaning colour only as a full-bleed band, a filled row, or a festival icon on core surfaces.
- **Do** draw Jain ideas and reference symbols with the app's own vectors, and keep Material shapes for plain actions.
- **Do** use the `pill` tint with a ✓ for every selected state.
- **Do** put navy (`onYellow`) text on yellow, and white text on red, green and navy.
- **Do** keep every time in one right-aligned, tabular column.
- **Do** carry every meaning in words, icons or weight as well as colour.
- **Do** keep touch targets at 48 dp and body text at 16 sp or larger, and scale with `textScaler` through at least 1.6×.
- **Do** bundle Mukta and Tiro Devanagari Hindi as assets.
- **Do** confine the warm-paper Pothi palette and stitched edge to Full Panchang and its Symbol Guide.
- **Do** label the Symbol Guide as reference-only and show only supported engine calculations on Full Panchang.

### Don't:
- **Don't** use yellow on any date other than today, or for anything but the next pachchakkhan, including text selection.
- **Don't** colour choghadiya quality, kshaya or vriddhi red or green.
- **Don't** put lists in cards or give any surface a shadow. Today's feature tiles are the only card-like blocks, and they stay flat.
- **Don't** use Material You dynamic colour or `ColorScheme.fromSeed`.
- **Don't** introduce saffron, beige, or other unapproved colours on Navpad surfaces; Pothi uses only its documented tokens.
- **Don't** set Tiro Devanagari on buttons, rows or numbers.
- **Don't** put a label or eyebrow above the hero tithi.
- **Don't** present reference glyphs as calculated planetary positions, active aspects, or eclipse events.
