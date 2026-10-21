"""
hindi_calendar_pdf.py -- Hindi Jain/Vedic Panchang calendar PDF.

Replaces the three near-identical generate_hindi_calendar_pdf*.py scripts, which
differed only in their year range and a hardcoded Gregorian-month-name table.
Everything here is parameterised by (start_year, start_month, month_count), and
the month names are computed, so a new edition needs no new file.

Table schema (strict order):

    दिनांक | वार | हिन्दू मास | हिन्दू तिथि | जैन तिथि | सूर्योदय | सूर्यास्त | पर्व एवं त्यौहार

The two tithi columns are the point of the layout. The Hindu Tithi is the one
prevailing at plain sunrise; the Jain Tithi is the one prevailing 2h24m
(6 ghati) later, which is the Jain day-start and the anchor every festival in
this calendar is mapped on. The previous single "पक्ष एवं तिथि" column was
already the Jain one -- it was just never labelled as such, so the two could not
be compared.

The month column follows the Purnimanta convention by default (month ends at
Purnima), matching printed North Indian panchangs. Pass calendar_system="amanta"
for Gujarati / South Indian reckoning. See plans/amanta-purnimanta-offset.md.
"""

from __future__ import annotations

import calendar
import os
import subprocess
import tempfile
import time
from datetime import date, datetime, timedelta

from astronomy import (
    get_planetary_longitude,
    get_sunrise,
    get_sunset,
    jd_to_local_time_string,
    utc_offset_hours,
    local_time_to_jd,
)
from jain_observances.festival_service import generate_jain_festivals
from panchang import (
    JAIN_TITHI_OFFSET_DAYS,
    find_chaitra_shukla_1,
    find_diwali,
    get_hindu_month,
    get_purnimanta_month,
    kshaya_tithi_between,
    get_tithi,
    get_vara_from_date,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
)

# ---------------------------------------------------------------------------
# Hindi vocabulary
# ---------------------------------------------------------------------------

WEEKDAYS_HINDI = [
    "रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार",
]

GREG_MONTHS_HINDI = [
    "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून",
    "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर",
]

TITHI_NAMES_HINDI = {
    1: "प्रथमा (एकम)",   2: "द्वितीया (दूज)",  3: "तृतीया (तीज)",
    4: "चतुर्थी (चौथ)",   5: "पंचमी",           6: "षष्ठी (छठ)",
    7: "सप्तमी",          8: "अष्टमी",           9: "नवमी",
    10: "दशमी",           11: "एकादशी (ग्यारस)", 12: "द्वादशी (बारस)",
    13: "त्रयोदशी (तेरस)", 14: "चतुर्दशी (चौदस)",
}

MONTH_NAMES_HINDI = {
    "CHAITRA": "चैत्र",
    "VAISHAKHA": "वैशाख",
    "JYESHTHA": "ज्येष्ठ",
    "ASHADHA": "आषाढ़",
    "SHRAVANA": "श्रावण",
    "BHADRAPADA": "भाद्रपद",
    "ASHWIN": "आश्विन",
    "KARTIKA": "कार्तिक",
    "AGRAHAYANA": "मार्गशीर्ष",
    "PAUSHA": "पौष",
    "MAGHA": "माघ",
    "PHALGUNA": "फाल्गुन",
}

TRANSLATIONS_MAP = {
    "Shri": "श्री",
    "Bhagwan": "भगवान",
    "Conception Kalyanak": "गर्भ कल्याणक",
    "Birth Kalyanak": "जन्म कल्याणक",
    "Austerity Kalyanak": "दीक्षा कल्याणक",
    "Omniscience Kalyanak": "केवलज्ञान कल्याणक",
    "Liberation Kalyanak": "मोक्ष कल्याणक",
    "Rishabhdev (Adinath)": "ऋषभदेव (आदिनाथ)",
    "Ajitnath": "अजितनाथ",
    "Sambhavnath": "संभवनाथ",
    "Abhinandan": "अभिनंदन नाथ",
    "Sumatinath": "सुमतिनाथ",
    "Padmaprabha": "पद्मप्रभ",
    "Suparshvanath": "सुपार्श्वनाथ",
    "Chandraprabha": "चंद्रप्रभ",
    "Pushpadanta (Suvidhinath)": "पुष्पदंत (सुविधिनाथ)",
    "Sheetalnath": "शीतलनाथ",
    "Shreyansnath": "श्रेयांसनाथ",
    "Vasupujya": "वासुपूज्य",
    "Vimalnath": "विमलनाथ",
    "Anantnath": "अनंतनाथ",
    "Dharmanath": "धर्मनाथ",
    "Shantinath": "शांतिनाथ",
    "Kunthunath": "कुंथुनाथ",
    "Aranatha": "अरनाथ",
    "Arahnath": "अरनाथ",
    "Mallinath": "मल्लिनाथ",
    "Munisuvrat": "मुनिसुव्रत",
    "Naminath": "नमिनाथ",
    "Neminath": "नेमिनाथ",
    "Parshvanath": "पार्श्वनाथ",
    "Mahavira": "महावीर",
    "Mahavir": "महावीर",
}

