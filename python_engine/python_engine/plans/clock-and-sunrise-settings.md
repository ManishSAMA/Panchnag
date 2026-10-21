# Clock and sunrise-rule settings

Status: implemented 2026-10-16.

## Why

The user compared the app against a New Jersey reference panchang
(`PanchangReport_2654.pdf`, 40°50'N 74°06'W, 2027, kept out of git) and found
that "it fails from March on". Measured:

- **Clock.** The reference prints Eastern *Standard* Time all year. The daily
  view, DB pre-compute and Laghu booklet follow the wall clock and switch to EDT
  on 14 Mar 2027, so every time from then to 7 Nov is +1 h. Before 14 Mar we
  match within ~3 min (tithi end 29:11 vs 29:14 on 8 Mar).
  The range CSV/Excel/JSON, English PDF and Hindi PDF use a single offset sampled
  on 1 January (`_timezone_snapshot`), which is standard time only by accident:
  south of the equator 1 January is summer time, so they would use DST all year.
- **Sunrise.** Ours is the modern rule (upper limb, refraction). Both references
  (NJ sheet and the Delhi laghu booklet) match the traditional rule: disc
  centre, no refraction (Swiss Ephemeris `BIT_DISC_CENTER | BIT_NO_REFRACTION`,
  identical to `BIT_HINDU_RISING` here). NJ 31 Mar: ref 05:46, ours 05:42,
  traditional 05:46. Delhi 1 Jan: booklet 07:19/17:31, traditional 07:18/17:31.

User decisions (2026-10-16): both become **settings**.

| Setting | Values | Default |
|---|---|---|
| `clock` | `standard` (zone's standard time all year) · `daylight` (wall clock, DST) | `standard` |
| `sunrise` | `modern` (upper limb + refraction) · `traditional` (disc centre, no refraction) | `modern` |

Note: the `standard` default changes today's daily view for DST places (it
currently follows the wall clock). India and other no-DST zones see no change.

## Design

### Core (pure, in `astronomy.py`)
- `ClockMode = Literal["standard", "daylight"]`, `SunriseRule = Literal["modern", "traditional"]`.
- `utc_offset_hours(tz_name, local_date, *, clock) -> float`: the offset in force
  at local noon (`daylight`), or `utcoffset() - dst()` (`standard`). Replaces the
  ad-hoc offset code in `_timezone_snapshot`, `db_generator._tz_offset_hours`,
  `panchang_service` (:386), `laghu_panchang._utc_offset_hours`.
- `get_sunrise(jd, lat, lon, rule="modern")` / `get_sunset(...)`: the rule maps to
  rise_trans flags. The `lru_cache` key includes the rule, because the argument
  is explicit.
- Time formatting that today converts via `ZoneInfo` (`jd_to_zoned_datetime`,
  :345) takes `clock` too, so the label reads EST rather than EDT under `standard`.

### Threading
`sunrise_rule` is passed explicitly, along the same path as `ayanamsa` (which is
already threaded through the festival service and vrat providers). It is not
module state, because `generate_jain_festivals` is `lru_cache`d and must key on it.
`clock` is needed only where a UTC offset or local-time label is computed.

Representative touch points (the full list comes from `grep get_sunrise|get_sunset|utcoffset`):
`panchang.py` (Jain tithi from sunrise, `find_chaitra_shukla_1`, `find_diwali`),
`jain_observances/festival_service.py` + `vrats/*.py`, `main.py` (`_compute_day`
and the worker config), `export_pdf.py`, `hindi_calendar_pdf.py`,
`laghu_panchang.py`, `panchang_service.py`, `range_generation_service.py`,
`pdf_generation_service.py`, `db_generator.py`, `app.py` (7 direct sunrise calls:
choghadiya, month overview, muhurta).

### Boundaries
- `request_parsing.py`: `parse_clock`, `parse_sunrise_rule` (shared, like
  `parse_calendar_system`); every request dataclass gains `clock` and
  `sunrise_rule`. Invalid values give 400.
- `app.py`: every endpoint passes them on. `/api/generate-db` takes
  `sunrise_rule` and records it in the DB `meta`. DB times are UTC, so the clock
  setting does not apply there.
- CLI: `--clock {standard,daylight}` and `--sunrise {modern,traditional}` on
  `main.py`, `main.py laghu` and `hindi_calendar_pdf.py`. The range CLI's
  `--tz_offset` is still honoured when given explicitly.
- Web UI: Settings gains two selects beside Ayanamsa: "Clock: Standard time /
  Daylight saving time" and "Sunrise: Modern (upper limb) / Traditional (disc
  centre)", stored in `jain_panchang_v2` and sent with every request exactly like
  `ayanamsa`.
- Output labels: the export tz label (`EST`), and the booklet/PDF headers note
  the convention when it is not the default (e.g. "पारम्परिक सूर्योदय").

## TDD increments

1. `utc_offset_hours`: NJ in July gives -5 (standard) and -4 (daylight); January
   gives -5 for both; Sydney in January gives +10 (standard) and +11 (daylight);
   Delhi gives +5.5 for both.
2. `get_sunrise`/`get_sunset` rule: traditional rise is later and set earlier
   than modern, everywhere and every month (an invariant). Cached and uncached
   values agree per rule (the cache never mixes rules). Golden spec cited from
   the references: NJ 31 Mar 2027 traditional rise 05:46 EST, Delhi 1 Jan 2027
   07:18/17:31.
3. The Laghu booklet honours both settings; the March DST test flips to "the
   header sunrise moves smoothly across 14 Mar under `standard`".
4. Range export, English PDF, Hindi PDF: times follow `clock`; a southern-
   hemisphere location under `standard` uses its winter offset in January (the
   `_timezone_snapshot` bug).
5. Daily panchang, month overview, choghadiya, muhurta: both settings honoured;
   default `standard` (the behaviour change, asserted explicitly).
6. Festival service: `sunrise_rule` reaches the vrats and the cache key. Under
   `modern`, festival dates are unchanged (the existing snapshot tests stay green).
   Under `traditional`, a report lists any 2026–2027 festival dates that move,
   for the user to review.
7. Request parsing, API, CLI flags, DB meta, UI selects (tests_ui).
8. Docs: `docs/api.md`, `docs/setup_and_usage.md`, CLAUDE.md gotchas.

## Verification

- `pytest tests`, `pytest tests_ui`.
- Regenerate New Jersey 2027 (`clock=standard`, `sunrise=traditional`) and
  compare against `PanchangReport_2654.pdf` for every month: sunrise within 1 min,
  tithi/nakshatra/yoga end and Moon-sign entry within ~3 min, no 1-hour jump
  after 14 March.
- Regenerate the Delhi booklets and compare the headers with the laghu
  reference (07:19 / 17:31).
- Re-measure every page with the overflow check (the fit script).

## Open items

- The ~3 min residual in tithi and nakshatra end times (ours earlier) is not
  explained by either setting; investigate separately if it matters (ΔT or the
  ephemeris model).
- The NJ sheet's sunset column fits neither rule (16:43 vs 16:39 modern / 16:34
  traditional on 1 Jan), so its sunrise column is the guide.
