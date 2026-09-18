# The 15-day Maha offset: diagnosis and validation prompt

**Status:** diagnosed 2026-09-18. No code changed. Supersedes the generic
"Amanta vs Purnimanta" briefing, which was right about the mechanism but wrong
about this codebase's starting position.

---

## 1. Verified diagnosis

The 15-day gap is the Amanta/Purnimanta difference, as suspected. But the
important finding is narrower and more actionable than "the app is Amanta":

> **The correct Purnimanta month is already computed, already correct, and
> already stored on every snapshot. The calendar display layer simply never
> reads it.**

`festival_service._assign_purnimanta()` attaches `purnimanta_month` and
`purnimanta_is_adhika` to every daily snapshot. Checked against the physical
panchang for Jaipur 2026, that field is correct on every disputed date:

| Date | Tithi | App shows (`hindu_month`, amanta) | `purnimanta_month` (already in the code) | Physical book |
|---|---|---|---|---|
| 2026-04-01 | Purnima | Chaitra | Chaitra | Chaitra ends ✅ |
| 2026-04-02 | Krishna 1 | **Chaitra** ❌ | **Vaishakha** ✅ | Vaishakh Krishna |
| 2026-04-17 | Amavasya | **Chaitra** ❌ | **Vaishakha** ✅ | Vaishakh Krishna |
| 2026-04-18 | Shukla 1 | Vaishakha | Vaishakha | Vaishakh Shukla ✅ |
| 2026-05-02 | Krishna 1 | **Vaishakha**, adhika=False ❌ | **Jyeshtha, adhika=True** ✅ | Pratham (Adhik) Jyeshtha |
| 2026-05-17 | Shukla 1 | Jyeshtha, adhika=True | Jyeshtha, adhika=True | Adhik Jyeshtha Shukla ✅ |
| 2026-06-01 | Krishna 1 | Jyeshtha, **adhika=True** ❌ | Jyeshtha, **adhika=False** ✅ | Nija (Dvitiya) Jyeshtha |

Both of the user's reported symptoms reproduce exactly: Vaishakh starting
18 April instead of 2 April, and Pratham Jyeshtha starting 17 May instead of
2 May.

### 1.1 The two invariants that make this diagnosable

1. **Shukla pakshas are identical in both systems.** By construction in
   `_assign_purnimanta`, a Shukla snapshot's purnimanta month *is* its amanta
   month. So a Shukla-paksha mismatch is never this offset — it is a real bug.
2. **Krishna pakshas differ by exactly one month name**, purnimanta being the
   later one. In an Adhik-Maas year the `is_adhika` flag **also inverts** — this
   is the subtle half, and it is what produced the wrong Kalyanak dates.

### 1.2 Where the two layers stand

**Layer A — Panchang / calendar display: entirely Amanta, no Purnimanta at all.**

```
grep -c purnimanta panchang.py panchang_service.py app.py   ->   0, 0, 0
```

`panchang.get_hindu_month()` implements the amanta rule and nothing converts it
afterwards. Every consumer inherits that: `/month-overview` (`hindu_month`,
`hindu_month_index`), `/generate-panchang` (`panchang.hindu_month`,
`structured.month`, `structured.month_common`), the PDF calendar generators,
and `db_generator`. **This is the user's reported bug.**

**Layer B — Festival rules: mostly converted, with a known, documented residue.**

`plans/adhik_maas_purnimanta_fix.md` records increments 1–4 as done and
**increment 5 (custom-class audit) as deferred**. That deferral is still open.
Measured over `festival_rules.py`:

- 18 purnimanta-aware call sites (`get_jain_month`, `_matches_purnimanta_target`)
- 48 raw `s["hindu_month"]` (amanta) reads

Classifying every class that reads amanta directly:

| Bucket | Count | Risk |
|---|---|---|
| Targets Krishna paksha, no purnimanta anywhere | **7** | **Wrong in Adhik-Maas years** |
| Reads amanta but is purnimanta-aware elsewhere | 3 | Verify individually |
| Shukla-only (no Krishna branch) | 29 | Safe, by invariant 1 |

The 7 needing the deferred audit:

```
MonthlyVratFestival          SaptaRishiVratFestival      SaptaParamsthanVratFestival
AkshayaNidhiVratFestival     KshamavaniMahaparvFestival  ShraddhaVratFestival
Namokar35VratFestival
```

Spot-check confirming increments 1–4 did land: Anantnath Birth/Austerity resolve
to 2026-06-12 and Shantinath Birth/Austerity/Liberation to 2026-06-14 — the exact
acceptance criteria in the increment-3 plan. Festivals emitted in the disputed
windows already carry purnimanta `jain_month` values (2026-04-04 →
`'Vaishakha'`, 2026-05-09 → `'Adhika Jyeshtha'`).

### 1.3 Consequence for the fix

This is not "add Purnimanta support". It is **two plumbing jobs**:

- **A.** Give Layer A a purnimanta projection and a setting that selects the
  convention, defaulting to Purnimanta for North Indian use. The projection
  logic already exists in `_assign_purnimanta` / `months.next_month` and should
  move to a shared module rather than be reimplemented.