# ---------------------------------------------------------------------------
# Schools of thought
# ---------------------------------------------------------------------------

# Numbered per the user's convention; these are the exact strings the registry's
# `sources` field carries. 105 of 209 registry entries name all three, 30 name a
# subset, and 74 cite no school at all (e.g. "Jain Traditions") -- those are
# ordinary observances rather than Kalyanaks and carry no tag.
SCHOOLS: tuple[str, str, str] = ("Vrindavan", "Uttarapurana", "Ashadhara")


def school_numbers(sources) -> list[int]:
    """Ascending 1-based indices of the schools named in `sources`."""
    if not sources:
        return []
    lowered = [str(s).lower() for s in sources]
    return [
        index
        for index, school in enumerate(SCHOOLS, start=1)
        if any(school.lower() in source for source in lowered)
    ]


SCHOOL_CHOICES: tuple[str, ...] = ("all",) + tuple(school.lower() for school in SCHOOLS)
SCHOOL_NAMES_HI = {"vrindavan": "वृन्दावन", "uttarapurana": "उत्तरपुराण", "ashadhara": "आशाधर"}


def festivals_for_school(festivals: list[dict], school: str) -> list[dict]:
    """Festivals as one school reckons them.

    A kalyanak attested only by other schools is dropped; one the chosen school
    attests, or that no school claims (parvas, vrats), is kept. "all" keeps all.
    """
    if school not in SCHOOL_CHOICES:
        raise ValueError(f"school must be one of: {', '.join(SCHOOL_CHOICES)} (got {school!r}).")
    if school == "all":
        return list(festivals)
    chosen = SCHOOL_CHOICES.index(school)  # 1-based, as school_numbers

    def attested(festival: dict) -> bool:
        numbers = school_numbers(festival.get("sources"))
        return not numbers or chosen in numbers

    return [festival for festival in festivals if attested(festival)]


def school_tag(sources) -> str:
    """Bracketed consensus tag, e.g. "(1, 2, 3)". Empty when no school applies."""
    numbers = school_numbers(sources)
    return f"({', '.join(str(n) for n in numbers)})" if numbers else ""


def merge_day_festivals(festivals: list[dict]) -> list[dict]:
    """Collapse same-named festivals on one day, unioning their school tags.

    Where schools disagree about a Kalyanak's tithi the registry holds separate
    entries. They usually resolve to different dates, but not always -- 2026-03-18
    carries Anantnath Liberation twice, as (1, 3) and as (2,). The reader should
    see one line tagged (1, 2, 3), not two adjacent lines.
    """
    merged: dict[str, dict] = {}
    for festival in festivals:
        name = festival.get("name", "")
        entry = merged.get(name)
        if entry is None:
            entry = dict(festival)
            entry["_schools"] = set(school_numbers(festival.get("sources")))
            merged[name] = entry
            continue
        entry["_schools"].update(school_numbers(festival.get("sources")))
        if not entry.get("_tag") and festival.get("_tag"):
            entry["_tag"] = festival["_tag"]

    for entry in merged.values():
        numbers = sorted(entry.pop("_schools"))
        entry["sources_tag"] = f"({', '.join(str(n) for n in numbers)})" if numbers else ""

    return list(merged.values())


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def hindi_greg_month(year: int, month: int) -> str:
    """"मार्च 2026" for any year, replacing the per-edition hardcoded tables."""
    return f"{GREG_MONTHS_HINDI[month - 1]} {year}"


