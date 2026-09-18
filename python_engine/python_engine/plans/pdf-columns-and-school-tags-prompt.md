# Prompt: PDF column restructure + Kalyanak school-consensus tags

**Written 2026-09-18. Not implemented — this is the spec to hand to the implementing session.**

Section 1 is what I verified in the codebase, so the implementer starts from
facts rather than assumptions. Section 2 is the prompt itself.

---

## 1. Ground truth (verified, not assumed)

### 1.1 Four corrections to the brief

**a) The third school is `Ashadhara`, and the first is recorded as `Vrindavan`, not
"Vaishnav".** The registry's `sources` field holds these exact strings:

| # | `sources` string | Registry entries |
|---|---|---|
| 1 | `Vrindavan` | 121 |
| 2 | `Uttarapurana` | 118 |
| 3 | `Ashadhara` | 118 |

These come from the Sanskrit Jin Kalyanaka Mala cross-reference recorded in
`jain_observances/KALYANAK_AUDIT_NOTES.md`.

**b) The PDF's existing tithi column is ALREADY the Jain Tithi.**
`generate_hindi_calendar_pdf.py:268` computes
`reference_jd = jd_sr + JAIN_TITHI_OFFSET_DAYS` and derives the "पक्ष एवं तिथि"
column from it. So this is **not** a change of that column — it is *adding* a
Hindu (sunrise) Tithi column beside it, and relabelling the existing one.

**c) Festivals are ALREADY mapped on the Jain Tithi.** Constraint 2 of the brief
is already satisfied: the whole festival engine resolves against the 6-ghati
anchor (`plans/tithi_unification/design.md`). `_build_snapshots` sets each
snapshot's `tithi` from `sunrise + JAIN_TITHI_OFFSET_DAYS`. **Verify this holds;
do not rebuild it.**

**d) This project does not use Skyfield or SciPy.** Neither is imported anywhere
nor listed in `requirements.txt`. All astronomy goes through **Swiss Ephemeris**
(`pyswisseph`) via `astronomy.py`. `de421.bsp` is a leftover. **Do not introduce
Skyfield** — it would produce a second, subtly divergent source of truth for
sunrise, which is the anchor the entire Jain Tithi definition rests on.

### 1.2 The consensus tag is a read, not a computation

Generated occurrences already carry `sources`: 373 of 374 occurrences for 2026.
The tag is a direct read of that list. Distribution across the 209 registry
entries:

| Combination | Count | Tag |
|---|---|---|
| All three | 105 | `(1, 2, 3)` |
| **No school** (e.g. `Jain Traditions`, `Pt. Jaini Jiyalal Panchang`) | **74** | **no tag at all** |
| Partial (`(1,)`, `(2,)`, `(3,)`, `(1,2)`, `(1,3)`, `(2,3)`) | 30 | as listed |

The 74 no-school entries are the case the brief does not cover. They are ordinary
observances, not Kalyanaks, and must render with **no bracket** — not `()`, not
`(0)`.

### 1.3 Same-date duplicates must be merged

Where schools disagree on a Kalyanak's tithi, the registry models it as
**separate entries**. Usually they land on different dates and need nothing
special. But sometimes they resolve to the *same* date and appear as two rows of
the same name. In 2026 there are exactly three:

```
2026-03-18  Shri Anantnath Ji - Liberation Kalyanak    tags (1,3) and (2,)
2026-03-18  Shri Anantnath Ji - Omniscience Kalyanak   tags (1,3) and (2,)
2026-03-18  Shri Arahnath Ji - Liberation Kalyanak     tags (1,3) and (2,)
```

Each must collapse to a single line with the **union** of the tags —
`Shri Anantnath Ji - Liberation Kalyanak (1, 2, 3)` — not two adjacent lines.

Note the recurring vrats (Rohini, Pakhi Chaudas, Bhaktambar, Namokar Mahamantra)
also repeat their names across many dates. Those are genuine separate
occurrences; merge **only within a single date**.

### 1.4 The Hindu Maas column has an open decision

`generate_hindi_calendar_pdf.py:280` calls `get_hindu_month(reference_jd)`, which
is **Amanta**. That is the ~15-day offset reported against the printed North
Indian panchang. `panchang.get_purnimanta_month()` now exists and the web layer
defaults to Purnimanta, but **the PDF generators were deliberately not switched**
— see `plans/amanta-purnimanta-offset.md` §3.

This must be decided before the PDF is regenerated, or the new PDF will print
month names 15 days out while the app prints them correctly.

### 1.5 There are three near-duplicate generators

```
generate_hindi_calendar_pdf.py            413 lines
generate_hindi_calendar_pdf_2027_2028.py  381 lines
generate_hindi_calendar_pdf_2028_2029.py  381 lines
```

The latter two differ in 52 lines, 24 of which are a mechanical Hindi
month-name-plus-year table. Do not add a fourth copy.

---

## 2. The prompt

---