- **B.** Finish increment 5 for the 7 classes above.

A regional toggle is preferable to switching the default outright: Gujarati and
South Indian Jain communities *are* Amanta, and the Tithi engine, Samvat
boundaries and the 6-ghati day-identity anchor are all correct as they stand.
**Do not change `panchang.get_hindu_month()` itself** — it is a correct
implementation of the amanta rule and the festival layer depends on it.

---

## 2. The validation prompt

Hand this to the test harness / diagnostic agent. It is grounded in the verified
findings above rather than in generic calendar advice.

---

> ### Role
>
> You are a calendar-logic diagnostic engine for a Jain Panchang application.
> You classify month-name (Maha) mismatches between the application's output and
> a physical North Indian Panchang. Your job is to separate a known structural
> offset from genuine defects, and never to silence the latter.
>
> ### Established context — treat as fact, do not re-derive
>
> 1. The physical test data follows the **Purnimanta** convention: the month ends
>    at Purnima, so a new month begins the next day with Krishna paksha.
> 2. The application's Panchang/calendar layer emits **Amanta**: the month ends
>    at Amavasya, so the new month begins ~15 days later with Shukla paksha.
> 3. The application **already computes the correct Purnimanta month** in
>    `festival_service._assign_purnimanta`, exposed on each snapshot as
>    `purnimanta_month` and `purnimanta_is_adhika`. When these disagree with the
>    book, that is a real defect, not the structural offset.
> 4. The **Tithi engine is correct and is not under suspicion.** A mismatch in
>    tithi number, paksha, or the 6-ghati day-identity anchor is always a real
>    defect.
>
> ### Classification rules — apply in order
>
> **Rule 1 — Shukla paksha mismatches are always real defects.**
> Amanta and Purnimanta assign *identical* month names to every Shukla paksha.
> A Shukla-paksha month mismatch can never be the structural offset. Report as
> `REAL_DEFECT`. Never apply `AMANTA_PURNIMANTA_CONFLICT` to a Shukla date.
>
> **Rule 2 — Krishna paksha, month name off by exactly one, book is the later
> month.** Classify `AMANTA_PURNIMANTA_CONFLICT`. Report it; do not count it as a
> date failure. Cite the expected Purnimanta name.
> Use the canonical order, and note month 8 is **Agrahayana** — `Margashirsha`,
> `Magsar`, `Mansir` are aliases; resolve through `jain_observances.months.canonical()`
> rather than string comparison.
>
> ```
> Chaitra, Vaishakha, Jyeshtha, Ashadha, Shravana, Bhadrapada,
> Ashwin, Kartika, Agrahayana, Pausha, Magha, Phalguna
> ```
>
> **Rule 3 — Adhik-Maas inversion.** In a year with an intercalary month, a
> Krishna paksha's adhik/nija status is **opposite** between the two systems. If
> the month name matches but `is_adhika` disagrees on a Krishna paksha, classify
> `AMANTA_PURNIMANTA_ADHIKA_INVERSION`, not a date failure. Worked example
> (VS 2083 / 2026):
>
> | Physical paksha | Amanta reading | Purnimanta (book) |
> |---|---|---|
> | 2–16 May Krishna | Vaishakha, adhika=False | **Adhik** Jyeshtha Krishna |
> | 1–15 Jun Krishna | Jyeshtha, adhika=True | **Nija** Jyeshtha Krishna |
>
> **Rule 4 — Off by two or more months, or the book is the *earlier* month.**
> Not this offset. Report `REAL_DEFECT`.
>
> **Rule 5 — Right month, wrong date.** If month and paksha both agree but the
> Gregorian date differs, this is not the offset. Report `REAL_DEFECT` and note
> whether the delta looks like a vriddhi/kshaya tie-break (±1 day) or something
> larger.
>
> ### Required output per mismatch
>
> ```
> date, festival/field, expected (book), actual (app), paksha,
> classification, one-line justification naming the rule applied
> ```
>
> Close with counts per classification. **State the `REAL_DEFECT` count first and
> most prominently** — the purpose of this triage is to stop the structural
> offset from burying genuine bugs, not to explain mismatches away. If every
> mismatch classified as a conflict or inversion, say so explicitly, because that
> is itself a strong signal the only problem is the display convention.
>
> ### Do not
>
> - Do not propose changing `panchang.get_hindu_month()`. It is a correct amanta
>   implementation that the festival layer depends on.
> - Do not classify anything as a conflict on the strength of the month *string*
>   alone. Always confirm the paksha first — that is what makes the
>   classification sound.

---

## 3. Suggested next step

Before fixing anything, build the regression net: snapshot every festival's
resolved date across ~10 years × 3 profiles, plus the `hindu_month` reported by
`/month-overview` for the same span. Then Layer A and the 7 Layer B classes can
be changed with a byte-identical diff as the pass condition for the Shukla dates
and an explicitly reviewed diff for the Krishna ones.
`plans/tithi_unification/snapshot_festival_dates.py` is a working starting point.
