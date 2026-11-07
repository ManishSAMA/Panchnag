# Product

<!-- impeccable:product-schema 1 -->

## Platform

android

## Users
The primary user is an observant Shwetambar Jain, often 50 or older. They check the app every morning and evening: today's tithi, Navkarsi and other pachchakkhan times, Chauvihar before sunset, and whether a parva, kalyanak or vrat is coming. Sangh members also check dates on behalf of each other. A wrong tithi is noticed immediately.

## Product Purpose
Jain Panchang (जैन पंचांग) is a sunrise-based Jain calendar for Android. It answers, for the user's own location, the questions "what is today's tithi and what is coming", "when may I complete my pachchakkhan", and "is this a good choghadiya". Success means testers in the sangh trust it enough to use it in place of the printed panchang, and there are no open wrong-date reports at launch.

## Positioning
- **Verified accuracy.** Every date is checked against a Swiss-Ephemeris reference engine (`python_engine`) for every day from 2016 to 2040. Kshaya and vriddhi days follow stated rules: a vrat on the second day of a vriddhi, a kalyanak on the first, and a parva on both.
- **Works anywhere, offline.** It uses any GPS location, including outside India. There is no internet use, and no ads, accounts or tracking.
- **The user's tradition's dates.** Tapagachchha, Sthanakvasi and Terapanthi each get their own festival dates.
- **Calm and respectful.** Devotional, but uncluttered, unlike the ad-heavy apps in the category.

## Operating Context
It is used at home and on the way to the temple or sthanak, often in bright daylight, at the start and end of a fast. It sits next to the printed Laghu Panchang booklet, which users compare it against. Days are shared on WhatsApp. The mental model is the printed panchang: Jain tithi, sud/vad, Purnimanta month, VS, and Vira Nirvana Samvat.

## Capabilities and Constraints
- **Beta screens:** onboarding, Today, Month (Gregorian grid with a day sheet), Pachchakkhan, Festivals, Choghadiya (opened from Today), Settings, festival reminders, a share card, and "report a wrong date". Spec: `python_engine/plans/mobile-ui-design.md`.
- **Languages:** Hindi and English only. Gujarati is out of scope.
- **Technical constraints:**
  - Flutter app with a pure-Dart engine, fully offline.
  - Date range 2016–2040 is a hard limit.
  - Reminders use inexact alarms.
  - Crash reporting is off by default.
- **Pachchakkhan rules:**
  - Navkarsi is sunrise + 48 min.
  - Porsi, Sadh-Porsi, Purimaddh and Avaddh are ¼, ⅜, ½ and ¾ of the day.
  - Chauvihar, Tivihar and Duvihar are at sunset.
  - Completion times round up and evening times round down.
- **Terminology:** Jain tithi (the tithi at sunrise + 2 h 24 m), kshaya, vriddhi, parva, kalyanak, vrat, choghadiya, pachchakkhan.
- **Undecided:** where wrong-date reports go.
- **Deferred:** widget, Hora, audio and iOS.

## Brand Commitments
- Display name: Jain Panchang / जैन पंचांग.
- Icon: the siddhashila mark (crescent and dot).
- Free, with no ads.

## Evidence on Hand
- Real engine output for any date and city via `python_engine`. Mockups use Delhi, 22 Oct 2026.
- Market research in `python_engine/plans/mobile-market-screens.md`.
- **Not on hand:** testimonials, download numbers, the store URL, or the Delhi 2027 booklet pages. Do not fabricate any of these.

## Product Principles
1. Every date shown is correct, or honestly marked as close to a boundary. Never guess.
2. Today's answers come first: tithi, the next pachchakkhan and the current choghadiya should take one glance.
3. Respect the reader. Large type, plain Hindi, and no clutter or dark patterns.
4. The user's tradition and location decide the dates, never a default the user didn't choose.
5. Offline and private by construction.

## Accessibility & Inclusion
- Elders are primary users: body text 16 sp or larger, touch targets 48 dp, text scaling up to 1.6×, and no gesture-only actions.
- High contrast for outdoor use.
- Meaning never relies on colour alone.
