# Case study: Bhaktambar Vrat Prarambh on Saptami, 9 May 2026

**Verdict: `EXPECTED_BEHAVIOR`** — deliberate, documented and test-pinned. Not an
off-by-one, not Adhik Maas, not a time-of-day anchor.

**But the rule itself rests on a domain judgement that deserves review.** §6 sets
out the two readings and what would change under each. No code was changed.

---

## 1. Root cause

The trigger is not Ashtami. It is **Chaturdashi**.

`BhaktambarVratFestival.resolve()` (festival_rules.py:553) spans Ashtami (8) to
Chaturdashi (14) — seven tithis — then applies this, at line 607:

```python
# Kshaya Rule: minimum 7 days guarantee
if natural_days < 7:
    has_kshaya = True
    if tithi_dates[7]:
        start_day = tithi_dates[7][0]      # <-- pull back to Saptami
```

In the Adhik Jyeshtha Krishna paksha of May 2026, **Chaturdashi is kshaya**:

| Date | Tithi in paksha |
|---|---|
| 2026-05-09 | 7 (Saptami) ← Vrat Prarambh |
| 2026-05-10 | 8 (Ashtami) |
| … | 9, 10, 11, 12 |
| 2026-05-15 | **13 (Trayodashi)** |
| 2026-05-16 | **15 (Amavasya)** — 14 never prevails at a 6-ghati mark |

So `tithi_dates[14]` is empty. `end_day` falls back to the last available target
date, 15 May (Trayodashi). Ashtami → that end is **6 civil days**, under the
seven-day floor, so the rule extends the start backwards one day into Saptami.

The premise in the brief — "Ashtami is present and not skipped, yet the Vrat is
mapped to Saptami" — is accurate but points at the wrong tithi. Ashtami's
presence was never the condition. The condition is the **length of the whole
8→14 window**, which Chaturdashi's kshaya shortened.

---

## 2. Directive 1 — Prarambh on the eve of Ashtami?

**The code does not model this, and I cannot adjudicate the theology.**

Nothing in `BhaktambarVratFestival` distinguishes "commencement of the fast"
from "the primary observance day". There is no eve-of concept, no separate
Prarambh anchor. The `(प्रारंभ)` tag in the PDF is added generically by
`build_festival_index()` to the first day of *any* multi-day span — it is a
rendering label, not a rule.

The Saptami start is a **side effect of a day-count guarantee**, not an
implementation of an eve-of-Ashtami doctrine. If the tradition does mandate
commencement during late Saptami, the current output happens to coincide on
these dates — but it would then be right for the wrong reason, and wrong on the
20 of 25 occurrences in 2026 that start on Ashtami.

That distinction matters for the fix, so it needs your ruling.

## 3. Directive 2 — time-of-day anchor?  **Rejected**

Measured for 9 May 2026 (Jaipur):

```
2026-05-09  6-ghati tithi = 22 (Krishna Saptami), ends 14:03
2026-05-10  6-ghati tithi = 23 (Krishna Ashtami), ends 15:07
```

Ashtami does begin on the **afternoon** of 9 May (14:03) — so the hypothesis is
reasonable on the face of it. But the rule never consults it. It reads
`tithi_in_paksha`, which comes from the 6-ghati snapshot field, and there is no
pradosh or evening evaluation anywhere in this class. The snapshot's
`evening_tithi` field exists but only `SplitDayAhoiKarwaDampatyaFestival` uses
it.

The coincidence is worth noting for §6, but it is not the mechanism.

## 4. Directive 3 — Adhik Maas interference?  **Rejected**

Three independent checks:

1. **The paksha block is not split.** Grouping uses amanta `hindu_month` +
   `is_adhika`; across 2–16 May 2026 both are constant (`Vaishakha`, `False`).
   The block is contiguous and complete.
2. **The adhika flag never touches date selection.** It is read once, after
   `start_day` and `end_day` are already fixed, and only feeds `month_title` and
   `occ_id`. The class already uses `purnimanta_is_adhika` correctly — which is
   why the row is labelled "Adhik Jyeshtha" and matches the book.
3. **It happens more in normal years.** 2027 carries no Adhik Maas and has
   **8** Saptami starts against 2026's **5**.

