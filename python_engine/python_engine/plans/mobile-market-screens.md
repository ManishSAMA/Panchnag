# Market research: must-have screens for a Jain Panchang app

Research date: 2026-10-27. This document compares the leading Jain panchang apps against our beta design ([`mobile-ui-design.md`](mobile-ui-design.md)) and against the locked beta scope in [`mobile-app-flutter.md`](mobile-app-flutter.md) §1.

The sources are store listings and developer sites, not hands-on use. Features marked Premium sit behind a paywall in that app.

## 1. Apps surveyed

| App | Reach | Notable for |
|---|---|---|
| Jain Panchang (Don't Know Technologies, `com.dkt.jainpanchang`) | 100K+ downloads, 4.8★ (≈2.6K reviews), updated Oct 2026 | Ad-free, offline, EN/HI/GU. Samudays: Tapagach (1-tithi and 2-tithi), Anchal, Khartar, Sthanakwasi. Full pachchakkhan timings, Asajjay calculator, compass |
| Jain Panchang & Kalyanaks (Jain Darshan, `com.jaindarshan.panchangtithi`, iOS id790266336) | 4.5★ (≈1.5K) on iOS, #162 in the free chart | Widgets (home and lock screen), Daily Niyam tracker, pachchakkhan audio, My Events, 100 years of data, ₹999 Premium |
| Jain Panchang (jainpanchang.in) | Says it has 500K+ Android downloads and has been around since 2013–14 | Navkarshi, Hora, a yearly kshay/vruddhi list, Kamdi Kal, Shubh Yog, pachchakkhan audio, e-books, and a community hub (Sangh updates, family alerts) |
| Jain Tithi (`com.jain.android.tithi`) | 10K+, 4.8★ | Reminder the day before; Navkarsi, Porsi, Sadh-Porsi, Purimaddh, Avaddh and Chauvihar by location |
| jainpanchang.app (web/Android) | New | Tabs: आज · मासिक · पच्चक्खाण · सेटिंग्स (Today · Monthly · Pachchakkhan · Settings); HI/GU/BN/EN; senior high-contrast mode |
| Digambar apps (Vitragvani, Jain-Calendar ABCOM, Jain Parv Calendar) | Small | Tithi, sunrise/sunset, parva marking, notes, japa counter, widgets. Mostly dated |
| Drik Panchang (Hindu, the reference leader) | Market leader | Countdown timer on each running muhurta, custom tithi reminders by Hindu or Gregorian date, DST handling. Criticised as cluttered and overwhelming |

## 2. Screen-by-screen comparison

✅ = in our beta design · ⚠️ = partly covered · ❌ = missing

### Tier 1: every serious Jain app has it (must have)

| Screen / feature | Market | Ours |
|---|---|---|
| **Today dashboard**: tithi, sunrise/sunset, the day's parva/kalyanak, nakshatra | All | ✅ |
| **Pachchakkhan timings**: Navkarsi, Porsi, Sadh-Porsi, Purimaddh, Avaddh, Chauvihar from local sunrise/sunset | All 5 major Shwetambar apps; one has a whole tab for it | ❌ Placeholder only, deferred to post-beta. **This is the biggest gap.** |
| **Choghadiya, day and night**, current slot highlighted | All | ✅ (with a countdown, as Drik has) |
| **Monthly calendar** with Ashtami, Chaudas and Panchami highlighted | All. Jain Darshan colour-codes tithis green/yellow/red for green-vegetable (lilotri) restrictions | ⚠️ We show category dots, but parva tithis are not highlighted as such |
| **Festival / kalyanak list** with reminders | All | ✅ |
| **Notifications**: day-before reminders for tithis, events and kalyanaks | All. Reviewers ask for reminders on *any* tithi, not just 8 and 14 | ⚠️ Per festival only. No parva-tithi reminder (every Ashtami/Chaudas) |
| **Tradition (sect) selection** | All. DKT separates the **1-tithi and 2-tithi Tapagach** views | ⚠️ We have 3 Shwetambar profiles. The 1-tithi/2-tithi split is not modelled |
| **Location**: GPS or city | All | ✅ |
| **Gujarati language** | Every Shwetambar app with traction offers EN/HI/GU | ❌ Beta is EN + HI only |
| **Offline, ad-free** | Top-rated apps lead with this | ✅ |

### Tier 2: common, and expected by regular users (should have)

| Screen / feature | Market | Ours |
|---|---|---|
| **Home-screen widget** (today's tithi, choghadiya, navkarsi) | Jain Darshan, Arihant, Jain Parv; a reviewer singles it out | ❌ Explicitly left out |
| **Hora** | jainpanchang.in, DKT, Jain Darshan (whose users complained when it was removed) | ❌ Deferred |
| **Kshay/Vruddhi yearly list** | jainpanchang.in | ⚠️ Visible in the month grid only |
| **Kalyanak browse by Tirthankar**, with search | Jain Darshan, DKT | ❌ |
| **Special nakshatra days**: Panchak, Vichudo, Guru/Ravi Pushya, Rohini | DKT, jainpanchang.in | ⚠️ Rohini only |
| **Pachchakkhan audio** (recited sutras) | 4 of 5 major apps | ❌ Licensing and recording are needed, so this is post-beta |
| **Personal tithi-based events**: a yearly reminder on a birth tithi or punya tithi | Jain Darshan (Premium), Drik, jainpanchang.in | ❌ |
| **Year/range navigation** (any year) | All. Jain Darshan offers 100 years | ✅ 2016–2040 |
| **Dark mode** | Most | ✅ Tokens planned |
| **Share** (kalyanak/day image) | Jain Darshan | ✅ |
| **Senior / high-contrast mode** | jainpanchang.app | ⚠️ Large type by default, no separate mode |

### Tier 3: differentiators (nice to have, post-beta)

Daily Niyam tracker (Chaudah Niyam, streaks); Asajjay (times when swadhyay, scriptural study, is restricted) calculator; Kal Maryada; Kamdi Kal; Shubh Yog / muhurat (Rahu Kalam, Abhijit); a daily quote; e-books; compass; Apple Watch; calendar sync; community features (Sangh updates, family alerts, business directory). The last of these needs accounts and servers, which our offline, no-account decision rules out.

## 3. What this means for our beta

1. **Promote pachchakkhan timings into beta.** Every competitor has them, and one app makes them a primary tab. They are cheap to compute: all are fractions of the day measured from sunrise and sunset, which we already have at parity. The traditional split is about ¼ of the day for Porsi, about ⅜ for Sadh-Porsi, and so on, with Chauvihar before sunset. Navkarsi is sunrise + 48 min. The exact rules and any samuday differences need a cited source before we write tests.
2. ~~Add Gujarati~~ **Decided 2026-10-27: no Gujarati.** The app stays English + Hindi.
3. **Highlight parva tithis** (Ashtami, Chaudas, Panchami, Purnima/Amavasya) in the Month grid and on Today, and add reminders for every parva tithi, not just per festival.
4. **Model the 1-tithi/2-tithi Tapagach choice**, or confirm that our Tapagachchha profile matches one of them, and label it that way.
5. **Make the widget a Phase 6 item** instead of "not designed".
6. **Add a kshay/vruddhi year list and kalyanak browsing by Tirthankar.** Both reuse data we already compute.

**Decided 2026-10-27:** pachchakkhan is in the beta (see [`mobile-ui-design.md`](mobile-ui-design.md) §3 · Pachchakkhan for its rules). The tabs are **आज · माह · पच्चक्खाण · पर्व** (Today · Month · Pachchakkhan · Festivals). Choghadiya would move into Today, keeping its countdown, plus a full-screen view opened from there. This matches jainpanchang.app's layout and puts the most-used daily lookups one tap away.

## Sources

- [Jain Panchang (DKT), Google Play](https://play.google.com/store/apps/details?id=com.dkt.jainpanchang&hl=en)
- [Jain Panchang & Kalyanaks, App Store](https://apps.apple.com/in/app/id790266336)
- [Jain Panchang & Choghadiya, Google Play](https://play.google.com/store/apps/details?id=com.jaindarshan.panchangtithi)
- [jainpanchang.in](https://jainpanchang.in/)
- [jainpanchang.app](https://jainpanchang.app/)
- [Jain Tithi, Google Play](https://play.google.com/store/apps/details?gl=US&hl=en&id=com.jain.android.tithi)
- [Jain Tithi Calendar, Google Play](https://play.google.com/store/apps/details?id=com.nitin.jainpanchang&hl=en_US)
- [Jain Panchang (mosync), Google Play](https://play.google.com/store/apps/details?id=com.mosync.app_Jain_Panchang&hl=en)
- [Vitragvani, App Store](https://apps.apple.com/in/app/vitragvani/id1293660812)
- [Jain Parv Calendar, App Store](https://apps.apple.com/us/app/id1132817716)
- [Drik Panchang, App Store](https://apps.apple.com/app/id1321271821)
- [Top 5 panchang apps review, shubhpanchang.com](https://shubhpanchang.com/blog/top-5-panchang-apps-in-india-a-users-honest-review)
