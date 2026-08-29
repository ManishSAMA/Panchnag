# Tirthankara Kalyanak data audit — findings and open items

Session date: 2026-08-26. Source: user-provided PDF "जैन पंचांग - 24 तीर्थंकर कल्याणक
(संपूर्ण वर्ष)" (Vrindavan / Uttarapurana / Ashadhara's Sanskrit Jin Kalyanaka Mala),
cross-checked against `tests/tirthankara_kalyanaks_data.json` (a pre-existing structured
parse of the same source document, 288 records).

## The amanta/purnimanta relationship (read this before touching any Krishna-paksha kalyanak entry)

`registry.py`'s `jain_month` field for a `SingleTithi` rule is the **amanta** (lunar,
Shukla-paksha-first) month used to filter `snapshots` in `festival_rules.py`. For a
**Krishna**-paksha entry, `festival_service.py`'s post-processing (`generate_jain_festivals`,
"Apply Purnimanta Shift" block) always displays it as **amanta_month + 1**. Your source PDF's
own month-section labels (e.g. "चैत्र कृष्ण पक्ष") are **purnimanta** — confirmed two
independent ways: Diwali is universally "Kartika Krishna Amavasya" (purnimanta), and
Janmashtami's well-known dual naming (purnimanta "Bhadrapada Krishna 8" = amanta "Shravana
Krishna 8", the same physical day).

**So: for a Krishna-paksha kalyanak entry, `jain_month` must be set to (PDF's stated month − 1
month), never the PDF's month directly.** Getting this wrong doesn't error or look obviously
broken — it just displays the event exactly one lunar month later than the source says, which
only shows up if you cross-check against the source. Shukla-paksha entries need no adjustment
(the month name is identical in both systems).

## Fixed this session (branch `wip/festival-engine-checkpoint`)

- **65 registry.py kalyanak entries** had `jain_month` set directly to the PDF's month name
  (i.e. the bug above), each displaying one month later than the source states. All 65
  corrected; see `KalyanakAmantaMonthCorrectionTest` in `tests/test_jain_festivals.py` for
  representative regression coverage, and the audit/fix scripts referenced below for the full
  list.
- **3 missing kalyanak entries added**: Sumatinath Liberation (Chaitra Shukla 9, Vrindavan
  only — distinct from the existing Ekadashi-11 entry shared by all three sources), Parshvanath
  Omniscience (Chaitra Krishna 4, Vrindavan+Ashadhara — Uttarapurana already had its own
  divergent day-14 version), Anantnath Liberation (Chaitra Krishna 4, Vrindavan only — distinct
  from the existing Amavasya-day entry).
- **2 stale test fixtures corrected** (not code bugs — the tests' own tithi assertions already
  agreed with the app; only the hardcoded `start_date` was wrong): `test_mahavir_jayanti_resolution`
  (2026-03-30 → 2026-03-31) and `test_paryushan_profile_specific_dates`'s Tapagachchha Samvatsari
  assertion (2026-09-14 → 2026-09-15).

## Fixed later this session: the same amanta/purnimanta bug, baked into code this time

The registry-data fix above covers `SingleTithi`-family entries where `jain_month` is a plain
string field. But the identical mistake — filtering `s["hindu_month"]` (raw amanta) directly
against a purnimanta-sounding literal, without the +1 shift Krishna-paksha targets need — also
exists **hardcoded inside custom rule classes** in `festival_rules.py`. Found via user cross-
check against an independently printed panchang: the whole Diwali/Mahavir-Nirvana/Chaturmas
cluster was duplicated a lunar month late (Kartika → wrongly landing on Agrahayana), alongside
Karwa Chauth, Ahoi Ashtami, Dampatya Ashtami, Gyan Trayodashi, and Dhan Trayodashi (Dhanteras)
all resolving a month late — confirmed to reproduce in **both** 2026 and 2027 (i.e. not an Adhik
Maas artifact; every one of these classes filters `s["hindu_month"].upper() in ["KARTIKA", ...]`
directly, when their target tithis are Krishna-paksha and so need `get_jain_month(s) ==
"KARTIKA"` instead — the same helper `ChaitraLabdhiVidhanFestival` already used correctly).

Fixed in `KartikaAmavasyaMahaviraNirvanaFestival`, `SplitDayAhoiKarwaDampatyaFestival`,
`GyanDhanTrayodashiFestival`, and `DiwaliChaturmasNishthapanFestival` by switching their month
filter from raw `s["hindu_month"]` to `get_jain_month(s)`. Verified: exactly the 10 affected
occurrence ids shifted to their correct Kartika dates in 2026 (nothing else in the 399-occurrence
festival list changed), and the same fix corrects 2027 too.