## 5. Directive 4 — ripple effect

Every Saptami start carries `has_kshaya=True`. None is isolated.

| Year | Bhaktambar occurrences | Start on Saptami | All with kshaya |
|---|---|---|---|
| 2026 (adhik) | 25 | 5 | yes |
| 2027 (normal) | 24 | 8 | yes |

The 2026 cases: 25 Jan, 25 Mar, **9 May**, 7 Jul, 5 Aug.

**One other class shares the identical fallback**: `AshtahnikaVratFestival`
(festival_rules.py:813-814) pulls back to Saptami under `has_only_kshaya`,
producing one such start in 2027 (Phalguna Ashtahnika, 15 Mar). Everything else
that begins on a Saptami does so because Saptami is genuinely its anchor
(Pushpanjali Day 3/4, Navapad Oli), not through this mechanism.

So: two classes, one shared rule, ~13 occurrences per two years.

---

## 6. Directive 5 — the fix

### It is specified behaviour

`tests/test_bhaktambar_vrat.py:44`:

```python
def test_kshaya_rule_enforces_7_days_from_saptami(self):
    """If a Tithi in 8..14 is skipped (e.g. Navami 9 is skipped),
       start shifts back to Saptami to guarantee 7 days."""
```

Someone decided this deliberately and pinned it. Classify as
**`EXPECTED_BEHAVIOR`**; it is not a defect against its own specification.

### The question worth reopening

The rule preserves a **count of civil days**. The alternative is to preserve the
**set of tithis**, and the two disagree exactly when a tithi is kshaya.

> A kshaya Chaturdashi has not been lost from the vrat — it is absorbed into the
> Trayodashi day. The observance still covers all seven tithis, Ashtami through
> Chaturdashi; it simply occupies six civil days because one tithi began and
> ended inside another day.

Under that reading, extending backwards into Saptami adds a day that lies
**outside the vrat's own stated range** (`registry.py`: "from Ashtami (8) to
Chaturdashi (14)"), and the correct output for May 2026 is 10–15 May, six days.

Which is right is a question about the tradition, not about the code. Two
observations that may bear on it:

- Ashtami genuinely begins at 14:03 on 9 May, so a Saptami start is defensible
  if the vrat commences when Ashtami *starts* rather than when it prevails at
  the day-anchor. But that principle would move **every** occurrence, not just
  the kshaya ones — the code would need a real eve-of rule, not a length floor.
- The seven-day floor currently has no source. `registry.py` cites only
  "Jain Traditions" and states the 8→14 range, not a duration guarantee.

### If you rule (A) — keep it

No code change. I would add one thing: `has_kshaya` is already on the
occurrence, so the PDF and UI can render "प्रारंभ (क्षय — सप्तमी से)" or a
footnote on those five rows, so a reader checking against a printed panchang
sees why the start moved instead of assuming an error. That is presentation
only.

### If you rule (B) — anchor strictly to Ashtami

The change is small and contained. In `BhaktambarVratFestival.resolve()`,
delete the `natural_days < 7` branch (lines 606-620) so:

```
start_day = tithi_dates[8][0]  if present, else first available target date
end_day   = tithi_dates[14][-1] if present, else last available target date
total_days = (end_day - start_day).days + 1     # may legitimately be 6
has_kshaya = any tithi in 8..14 absent from this paksha
```

Then:

- update `test_kshaya_rule_enforces_7_days_from_saptami` — it asserts the
  behaviour being removed, so it must be rewritten, not deleted, to pin the
  six-day outcome;
- relax `test_annual_bhaktambar_vrats_resolution_2026:144`, which asserts
  `duration_days >= 7`;
- apply the same decision to `AshtahnikaVratFestival:813` or explicitly document
  why the two differ;
- expect exactly these 2026 dates to move: 25 Jan, 25 Mar, 9 May, 7 Jul, 5 Aug
  (each start +1 day, duration 7→6), and the eight 2027 cases in §5.

### Recommended next step

Check 9 May 2026 in the printed Pt. Jaini Jiyalal panchang. If it shows the vrat
beginning on the 10th, that settles it as (B) and the fix is an hour's work with
the blast radius already enumerated above.