def format_time_12h(jd: float, tz_offset: float = 5.5) -> str:
    if jd <= 0.0:
        return "--"
    time_string = jd_to_local_time_string(jd, tz_offset)
    if not time_string or ":" not in time_string:
        return "--"
    try:
        hour, minute = int(time_string.split(":")[0]), int(time_string.split(":")[1])
    except (ValueError, IndexError):
        return time_string[:5]
    suffix = "प्रातः" if hour < 12 else "सायं"
    return f"{hour % 12 or 12:02d}:{minute:02d} {suffix}"


def _paksha_and_name(tithi_index: int) -> tuple[str, str]:
    """("शुक्ल", "सप्तमी") for a 1-30 Tithi index."""
    if tithi_index <= 15:
        paksha, number = "शुक्ल", tithi_index
    else:
        paksha, number = "कृष्ण", tithi_index - 15

    if number == 15:
        return paksha, ("पूर्णिमा" if paksha == "शुक्ल" else "अमावस्या")
    return paksha, TITHI_NAMES_HINDI.get(number, str(number))


def format_tithi(tithi_index: int) -> str:
    """"शुक्ल सप्तमी" / "कृष्ण अमावस्या" from a 1-30 Tithi index."""
    paksha, name = _paksha_and_name(tithi_index)
    return f"{paksha} {name}"


def format_tithi_pair(tithi_index: int, kshaya_index: int | None) -> str:
    """Render a day's Tithi, appending the kshaya Tithi it absorbed.

    "शुक्ल त्रयोदशी/चतुर्दशी" -- the paksha is stated once when both share it,
    and repeated ("कृष्ण अमावस्या/शुक्ल प्रथमा") when the lost Tithi falls in
    the next paksha.
    """
    paksha, name = _paksha_and_name(tithi_index)
    if kshaya_index is None:
        return f"{paksha} {name}"

    lost_paksha, lost_name = _paksha_and_name(kshaya_index)
    tail = lost_name if lost_paksha == paksha else f"{lost_paksha} {lost_name}"
    return f"{paksha} {name}/{tail}"


def hindi_month_name(month_name: str, is_adhika: bool) -> str:
    base = month_name.removeprefix("Adhika ").strip()
    hindi = MONTH_NAMES_HINDI.get(base.upper(), base)
    return f"अधिक {hindi}" if is_adhika else hindi


def translate_fest(festival: dict) -> str:
    name_hindi = festival.get("name_hindi")
    if name_hindi and any("\u0900" <= ch <= "\u097f" for ch in name_hindi):
        return name_hindi

    text = festival.get("title") or festival.get("name") or ""
    for english, hindi in TRANSLATIONS_MAP.items():
        text = text.replace(english, hindi)
    return text.replace(" Ji - ", " भगवान ").replace(" Ji", "")


def festival_cell(festivals: list[dict]) -> str:
    """Render one day's festivals, merged and school-tagged, for the PDF cell."""
    parts = []
    for festival in merge_day_festivals(festivals):
        label = translate_fest(festival)
        if festival.get("_tag"):
            label = f"{label} ({festival['_tag']})"
        if festival.get("sources_tag"):
            label = f"{label} {festival['sources_tag']}"
        if label and label not in parts:
            parts.append(label)
    return " • ".join(parts)


# ---------------------------------------------------------------------------
# Row construction
# ---------------------------------------------------------------------------

