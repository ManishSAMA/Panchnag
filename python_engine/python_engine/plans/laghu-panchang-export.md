# Plan: Laghu Panchang yearly export (PDF + Excel, web + API + CLI)

Status: implemented 2026-10-12. Reference booklet: "laghu panchang 2027 12ver (2) naman.pdf" (kept out of git).

## Context

The user has a printed "laghu panchang 2027" booklet (12 landscape pages, legacy Kruti-font Hindi) and wants the app to generate the same booklet for **any year (Jan–Dec) and any location set in the app**, from the app's own calculations. Output must be **searchable/copyable Unicode Hindi PDF**, and the same data as **Excel**. Available from the web app, an API endpoint and the CLI.

Decisions already made with the user:
- 卐 = day has a *highly auspicious* shubh yoga; `-` otherwise.
- Festivals = the app's own calendar, using the profile selected in the app (default `shwetambar_murtipujak_tapagachchha`), not a Digambar list.
- Include everything the app can compute; skip what it can't (acharya/muni anniversaries, melas).
- Location comes from the app; header sunrise/sunset = the app's own values (1st and 16th of month).

## Target layout (decoded from the reference PDF)

One Gregorian month per page, landscape 8in × 5in, two half-month tables side by side (1–15 | 16–end).

Half header (4 lines):
1. `वीर निर्वाण सं. 2553   विक्रम संवत् 2083` (range like `2083–84` if it changes within the half)
2. `1 जनवरी से 15 जनवरी 2027 तक।`
3. `पौष कृष्ण नवमी से पौष शुक्ल सप्तमी तक` (udaya tithi + Purnimanta month of first/last day)
4. `सूर्योदय – 07:19 बजे, सूर्यास्त – 17:31 बजे` (1st / 16th)

11 columns:

| Header | Content |
|---|---|
| दि. | day number |
| शुभ दि. | `卐` / `-` |
| जैन तिथि | tithi at sunrise + 2h24m: 1–14, 15 (पूर्णिमा), 30 (अमावस); on Pratipada → `पौ.शु. 01` / `मा.कृ. 01` (Purnimanta month abbr) |
| उदय तिथि | tithi at sunrise, same format; kshaya → `3-4` |
| वा. | र सो मं बु बृ शु श |
| तिथि समाप्ति | end of udaya tithi, `HH:MM` from the civil day's midnight (so `25:47` = 01:47 next day); `अहोरात्र` if it outlasts next sunrise |
| नक्षत्र | abbr at sunrise (अ. भ. कृ. रो. मृ. आ. पुन. पु. आश्ले. म. पू.फा. उ.फा. ह. चि. स्वा. वि. अनु. ज्ये. मू. पू.षा. उ.षा. श्र. ध. श. पू.भा. उ.भा. रे.) |
| नक्षत्र समय | end time, same format |
| योग | abbr at sunrise (वि. प्री. आ. सौ. शो. अ. सु. धृ. शू. गं. वृ. ध्रु. व्या. ह. वज्र सि. व्य. वरी. परि. शि. सा. शु. शु. ब्र. ऐ. वै.) |
| चन्द्र राशि प्रवेश | rashi at sunrise (मेष…मीन); if Moon changes sign before next sunrise → `<new abbr>-HH:MM` (e.g. `वृ.-28:21`; abbrs मे. वृ. मि. क. सिं. कन्या तु. वृश्चि. ध. म. कुं. मी.) |
| पर्व, त्यौहार, पंचक आदि | festivals/kalyanaks (Hindi names) • `भ. 25:47 से 14:24 तक` (Bhadra) • `पंचक 28:34 से` / `पंचक … तक` |

## Design