**Not fixed, flagged for a dedicated audit:** this exact `s["hindu_month"].upper() in [...]`
raw-amanta pattern (not `get_jain_month()`) appears **40+ times** across `festival_rules.py`,
in dozens of other classes. Most are probably fine — a class whose target tithi is Shukla-paksha
only doesn't need the shift, and many of the 40+ are exactly that. But some unknown subset may
share this same Krishna-paksha bug undetected. This needs the same kind of case-by-case check
done for the 4 classes above, not a blanket find-replace (an incorrect blanket change could
break a class that's currently right). This is a natural companion to the still-unexecuted
`festival_rules.py` duplication refactor (Family A/B/C plan, see memory) — a shared, correctly
`get_jain_month()`-based helper would prevent this whole bug class at the source.

**Also flagged, separate and smaller:** `SplitDayAhoiKarwaDampatyaFestival`'s docstring claims
Ahoi Ashtami uses a "Pradosha (evening) Vyapini" day-selection rule, distinct from Dampatya
Ashtami's "Udaya Tithi" rule — but the code doesn't actually implement that distinction; both
just take the first sunrise-tithi Ashtami day. This is why, after the month fix, Ahoi Ashtami
lands on 2026-11-02 while an independently printed panchang says 2026-11-01 — a real, un-
implemented feature gap, not a regression from the month fix above.

## NOT fixed — needs your call before anyone touches it

### 1. `KarmaNirjaraVratFestival` vs `jain_observances/vrats/karma_nirjara.py`
Live code (tested, wired up) targets Shukla Chaturdashi (14), no kshaya handling. A dead,
never-imported module targets Shukla Panchami (5) with a Chaturthi (4) kshaya fallback. Two
different definitions of "Karma Nirjara Vrat". Unresolved — pick one before editing either file.
Currently causes `KarmaNirjaraVratTest.test_karma_nirjara_vrat_resolution` to fail (expects 5
occurrences, gets 4) — pre-existing, unrelated to this session's changes.

### 2. Snapshot-timing inconsistency in `festival_service.py` (architectural, wide blast radius)
> **Update:** the Krishna-paksha *month-naming* consequence of this is now fixed — see
> "adhik-maas purnimanta resolution" below. The underlying dual-moment snapshot
> (`tithi` at plain sunrise vs `hindu_month` at +2.4h) is still there for other fields.

In `generate_jain_festivals`'s snapshot-building loop: `tithi`/`paksha`/`tithi_in_paksha` are
computed at **plain sunrise** (`sunrise_jd`), but `hindu_month`, `jain_tithi`, `jain_paksha` are
computed at **sunrise + 2.4 hours** (`reference_jd`). On any day where a tithi transition falls
inside that 2.4-hour window, the resulting snapshot has fields describing two different moments
— e.g. `hindu_month` says the new month already started while `paksha`/`tithi_in_paksha` still
say the old tithi. Confirmed concretely for 2026-03-19: plain-sunrise tithi is `Krishna 15`
(Amavasya, the tail of the *previous* amanta month), but `hindu_month` (2.4h later) already
reads `"Chaitra"` (the *new* month) — a combination that doesn't correspond to any single real
moment.

This is what breaks `ChaitraAmavasyaKalyanakVarshantTest`:
`ChaitraAmavasyaKalyanakVarshantFestival.resolve()` (festival_rules.py) filters snapshots by
`hindu_month == "CHAITRA"` then searches for `paksha=="Krishna" and tithi_in_paksha==15` within
them — and picks up **both** the spurious 03-19 snapshot and the genuine 04-17 one, so
`first_amavasya` (used for Ananthnath/Aranath Moksha) lands on the wrong, spurious date while
`last_amavasya` (Vikram Samvat Varshant) correctly lands on 04-17.

Since essentially every rule class reads `hindu_month` alongside `paksha`/`tithi_in_paksha`
as if they were one consistent state, this could silently affect other rules near other
month-transition boundaries throughout the year — not just this one festival. **Deliberately
not touched this session** — fixing the snapshot builder's timing model needs its own
dedicated, carefully-tested pass (it's astronomical-timing-sensitive code every rule depends
on), not a tack-on fix. `test_chaitra_amavasya_kalyanak_varshant_resolution_2026` is left
failing, understood, and documented here rather than papered over.

## Fixed later: adhik-maas purnimanta resolution (`plans/adhik_maas_purnimanta_fix.md`)

`_build_snapshots` now attaches `purnimanta_month` / `purnimanta_is_adhika` to every
snapshot, derived from the **next chronological Shukla paksha's** amanta month/adhika
(a Krishna paksha shares its purnimanta month with the Shukla paksha that ends at that
month's Purnima). `SingleTithiFestival` / `MultiDayFestival` match Krishna-paksha entries
against those fields; `get_jain_month()` and both display paths use them too. Single source
of truth for month names + the shift is the new `jain_observances/months.py`.

This corrected three latent bug classes at once:
1. **Adhik-Maas Krishna flip** (the reported bug). VS 2083 = Adhika Jyeshtha. A Krishna
   paksha's adhik/nija status is *opposite* in amanta vs purnimanta reckoning, so filtering
   `not s["is_adhika"]` (amanta) put every Jyeshtha-Krishna Kalyanak in the *Adhik* paksha
   (2-16 May 2026) instead of the *Nija* one (1-15 Jun). Anantnath J&T 14 May → **12 Jun**;
   Shantinath J-T-M 16 May → **14 Jun**; Shreyansnath/Vimalnath/Ajitnath conceptions likewise.
   Confirmed against Pt. Jaini Jiyalal Panchang.
2. **Item #2 above (snapshot-timing) — now effectively resolved for Krishna month-naming.**
   Deriving purnimanta identity from the next Shukla day (mid-paksha, away from the month
   boundary) sidesteps the 2.4h `reference_jd` ambiguity at the Amavasya. Diwali 2027 moved
   from a wrong **2027-09-30** to the correct **2027-10-29**; `ChaitraAmavasyaKalyanakVarshantTest`
   now passes; ~10 Krishna-Amavasya-day Kalyanaks that were silently dropped (Anantnath/Aranath
   Moksha on Chaitra Kr Amavasya, Shreyansnath Omniscience on Magha Kr Amavasya, …) now appear.
3. **"Margashirsha" vs "Agrahayana" spelling mismatch.** `get_hindu_month` emits "Agrahayana";
   ~16 registry entries store `jain_month: "Margashirsha"` and were matched with `==`, so they
   produced nothing. `months.canonical()` collapses the aliases → Pushpadanta / Arahnath /
   Naminath / Sambhavnath / Sheetalnath entries in that month now resolve.

Verification: 274/274 SingleTithi Kalyanak occurrences across 2026 + 2027 display the
purnimanta month/paksha their registry entry intends (0 mismatches); full 2027 (non-adhik)
diff is additive only (previously-missing entries), nothing mis-shifted.

**Still open:** the ~30 custom rule classes that filter raw `s["hindu_month"].upper() in [...]`
+ `is_adhika` for Krishna-paksha targets are not individually audited for adhik years. The
2026-relevant one (`MonthlyVratFestival`, targets Jyeshtha) plus the KALYANAK_AUDIT-fixed
Kartika cluster are covered by tests and green; the rest are mostly Shukla-only or non-adhik-
month and lower risk. Companion to the still-unexecuted festival_rules.py dedup refactor.

## Fixed later: pradosh-vyapini day-selection for the Diwali / Mahavir Nirvana cluster

The engine resolved every tithi by **udaya (sunrise)** only. Diwali / Mahavir Nirvana,
Dhanteras and Ahoi Ashtami are **pradosh (evening) vyapini** -- observed on the day the
target tithi prevails at sunset. Whenever that tithi begins during the day and ends before
the next sunrise, udaya lands the festival one day late. Concretely for 2026: Kartik Krishna
Amavasya runs 8 Nov 11:28 -> 9 Nov 12:31 IST, so Mahavir Nirvana Kalyanak / Jain Diwali
belongs on **8 Nov** (evening), not the udaya-Amavasya **9 Nov** the app was emitting -- the
single most important Jain date of the year, one day off. Dhanteras 7 -> 6 Nov, Ahoi 2 -> 1 Nov.

Fix: `_build_snapshots` records the sunset tithi (`evening_tithi` / `evening_paksha` /
`evening_tithi_in_paksha`); `festival_rules._pradosh_days()` selects days by it; a `day_rule`
config key (`"pradosh"`) routes `SingleTithiFestival`; and `KartikaAmavasyaMahaviraNirvana`,
`DiwaliChaturmasNishthapan`, `GyanDhanTrayodashi`, `SplitDayAhoiKarwaDampatya` (Ahoi only --
Dampatya stays udaya, Karwa Chauth stays moonrise) use it directly. Jain New Year is now
computed as **Mahavir Nirvana + 1 day**; a `skip_relabel` post-processor flag lets it keep
its "Kartika Shukla Pratipada" labels on a day whose udaya paksha is still Krishna.
`PradoshVyapiniDiwaliClusterTest` covers 2026 + the 2027 (normal-year) cascade.

**Not implemented:** aparahna / nishita / moonrise vyapini. Bhai Dooj (aparahna) and Karwa
Chauth (moonrise) stay on udaya -- Bhai Dooj can be +1 in years where Shukla Dvitiya is short.

## Reusable audit tooling (scratchpad, not committed)

The cross-reference approach (parse `tests/tirthankara_kalyanaks_data.json`, apply the
amanta/purnimanta shift, compare per-(tirthankara, event, source) against `registry.py`) lives
in this session's scratchpad as `kalyanak_audit.py` / `build_fixlist.py` / `patch_registry.py`.
Worth turning into a proper `tests/` script if the kalyanak dataset is edited again.