def build_month_rows(
    year: int,
    month: int,
    *,
    lat: float,
    lon: float,
    tz_offset: float,
    ayanamsa: str,
    date_to_fests: dict[str, list[dict]],
    calendar_system: str = "purnimanta",
    tz_name: str | None = None,
    clock: str = "standard",
    sunrise_rule: str = "modern",
) -> list[dict]:
    """One dict per civil day, carrying exactly the eight table columns.

    With tz_name, each day takes its own offset under the clock setting;
    without, the fixed tz_offset applies.
    """
    resolve_month = get_purnimanta_month if calendar_system == "purnimanta" else get_hindu_month
    day_count = calendar.monthrange(year, month)[1]

    def offset_on(current: date) -> float:
        return utc_offset_hours(tz_name, current, clock=clock) if tz_name else tz_offset

    def day_facts(current: date) -> dict:
        day_start_jd = local_time_to_jd(current.year, current.month, current.day, 0.0, offset_on(current))
        sunrise_jd = get_sunrise(day_start_jd, lat, lon, sunrise_rule)
        reference_jd = sunrise_jd + JAIN_TITHI_OFFSET_DAYS
        return {
            "sunrise_jd": sunrise_jd,
            "sunset_jd": get_sunset(day_start_jd, lat, lon, sunrise_rule),
            "reference_jd": reference_jd,
            # Hindu Tithi: plain sunrise. Jain Tithi: the 6-ghati Jain day-start,
            # which is also what the month and every festival are keyed on.
            "hindu_tithi": get_tithi(
                get_planetary_longitude(sunrise_jd, "Sun", ayanamsa),
                get_planetary_longitude(sunrise_jd, "Moon", ayanamsa),
            ),
            "jain_tithi": get_tithi(
                get_planetary_longitude(reference_jd, "Sun", ayanamsa),
                get_planetary_longitude(reference_jd, "Moon", ayanamsa),
            ),
        }

    # One day past the month, so a kshaya on the last day is still detected.
    days = [date(year, month, d) for d in range(1, day_count + 1)]
    facts = {d: day_facts(d) for d in days + [days[-1] + timedelta(days=1)]}

    rows: list[dict] = []
    for current in days:
        fact = facts[current]
        following = facts[current + timedelta(days=1)]
        kshaya = kshaya_tithi_between(fact["jain_tithi"], following["jain_tithi"])

        month_name, _common, is_adhika = resolve_month(fact["reference_jd"], ayanamsa)
        vara_index = get_vara_from_date(current)

        rows.append({
            "date_str": f"{current.day:02d}-{month:02d}-{year}",
            "day_num": current.day,
            "vara": WEEKDAYS_HINDI[vara_index],
            "is_sunday": vara_index == 0,
            "h_month": hindi_month_name(month_name, is_adhika),
            "hindu_tithi": format_tithi(fact["hindu_tithi"]),
            "jain_tithi": format_tithi_pair(fact["jain_tithi"], kshaya),
            "kshaya_tithi": kshaya,
            "sunrise": format_time_12h(fact["sunrise_jd"], offset_on(current)),
            "sunset": format_time_12h(fact["sunset_jd"], offset_on(current)),
            "festivals": festival_cell(date_to_fests.get(current.isoformat(), [])),
        })

    return rows