### Reused (do not rewrite)
- `panchang.generate_daily_panchang` (Tithi/Nakshatra/Yoga index + `_End_JD`), `calculate_jain_tithi_from_sunrise`, `calculate_bhadra_kaal`, `calculate_panchak_kaal`, `get_purnimanta_month`, `kshaya_tithi_between`, `get_vikram_samvat`, `get_vira_nirvana_samvat`, `find_chaitra_shukla_1`, `find_diwali`, `_find_exact_end_time` pattern.
- `astronomy.get_sunrise`, `get_sunset`, `local_time_to_jd`, `get_planetary_longitude`.
- `yoga_service.detect_all_yogas_for_day` (entries carry `nature`, `severity`, `start_jd`, `end_jd`, `cancelled`, `is_nullified`).
- `jain_observances.festival_service.generate_jain_festivals(year, lat, lon, ayanamsa, profile)` + `hindi_calendar_pdf.build_festival_index`, `merge_day_festivals`, `translate_fest`.
- `hindi_calendar_pdf.MONTH_NAMES_HINDI`, `GREG_MONTHS_HINDI`, `TITHI_NAMES_HINDI`, `_paksha_and_name`; `hindi_export.RASHI_HI`.
- `hindi_calendar_pdf._html_to_pdf` (Playwright → Edge fallback → HTML-only).
- `panchang_service.resolve_location`; `GENERATED_EXPORTS` + `/downloads/<token>` in `app.py`.

