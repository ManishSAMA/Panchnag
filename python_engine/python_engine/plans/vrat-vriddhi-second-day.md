# Vrats take the second day of a tithi vriddhi (वृद्धौ कार्या तथोत्तरा)

Status: implemented 2026-10-20.

## Why

Reviewing the Laghu booklet, the user flagged 18–19 Oct 2026 (New Delhi): Saptami
ends 08:27 (Drik Panchang; ours 08:29), so Ashtami holds the Jain day-start
(sunrise + 6 ghati) on both days. The app puts the Bhaktamar Vrat and Jeev Daya
Ashtami on the first day (18th). The user's rule, from the classical maxim
"क्षये पूर्वा तिथिः कार्या, वृद्धौ कार्या तथोत्तरा": **vrats go on the second day**.

## Decisions (user, 2026-10-20)

| Observance | Vriddhi day | Source of decision |
|---|---|---|
| Vrats: categories `vrat`, `monthly_vrat`, `tap_vrat`, `parva_vrat`, `mahaparv_vrat` | **second** | this change |
| Kalyanaks | first (unchanged) | book-verified earlier; KALYANAK_AUDIT_NOTES.md |
| Parva tithis (Ashtami / Chaudas `parva`) | both days (unchanged) | printed-panchang check, `ParvaTithiVriddhiShowsBothDaysTest` |
| Karma Nirjara Vrat | first (unchanged) | user directive 2026-08-30 |
| Ashtahnika span and its markers (Kartika Nandishwar Ashtami, Ashtahnika Purna) | follow the span (first Ashtami / second Purnima) | this change |
| Ravi Vrat, Ravivara Vrat (Sunday-bound) | unchanged | a weekday vrat cannot move to Monday |
| Gyan Panchami (+ Labh Panchami, same day) | first Panchami (unchanged) | its rule documents "Vriddhi -> 1st Panchami"; matches the user's 2027 reference PDF (decision 2026-10-21) |

## Design: the first day of a vriddhi belongs to the previous tithi

The maxim treats the first day of a vriddhi as the preceding tithi (the Ashtami
vriddhi is "a Saptami vriddhi" for observance). So instead of shifting dates
afterwards, vrat rules **see the first day relabelled as the previous tithi**,
and every rule recomputes naturally. Numbered series (Pushpanjali "दिन 1…5",
Namokar steps) renumber correctly, and spans start on the second day.

1. `festival_service`: build `vrat_snapshots`, a copy of the snapshots where,
   for each consecutive pair (d, d+1) with the same Jain-day tithi, day d takes
   the tithi identity (`tithi`, `jain_tithi`, `paksha`, `tithi_in_paksha`,
   `jain_*`, month fields) of day d-1. Pure function, tested on its own.
2. Rules whose category is a vrat category get `vrat_snapshots`; all other
   rules get the original snapshots. Excluded by id: Karma Nirjara, Ashtahnika
   markers, Ravi/Ravivara vrats.
3. Provider-based calculators (Dashlakshan, Ratnatraya, Shodashkaran) read the
   Jain-day tithi through the provider at sunrise + 144 min. Add
   `jain_day_tithi(date)` to `SwissEphTithiProvider`, with the same relabelling
   when constructed with `vriddhi="second_day"`, and switch those three
   calculators to it.

## Expected changes (New Delhi, from the vriddhi scan; verified after implementation)

- Bhaktamar Vrat: 10→11 Jan 2026, 26→27 Aug 2026, 18→19 Oct 2026, 28→29 May 2027, 15→16 Aug 2027
- Jeev Daya Ashtami: 18→19 Oct 2026
- Bhadrapada Dashlakshan 2026: starts 16 Sep (the day after Samvatsari), not 15 Sep
- Pushpanjali (monsoon 2026): days 1–5 on 16–20 Sep
- Labdhi Vidhan Purna 2026, Pratham Jeth Jinvani 2027, Namokar step (8→9 Oct 2027): one day later
- Unchanged: every kalyanak, Pakhi Chaudas and Ashtami parva on both days, Karma Nirjara, Ashtahnika, Ravi Vrat

## Actual changes (before/after diff, Delhi, all three profiles, 2026-2027)

Exactly these moved; nothing outside vrat categories changed.

- Bhaktamar Vrat: 10→11 Jan 2026, 26→27 Aug 2026, 18→19 Oct 2026, 28→29 May 2027, 15→16 Aug 2027
- Jeev Daya Ashtami: 18→19 Oct 2026
- Bhadrapada Dashlakshan 2026: starts 16 Sep (was 15 Sep, the Samvatsari day)
- Pushpanjali (monsoon 2026): days 1–5 on 16–20 Sep (was 6 days, 15–20 Sep)
- Namokar Mahamantra Vrat step: 8→9 Oct 2027
- Pratham Jeth Jinvani Vrat 2027: start 19→20 Jun, conclusion 18→19 Jun
- Chaitra Navpad Oli Purna and Ratnatraya/Sankatharan Purna 2026: 1→2 Apr (not in the
  first estimate; 2 Apr is Purnima at sunrise and the second Purnima under the maxim;
  user confirmed 2026-10-20)

Implementation: `jain_observances/vriddhi.py` (who follows the rule),
`festival_service.vrat_view_of_snapshots` (snapshot-based vrat rules),
`vrats/provider.jain_day_tithi` (Dashlakshan, Ratnatraya, Shodashkaran).

## TDD

1. Pure relabelling: a vriddhi pair's first day reads as the previous tithi; non-vriddhi days untouched; kshaya untouched; a Pratipada vriddhi relabels to the previous paksha's last tithi.
2. Festival engine, real data (Delhi 2026–27): each "expected change" above, and each "unchanged" item, as tests citing this decision.
3. Existing tests that encode first-day for vrats (`test_tithi_vriddhi_first_day` for vrats, Bhaktamar tests) updated with the decision recorded; kalyanak, parva-both-days and Karma Nirjara tests stay as they are.
4. A before/after diff of every 2026–2027 festival date (Delhi, all three profiles) to confirm that nothing outside the expected list moved.
5. Laghu booklet regenerated; docs and KALYANAK_AUDIT_NOTES.md updated.