def build_festival_index(results: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    """Split festival results into a per-date index and a multi-day registry.

    Multi-day observances are marked only on their first and last day in the
    daily grid; they get their own table up front.
    """
    date_to_fests: dict[str, list[dict]] = {}
    multi_day: list[dict] = []
    seen: set[tuple] = set()

    for result in results:
        for span in result.get("multi_day_festivals", []):
            key = (span["name"], span["start_date"], span["end_date"])
            if key not in seen:
                seen.add(key)
                multi_day.append(span)

        for festival in result.get("festivals", []):
            try:
                start = datetime.strptime(festival["start_date"], "%Y-%m-%d").date()
                end = datetime.strptime(festival["end_date"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue

            if start == end:
                date_to_fests.setdefault(start.isoformat(), []).append(festival)
            else:
                # A festival may name its own boundary words -- Ashtahnika ends in
                # Parana (breaking the fast), not a generic "completion".
                opening = dict(festival, _tag=festival.get("start_label", "प्रारंभ"))
                closing = dict(festival, _tag=festival.get("end_label", "समाप्ति"))
                date_to_fests.setdefault(start.isoformat(), []).append(opening)
                date_to_fests.setdefault(end.isoformat(), []).append(closing)

    multi_day.sort(key=lambda span: (span["start_date"], span["end_date"]))
    return date_to_fests, multi_day


def month_sequence(start_year: int, start_month: int, count: int) -> list[tuple[int, int]]:
    months = []
    year, month = start_year, start_month
    for _ in range(count):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


# ---------------------------------------------------------------------------
# HTML / PDF rendering
# ---------------------------------------------------------------------------

_STYLE = """
@page { size: A4 landscape; margin: 10mm 8mm 10mm 8mm; }
body { font-family: 'Segoe UI', 'Nirmala UI', 'Mangal', sans-serif; background: #fff;
       color: #1a1a1a; margin: 0; padding: 0; font-size: 10pt; }
.month-header { background: linear-gradient(135deg, #4A154B, #6B1110); color: #fff;
       padding: 10px 15px; border-radius: 6px; margin-bottom: 10px; display: flex;
       justify-content: space-between; align-items: center; }
.month-title { font-size: 16pt; font-weight: bold; }
.samvat-info { font-size: 11pt; color: #FFD700; font-weight: bold; }
.panchang-table { width: 100%; border-collapse: collapse; margin-bottom: 20px;
       font-size: 9.5pt; table-layout: fixed; }
.panchang-table th { background-color: #2C3E50; color: #fff; border: 1px solid #34495E;
       padding: 6px 4px; font-size: 9pt; text-align: center; word-wrap: break-word; }
.panchang-table td { border: 1px solid #BDC3C7; padding: 5px 4px; text-align: center;
       vertical-align: middle; word-wrap: break-word; font-size: 9pt; }
.panchang-table tr:nth-child(even) { background-color: #F8F9F9; }
.panchang-table tr.sunday-row { background-color: #FDEDEC; }
.panchang-table tr.parva-row { background-color: #FEF9E7; }
.date-cell { font-weight: bold; color: #2C3E50; }
.tithi-cell { color: #8E44AD; font-weight: 600; }
.jain-tithi-cell { color: #145A32; font-weight: 700; }
.fest-cell { text-align: left !important; color: #C0392B; font-weight: 600;
       font-size: 8.5pt; line-height: 1.25; }
.page-break { page-break-after: always; }
.header-main { text-align: center; margin-bottom: 15px; border-bottom: 2px solid #8E44AD;
       padding-bottom: 8px; }
.header-main h1 { color: #4A154B; font-size: 20pt; margin: 0 0 5px 0; }
.header-main p { color: #555; margin: 0; font-size: 10pt; }
.legend { margin: 0 0 12px 0; font-size: 9pt; color: #444; text-align: center; }
"""

# (header, width%, row key, css class)
_COLUMNS = [
    ("दिनांक",           8,  "date_str",    "date-cell"),
    ("वार",              9,  "vara",        ""),
    ("हिन्दू मास",        11, "h_month",     ""),
    ("हिन्दू तिथि",       15, "hindu_tithi", "tithi-cell"),
    ("जैन तिथि",          15, "jain_tithi",  "jain-tithi-cell"),
    ("सूर्योदय",          10, "sunrise",     ""),
    ("सूर्यास्त",         10, "sunset",      ""),
    ("पर्व एवं त्यौहार",  22, "festivals",   "fest-cell"),
]


def render_calendar_html(
    months: list[tuple[int, int]],
    rows_by_month: dict[tuple[int, int], list[dict]],
    multi_day: list[dict],
    samvat_by_year: dict[int, tuple],
    *,
    title: str,
) -> str:
    parts = [
        "<!DOCTYPE html>", "<html>", "<head>", "<meta charset='utf-8'>",
        f"<title>{title}</title>", "<style>", _STYLE, "</style>", "</head>", "<body>",
        "<div class='header-main'>",
        f"<h1>{title}</h1>",
        "<p>सूर्योदय, सूर्यास्त, हिन्दू एवं जैन तिथि, वार तथा समस्त जैन पर्व एवं त्यौहार</p>",
        "</div>",
        "<div class='legend'>पर्व के आगे कोष्ठक में मतसंख्या: "
        "1 = वृंदावन, 2 = उत्तरपुराण, 3 = आशाधर</div>",
    ]

    window_start = f"{months[0][0]:04d}-{months[0][1]:02d}-01"
    window_end = f"{months[-1][0]:04d}-{months[-1][1]:02d}-31"
    in_window = [m for m in multi_day if window_start <= m["start_date"] <= window_end]
    if in_window:
        parts.append("<div class='month-header'><div class='month-title'>बहु-दिवसीय पर्व एवं व्रत</div></div>")
        parts.append("<table class='panchang-table'>")
        parts.append("<tr><th style='width:55%'>पर्व / व्रत</th>"
                     "<th style='width:22%'>प्रारंभ तिथि</th>"
                     "<th style='width:23%'>समाप्ति तिथि</th></tr>")
        for span in in_window:
            name = translate_fest({"name": span["name"], "title": span["name"],
                                   "name_hindi": span.get("name_hindi", "")})
            name = (name.replace("(MAGHA_PHALGUNA)", "(माघ-फाल्गुन)")
                        .replace("(CHAITRA_VAISHAKHA)", "(चैत्र-वैशाख)")
                        .replace("(BHADRAPADA_ASHVINA)", "(भाद्रपद-आश्विन)"))
            tag = school_tag(span.get("sources"))
            if tag:
                name = f"{name} {tag}"
            start = datetime.strptime(span["start_date"], "%Y-%m-%d").strftime("%d-%m-%Y")
            end = datetime.strptime(span["end_date"], "%Y-%m-%d").strftime("%d-%m-%Y")
            parts.append(f"<tr><td class='fest-cell'>{name}</td><td>{start}</td><td>{end}</td></tr>")
        parts.append("</table>")
        parts.append("<div class='page-break'></div>")

    for index, (year, month) in enumerate(months):
        rows = rows_by_month[(year, month)]
        months_seen = list(dict.fromkeys(r["h_month"] for r in rows if r["h_month"]))
        vikram, vira = samvat_by_year[year]

        parts.append("<div class='month-header'>")
        parts.append(f"<div class='month-title'>{hindi_greg_month(year, month)} "
                     f"({' / '.join(months_seen)})</div>")
        parts.append(f"<div class='samvat-info'>विक्रम संवत: {vikram} | "
                     f"वीर निर्वाण संवत: {vira}</div>")
        parts.append("</div>")

        parts.append("<table class='panchang-table'>")
        parts.append("<thead><tr>")
        for header, width, _key, _cls in _COLUMNS:
            parts.append(f"<th style='width:{width}%;'>{header}</th>")
        parts.append("</tr></thead><tbody>")

        for row in rows:
            row_class = "sunday-row" if row["is_sunday"] else ("parva-row" if row["festivals"] else "")
            parts.append(f"<tr class='{row_class}'>")
            for _header, _width, key, css in _COLUMNS:
                parts.append(f"<td class='{css}'>{row[key]}</td>" if css else f"<td>{row[key]}</td>")
            parts.append("</tr>")

        parts.append("</tbody></table>")
        if index < len(months) - 1:
            parts.append("<div class='page-break'></div>")

    parts.append("</body></html>")
    return "\n".join(parts)


def _html_to_pdf(html_path: str, pdf_path: str, *, css_page_size: bool = False) -> bool:
    """Render the HTML to PDF. Returns whether the PDF was produced.

    Playwright first: it is already a dev dependency (tests_ui drives it), it
    honours the @page rules, and it works the same on every platform. Headless
    Edge stays as a fallback for a runtime that has Edge but no Playwright.

    css_page_size lets the document's own @page size and margins win over the
    A4-landscape default (the Laghu Panchang prints on 8in x 5in).
    """
    file_uri = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    target = os.path.abspath(pdf_path)

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(file_uri, wait_until="load")
                if css_page_size:
                    page.pdf(path=target, print_background=True, prefer_css_page_size=True)
                else:
                    page.pdf(path=target, format="A4", landscape=True, print_background=True,
                             margin={"top": "10mm", "bottom": "10mm",
                                     "left": "8mm", "right": "8mm"})
            finally:
                browser.close()
        if os.path.exists(target):
            return True
    except Exception as exc:  # renderer missing or browser not installed
        print(f"Playwright render unavailable ({exc.__class__.__name__}); trying Edge.")

    for edge in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        # A throwaway profile keeps Edge from handing the job to an Edge window
        # the user already has open, which exits at once without printing.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile_dir:
            try:
                subprocess.run(
                    [edge, "--headless=new", "--disable-gpu", "--no-first-run",
                     f"--user-data-dir={profile_dir}", "--no-pdf-header-footer",
                     f"--print-to-pdf={target}", file_uri],
                    capture_output=True, text=True, timeout=600,
                )
            except (OSError, subprocess.SubprocessError):
                continue
            # msedge.exe returns immediately; a child process prints afterwards,
            # so wait for it while its profile directory still exists.
            if _wait_for_finished_file(target):
                return True

    return False


def _wait_for_finished_file(path: str, timeout_s: float = 120.0) -> bool:
    """Whether ``path`` appears and stops growing within ``timeout_s``."""
    deadline = time.monotonic() + timeout_s
    last_size = -1
    while time.monotonic() < deadline:
        size = os.path.getsize(path) if os.path.exists(path) else -1
        if size > 0 and size == last_size:
            return True
        last_size = size
        time.sleep(0.5)
    return False


def generate_hindi_pdf_calendar(
    out_pdf_path: str,
    *,
    start_year: int = 2026,
    start_month: int = 3,
    month_count: int = 13,
    lat: float = 26.9124,
    lon: float = 75.7873,
    tz_offset: float = 5.5,
    ayanamsa: str = "Lahiri",
    profile: str = "all",
    calendar_system: str = "purnimanta",
    tz_name: str | None = None,
    clock: str = "standard",
    sunrise_rule: str = "modern",
) -> str:
    """Write the Hindi Panchang calendar.

    Returns the path actually written: the PDF, or the HTML when no headless
    browser was available to print it.
    """
    months = month_sequence(start_year, start_month, month_count)
    years = sorted({year for year, _ in months})

    date_to_fests, multi_day = build_festival_index(
        [generate_jain_festivals(year, lat, lon, ayanamsa, profile, sunrise_rule=sunrise_rule) for year in years]
    )

    samvat_by_year = {}
    for year in years:
        chaitra_shukla_1 = find_chaitra_shukla_1(year, lat, lon, tz_offset, ayanamsa, sunrise_rule=sunrise_rule)
        diwali = find_diwali(year, lat, lon, tz_offset, ayanamsa, sunrise_rule=sunrise_rule)
        anchor = date(year, 6, 15)
        samvat_by_year[year] = (
            get_vikram_samvat(anchor, chaitra_shukla_1),
            get_vira_nirvana_samvat(anchor, diwali),
        )

    rows_by_month = {
        (year, month): build_month_rows(
            year, month, lat=lat, lon=lon, tz_offset=tz_offset, ayanamsa=ayanamsa,
            date_to_fests=date_to_fests, calendar_system=calendar_system,
            tz_name=tz_name, clock=clock, sunrise_rule=sunrise_rule,
        )
        for year, month in months
    }

    first, last = months[0], months[-1]
    title = (f"जैन एवं वैदिक सम्पूर्ण पंचांग "
             f"({hindi_greg_month(*first)} – {hindi_greg_month(*last)})")

    html = render_calendar_html(months, rows_by_month, multi_day, samvat_by_year, title=title)

    html_path = out_pdf_path.replace(".pdf", ".html")
    os.makedirs(os.path.dirname(os.path.abspath(out_pdf_path)), exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write(html)

    if not _html_to_pdf(html_path, out_pdf_path):
        print(f"Edge not available; wrote HTML only: {os.path.abspath(html_path)}")
        return html_path

    size = os.path.getsize(out_pdf_path)
    print(f"Generated PDF: {os.path.abspath(out_pdf_path)} ({size:,} bytes)")
    return out_pdf_path


def main(argv: list[str] | None = None) -> None:
    import argparse

    from astronomy import CLOCK_MODES, SUNRISE_RULES

    parser = argparse.ArgumentParser(description="Generate the Hindi Panchang calendar PDF.")
    parser.add_argument("--start-year", type=int, default=2026)
    parser.add_argument("--start-month", type=int, default=3)
    parser.add_argument("--months", type=int, default=13)
    parser.add_argument("--lat", type=float, default=26.9124)
    parser.add_argument("--lon", type=float, default=75.7873)
    parser.add_argument("--tz-offset", type=float, default=5.5)
    parser.add_argument("--ayanamsa", default="Lahiri")
    parser.add_argument("--profile", default="all")
    parser.add_argument("--calendar-system", default="purnimanta",
                        choices=["purnimanta", "amanta"])
    parser.add_argument("--out", default=None)
    parser.add_argument("--tz-name", default=None,
                        help="IANA zone (e.g. America/New_York); lets --clock pick each day's offset")
    parser.add_argument("--clock", default="standard", choices=CLOCK_MODES)
    parser.add_argument("--sunrise", default="modern", choices=SUNRISE_RULES)
    args = parser.parse_args(argv)

    last_year, last_month = month_sequence(args.start_year, args.start_month, args.months)[-1]
    out = args.out or (
        f"output/Jain_Vedic_Panchang_{args.start_year}_{args.start_month:02d}"
        f"_{last_year}_{last_month:02d}_Hindi.pdf"
    )

    generate_hindi_pdf_calendar(
        out,
        start_year=args.start_year, start_month=args.start_month, month_count=args.months,
        lat=args.lat, lon=args.lon, tz_offset=args.tz_offset, ayanamsa=args.ayanamsa,
        profile=args.profile, calendar_system=args.calendar_system,
        tz_name=args.tz_name, clock=args.clock, sunrise_rule=args.sunrise,
    )


if __name__ == "__main__":
    main()