### New code
1. **`panchang.find_moon_rashi_change(sunrise_jd, next_sunrise_jd, ayanamsa) -> tuple[int, int | None, float | None]`**: rashi at sunrise, the new rashi and its entry JD (bisection), or None. Then refactor the inline bisection in `calculate_bhadra_kaal` (:971–984) to use it.
2. **`laghu_panchang.py`** (data, pure apart from the ephemeris):
   - `@dataclass(frozen=True) LaghuDay` (the 11 display strings + `date`), `LaghuHalf` (4 header strings + `days: tuple[LaghuDay, ...]`).
   - Abbreviation tables above as module-level tuples, indexed like `panchang.NAKSHATRA_NAMES` / `YOGA_NAMES`.
   - Pure formatters: `clock_from_midnight(jd, midnight_jd) -> "HH:MM"`, `tithi_cell(index, month_abbr)`, `shubh_mark(yoga_result, sunrise_jd)` (any entry in `aanandadi_yogas`/`yogas`/`ravi_yogas`/`special_yogas` with `nature=="shubh"`, `severity=="highly_auspicious"`, not cancelled or nullified, `start_jd <= sunrise < end_jd`), `moon_sign_cell`, `bhadra_text`, `panchak_text`, `festival_text`.
   - `build_laghu_year(*, year, lat, lon, tz_name, ayanamsa, profile) -> tuple[LaghuHalf, ...]` (24 halves). **Per-day UTC offset from `zoneinfo`** (not `_timezone_snapshot`'s Jan-1 offset) so DST locations (e.g. Trenton, NJ) are correct. Computes Dec 31 + Jan 1 of the next year for kshaya and next-sunrise.
   - Performance: build serially first and time it. If a year takes over ~60 s, parallelise per month with `multiprocessing.Pool` like `main.run_generation`.
3. **`laghu_panchang_render.py`**:
   - `render_html(halves, *, title, location_name) -> str`: `@page { size: 8in 5in; margin: 0.15in }`, Nirmala UI / Mangal / Noto Sans Devanagari, two tables per page, page break per month, 卐 rendered as text.
   - `write_pdf(halves, path) -> str`: writes the .html, calls `_html_to_pdf` and returns the PDF path (or the .html path when no renderer exists). If `_html_to_pdf` hard-codes A4, add a keyword `prefer_css_page_size=True` path (backward compatible).
   - `write_excel(halves, path)`: openpyxl, 12 sheets (Hindi month names), each sheet mirrors the page: two blocks side by side, merged header rows, same 11 column headers, styling like `export.export_to_excel` (2C3E50 header, frozen panes).
4. **Service**: `pdf_generation_service.generate_laghu_panchang_export(*, year, city, lat, lon, ayanamsa_name, profile, output_format: "pdf"|"excel"|"both", output_dir=None) -> dict` returning `{year, ayanamsa, profile, location{...}, files: [{name, path, format}]}`; file names `Laghu_Panchang_<year>_<place>.pdf/.xlsx`.
5. **Request parsing**: `LaghuPanchangRequest` frozen dataclass + `parse_laghu_panchang_request(payload)` in `request_parsing.py` (year 1900–2100, format, profile; reuse `_parse_required_int`, `_parse_location_fields`; extract the duplicated profile set into one `VALID_PROFILES` constant while there).
6. **API**: `POST /generate-laghu-panchang` → `{..., files: [{name, format, download_url}]}`; 400 on `ValueError`, 500 otherwise (same as `/generate-hindi-pdf`).
7. **CLI**: `python main.py laghu --year 2027 (--city Delhi | --lat --lon) [--ayanamsa] [--profile] [--format pdf|excel|both] [--output DIR]`. `main()` dispatches to `laghu_cli(argv)` when `argv[1] == "laghu"`; the existing flat parser stays unchanged.
8. **Web UI**: a "लघु पंचांग (Laghu Panchang)" card in Settings next to the Hindi PDF card (`templates/index.html` ~:612): `#laghuYear`, `#laghuFormat` (PDF / Excel / दोनों), `#laghuBtn`, `#laghuResult`. `static/app.js` handler like :1404: reads `state.lat/lon/ayanamsa/jainProfile`, posts, renders download links.
9. **Docs**: `docs/api.md` (endpoint), `docs/setup_and_usage.md` (CLI + UI), `CLAUDE.md` (gotchas), and `plans/laghu-panchang-export.md` updated to match this plan.
10. `requirements-dev.txt`: add `pypdf` (searchability test only).

## TDD increments (each RED → GREEN → mutate → refactor, commit approval each)

1. `find_moon_rashi_change`: invariants (entry JD inside window; rashi before ≠ after; None when the sign holds all day); then refactor Bhadra onto it with the existing Bhadra tests green.
2. Pure formatters: `clock_from_midnight` (>24h after midnight, minutes < 60), `tithi_cell` (Pratipada abbr, 15/30), `shubh_mark` with hand-built yoga dicts (nullified/cancelled ignored), `moon_sign_cell`, Bhadra/Panchak text.
3. `build_laghu_year` invariants (one real year, Delhi): 24 halves; every date once in order; split 1–15/16–end; 卐/`-` only; weekday consistent with the date; time cells match `^\d{2}:\d{2}$|^अहोरात्र$`, hour < 48. Spot checks: a known kalyanak date's cell contains its Hindi registry name (cite registry), and a DST location's sunrise header shifts by an hour across the DST boundary.
4. Excel: 12 sheets, 11 headers ×2 per sheet, row count = days in month.
5. HTML/PDF: HTML contains all headers + 卐; `_html_to_pdf` patched (as in `tests/test_hindi_pdf_export.py`); real-renderer test (skipped if no Playwright/Edge) extracts text with pypdf and finds `सूर्योदय`, so the PDF is searchable.
6. Request parser (parametrised bad year/format/profile) → API endpoint (patched service, then GET download) → CLI (`main.main(["laghu", …])` writes files to tmp).
7. UI: `tests_ui/test_smoke.py` class like `TestHindiCalendarExport` (:228): routes `**/generate-laghu-panchang`, asserts the posted payload carries lat/lon/profile/format, link appears, no JS errors.

## Verification

- `pytest tests` and `pytest tests_ui` (run separately), both green.
- `python main.py laghu --year 2027 --city Delhi --format both`, then open the PDF and compare page 1 against the reference booklet (sunrise ≈ 07:19 on Jan 1, tithi 9/9 Friday, Chitra nakshatra, Tula rashi). Small minute differences are acceptable; any difference in tithi or nakshatra gets investigated.
- In the browser preview: set the location, generate both formats from the card, download, and select/copy Hindi text from the PDF.
- Run with Trenton, NJ too (DST check).