> ### Task
>
> Restructure the Hindi Panchang PDF's table schema and add school-consensus
> tags to the festival column, in `python_engine/python_engine/`.
>
> ### Before writing code
>
> Read `plans/pdf-columns-and-school-tags-prompt.md` §1, `docs/calculations.md`,
> and `jain_observances/KALYANAK_AUDIT_NOTES.md`. Four things in the original
> brief are wrong about this codebase and §1 corrects them — most importantly,
> the existing tithi column is already the Jain Tithi, and this project uses
> Swiss Ephemeris, not Skyfield.
>
> This project's `CLAUDE.md` applies: **TDD is non-negotiable**, every change
> starts from a failing test, and **you wait for commit approval**.
>
> ### Part A — Column structure
>
> Output exactly these columns, in this order:
>
> | # | Header | Source |
> |---|---|---|
> | 1 | दिनांक | Gregorian date |
> | 2 | वार | `get_vara_from_date` → `WEEKDAYS_HINDI` |
> | 3 | हिन्दू मास | Lunar month — see the convention decision below |
> | 4 | हिन्दू तिथि | Tithi at **plain sunrise** (`jd_sr`) — **new column** |
> | 5 | जैन तिथि | Tithi at **`jd_sr + JAIN_TITHI_OFFSET_DAYS`** — this is the **existing** column, relabelled |
> | 6 | सूर्योदय | `get_sunrise` |
> | 7 | सूर्यास्त | `get_sunset` |
> | 8 | पर्व एवं त्यौहार | Festivals, Kalyanaks, observances |
>
> Both tithi columns keep the existing paksha formatting (`शुक्ल`/`कृष्ण`,
> with `पूर्णिमा` and `अमावस्या` as special cases).
>
> The चन्द्रोदय and चन्द्रास्त columns are dropped by this schema. **Confirm
> that is intended before deleting the code that computes them** — the brief
> lists eight columns and does not mention moonrise/moonset, but does not
> explicitly say to remove them either.
>
> Column widths must re-sum to 100%. Verify the table does not overflow the page
> box at the current font size, since two tithi columns replace one.
>
> ### Part B — Festival column, mapped on Jain Tithi
>
> Festivals must map **exclusively** on the Jain Tithi (column 5), never the
> Hindu Tithi and never Gregorian midnight. The engine already does this — write
> a test that **proves** it rather than changing the mapping. A good proof: pick
> a date where the sunrise tithi and the 6-ghati tithi differ, and assert the
> festival lands on the 6-ghati day.
>
> ### Part C — School-consensus tags
>
> Append a bracketed tag listing every school observing that festival on that
> date, using `1 = Vrindavan`, `2 = Uttarapurana`, `3 = Ashadhara`, always
> ascending, comma-space separated:
>
> ```
> Shri Munisuvratnath Janam (1, 2, 3)
> Shri Munisuvratnath Janam (2, 3)
> ```
>
> Read each occurrence's `sources` list. Match case-insensitively by substring,
> as `app.py`'s export filter already does.
>
> Three rules the brief does not cover:
>
> 1. **No recognised school → no bracket.** 74 registry entries have sources
>    like `Jain Traditions`. Emit the name alone — never `()` or `(0)`.
> 2. **Merge same-name-same-date entries** into one line with the union of their
>    tags. §1.3 lists the three 2026 cases; they must render as `(1, 2, 3)`.
>    Merge only within a single date.
> 3. **Hindi names.** The festival column renders Hindi (`name_hindi`). The tag
>    is numeric, so it is script-neutral — append it after the Hindi name and
>    confirm it does not break RTL/Devanagari shaping in the PDF renderer.
>
> ### Part D — Do not add a fourth copy of the generator
>
> The three `generate_hindi_calendar_pdf*.py` files differ by 52 lines, mostly a
> mechanical month-name table. Parameterise by year range into one module and
> have the three entry points call it. If that turns out to be a bigger job than
> the column change, say so and do the column change in one place first — but do
> not duplicate the new schema into three files.
>
> ### Decision required before you start
>
> **Column 3 is currently Amanta and the web app now defaults to Purnimanta.**
> The PDF generators were deliberately left on `get_hindu_month`; the projection
> is `panchang.get_purnimanta_month`. Ask the user which the printed calendar
> should use before generating any PDF. Getting this wrong prints month names 15
> days out — exactly the discrepancy reported against the physical panchang.
> Do not guess.
>
> ### Verification
>
> - `pytest tests` and `pytest tests_ui` stay green.
> - Generate one PDF and diff the rendered table against the previous edition:
>   every date's Jain Tithi must be **unchanged** (it is the same column, only
>   relabelled). If any Jain Tithi moves, you have changed the anchor — stop.
> - Spot-check the three §1.3 merge cases in the 2026 output.
> - Spot-check one all-three festival, one partial, and one no-school festival.

---

## 3. Suggested follow-up

The two remaining commands the user mentioned are not covered here. When they
arrive, check whether they touch the same three generator files — if so, do the
Part D consolidation first so all three changes land in one place.
