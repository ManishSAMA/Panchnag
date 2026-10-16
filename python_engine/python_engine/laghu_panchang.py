"""
laghu_panchang.py -- the yearly "Laghu Panchang" booklet: data and cell text.

Layout follows the printed laghu panchang booklet (see
plans/laghu-panchang-export.md): one Gregorian month per page, split into two
half-month tables (1-15, 16-end), eleven columns per day.

Times are written as clock readings from the civil day's midnight, so an event
after midnight but before the next sunrise reads 25:47 rather than 01:47 -- the
traditional panchang convention, which keeps a solar day on one row.
"""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from astronomy import get_sunrise, get_sunset, local_time_to_jd
from hindi_calendar_pdf import (
    GREG_MONTHS_HINDI,
    _paksha_and_name,
    build_festival_index,
    hindi_month_name,
    merge_day_festivals,
    translate_fest,
)
from hindi_export import RASHI_HI
from jain_observances.festival_service import generate_jain_festivals
from panchang import (
    calculate_bhadra_kaal,
    calculate_jain_tithi_from_sunrise,
    calculate_panchak_kaal,
    find_chaitra_shukla_1,
    find_diwali,
    find_moon_rashi_change,
    generate_daily_panchang,
    get_purnimanta_month,
    get_tithi_at_jd,
    get_vara_from_date,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
    kshaya_tithi_between,
)
from yoga_service import detect_all_yogas_for_day

AHORATRA = "अहोरात्र"
SHUBH = "卍"
NOT_SHUBH = "-"

# Short forms as printed in the reference booklet, indexed like
# panchang.NAKSHATRA_NAMES / YOGA_NAMES / RASHI_HI.
NAKSHATRA_ABBR = (
    "अ.", "भ.", "कृ.", "रो.", "मृ.", "आ.", "पुन.", "पु.", "आश्ले.",
    "म.", "पू.फा.", "उ.फा.", "ह.", "चि.", "स्वा.", "वि.", "अनु.", "ज्ये.",
    "मू.", "पू.षा.", "उ.षा.", "श्र.", "ध.", "श.", "पू.भा.", "उ.भा.", "रे.",
)

# The booklet prints Siddhi/Siddha and Shubha/Shukla identically; the second of
# each pair is spelled out here so the two stay distinguishable.
YOGA_ABBR = (
    "वि.", "प्री.", "आ.", "सौ.", "शो.", "अ.", "सु.", "धृ.", "शू.",
    "गं.", "वृ.", "ध्रु.", "व्या.", "ह.", "वज्र", "सि.", "व्य.", "वरी.",
    "परि.", "शि.", "सिद्ध", "सा.", "शुभ", "शु.", "ब्र.", "ऐ.", "वै.",
)

RASHI_ABBR = (
    "मे.", "वृ.", "मि.", "क.", "सिं.", "कन्या",
    "तु.", "वृश्चि.", "ध.", "म.", "कुं.", "मी.",
)

MONTH_ABBR = {
    "CHAITRA": "चै.", "VAISHAKHA": "वै.", "JYESHTHA": "ज्ये.", "ASHADHA": "आषा.",
    "SHRAVANA": "श्रा.", "BHADRAPADA": "भा.", "ASHWIN": "आश्वि.", "KARTIKA": "का.",
    "AGRAHAYANA": "मार्ग.", "PAUSHA": "पौ.", "MAGHA": "मा.", "PHALGUNA": "फा.",
}

_YOGA_LISTS = ("yogas", "aanandadi_yogas", "ravi_yogas", "special_yogas")


# ---------------------------------------------------------------------------
# Cell formatters (pure)
# ---------------------------------------------------------------------------

def clock_from_midnight(jd: float, midnight_jd: float) -> str:
    """"25:47" -- hours and minutes since the civil day's local midnight."""
    hours, minutes = divmod(round((jd - midnight_jd) * 1440.0), 60)
    return f"{hours:02d}:{minutes:02d}"


def end_time_cell(end_jd: float, *, midnight_jd: float, next_sunrise_jd: float) -> str:
    """End time of a Tithi or Nakshatra, or अहोरात्र when it outlasts the day."""
    if end_jd > next_sunrise_jd:
        return AHORATRA
    return clock_from_midnight(end_jd, midnight_jd)


def _paksha_number(tithi_index: int) -> int:
    if tithi_index == 30:
        return 30
    return tithi_index if tithi_index <= 15 else tithi_index - 15


def _month_abbr(month_name: str) -> str:
    base = month_name.removeprefix("Adhika ").strip()
    abbr = MONTH_ABBR.get(base.upper(), base)
    return f"अ.{abbr}" if month_name.startswith("Adhika ") else abbr


def tithi_cell(tithi_index: int, *, month_name: str, kshaya_index: int | None = None) -> str:
    """Paksha-relative Tithi number; Pratipada carries month and paksha."""
    if tithi_index in (1, 16):
        paksha = "शु." if tithi_index == 1 else "कृ."
        text = f"{_month_abbr(month_name)}{paksha} 01"
    else:
        text = str(_paksha_number(tithi_index))

    if kshaya_index is None:
        return text
    return f"{text}-{_paksha_number(kshaya_index)}"


def _active_highly_auspicious(yoga: dict, sunrise_jd: float) -> bool:
    return (
        yoga.get("nature") == "shubh"
        and yoga.get("severity") == "highly_auspicious"
        and not yoga.get("is_nullified")
        and not yoga.get("cancelled")
        and yoga["start_jd"] <= sunrise_jd < yoga["end_jd"]
    )


def shubh_mark(yoga_result: dict, sunrise_jd: float) -> str:
    """卍 when a highly auspicious yoga is in force at sunrise, else "-"."""
    yogas = (yoga for kind in _YOGA_LISTS for yoga in yoga_result.get(kind, ()))
    return SHUBH if any(_active_highly_auspicious(yoga, sunrise_jd) for yoga in yogas) else NOT_SHUBH


def moon_sign_cell(
    rashi_at_sunrise: int,
    new_rashi: int | None,
    entry_jd: float | None,
    *,
    midnight_jd: float,
) -> str:
    """Full sign name, or "वृ.-28:21" when the Moon enters a new sign that day."""
    if new_rashi is None or entry_jd is None:
        return RASHI_HI[rashi_at_sunrise]
    return f"{RASHI_ABBR[new_rashi]}-{clock_from_midnight(entry_jd, midnight_jd)}"


def _merge_contiguous(windows: list[dict]) -> list[dict]:
    """Rejoin windows split only because the Moon changed sign mid-window."""
    merged: list[dict] = []
    for window in sorted(windows, key=lambda w: w["start_jd"]):
        if merged and abs(window["start_jd"] - merged[-1]["end_jd"]) < 1e-6:
            merged[-1] = {**merged[-1], "end_jd": window["end_jd"], "clipped_end": window["clipped_end"]}
        else:
            merged.append(dict(window))
    return merged


def _window_text(label: str, window: dict, midnight_jd: float) -> str:
    start = clock_from_midnight(window["start_jd"], midnight_jd)
    end = clock_from_midnight(window["end_jd"], midnight_jd)
    if window["clipped_start"] and window["clipped_end"]:
        return ""
    if window["clipped_start"]:
        return f"{label} {end} तक"
    if window["clipped_end"]:
        return f"{label} {start} से"
    return f"{label} {start} से {end} तक"


def bhadra_text(windows: list[dict], *, midnight_jd: float) -> str:
    """"भ. 25:47 से" / "भ. 14:24 तक" / "भ. 16:31 से 29:18 तक"."""
    parts = (_window_text("भ.", window, midnight_jd) for window in _merge_contiguous(windows))
    return ", ".join(part for part in parts if part)


def panchak_text(windows: list[dict], *, midnight_jd: float) -> str:
    """Panchak's start or end on the day it happens; silent on days wholly inside it."""
    parts = (_window_text("पंचक", window, midnight_jd) for window in windows)
    return ", ".join(part for part in parts if part)


# festival_service tags a Kalyanak pulled onto a civil date of another tithi with
# its own tithi in English ("[Ekadashi] ..."); the booklet is all-Hindi.
_NATIVE_TITHI_TAG_HI = {
    f"[{english}]": f"[{hindi}]"
    for english, hindi in zip(
        ("Ekam", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi", "Saptami", "Ashtami",
         "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", "Amavasya"),
        ("प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
         "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा", "अमावस्या"),
    )
}


def _hindi_native_tag(label: str) -> str:
    tag, _, rest = label.partition(" ")
    return f"{_NATIVE_TITHI_TAG_HI[tag]} {rest}" if tag in _NATIVE_TITHI_TAG_HI else label


def festival_text(festivals: list[dict]) -> str:
    """Hindi festival names for the day, de-duplicated across schools."""
    labels = []
    for festival in merge_day_festivals(festivals):
        label = _hindi_native_tag(translate_fest(festival))
        tag = festival.get("_tag")
        if tag and f"({tag})" not in label:
            label = f"{label} ({tag})"
        if label and label not in labels:
            labels.append(label)
    return ", ".join(labels)


# ---------------------------------------------------------------------------
# The year
# ---------------------------------------------------------------------------

COLUMN_HEADERS = (
    "दि.", "शुभ दि.", "जैन तिथि", "उदय तिथि", "वा.", "तिथि समाप्ति समय",
    "नक्षत्र", "नक्षत्र समाप्ति समय", "योग", "चन्द्र राशि प्रवेश", "पर्व, त्यौहार, पंचक आदि",
)

VARA_ABBR = ("र", "सो", "मं", "बु", "बृ", "शु", "श")  # Sunday first, as get_vara_from_date


@dataclass(frozen=True)
class LaghuDay:
    date: date
    shubh: str
    jain_tithi: str
    udaya_tithi: str
    vara: str
    tithi_end: str
    nakshatra: str
    nakshatra_end: str
    yoga: str
    moon_sign: str
    events: str

    @property
    def cells(self) -> tuple[str, ...]:
        """The row in COLUMN_HEADERS order."""
        return (
            str(self.date.day), self.shubh, self.jain_tithi, self.udaya_tithi, self.vara,
            self.tithi_end, self.nakshatra, self.nakshatra_end, self.yoga, self.moon_sign, self.events,
        )


@dataclass(frozen=True)
class LaghuHalf:
    samvat: str
    date_range: str
    tithi_range: str
    sun_times: str
    days: tuple[LaghuDay, ...]


@dataclass(frozen=True)
class _SolarDay:
    """The per-day astronomy every cell is derived from."""
    date: date
    midnight_jd: float
    sunrise_jd: float
    udaya_tithi: int
    udaya_month: str
    jain_tithi: int
    jain_month: str


def _utc_offset_hours(day: date, tz_name: str) -> float:
    """Offset in force at local noon, so DST days use their own clock."""
    noon = datetime(day.year, day.month, day.day, 12, tzinfo=ZoneInfo(tz_name))
    return noon.utcoffset().total_seconds() / 3600.0


def _solar_day(day: date, *, lat: float, lon: float, tz_name: str, ayanamsa: str) -> _SolarDay:
    midnight_jd = local_time_to_jd(day.year, day.month, day.day, 0.0, _utc_offset_hours(day, tz_name))
    sunrise_jd = get_sunrise(midnight_jd, lat, lon)
    jain = calculate_jain_tithi_from_sunrise(sunrise_jd, ayanamsa)
    return _SolarDay(
        date=day,
        midnight_jd=midnight_jd,
        sunrise_jd=sunrise_jd,
        udaya_tithi=get_tithi_at_jd(sunrise_jd, ayanamsa),
        udaya_month=get_purnimanta_month(sunrise_jd, ayanamsa)[0],
        jain_tithi=jain["Jain_Tithi_Index"],
        jain_month=get_purnimanta_month(jain["Jain_Tithi_Reference_JD"], ayanamsa)[0],
    )


def _laghu_day(
    today: _SolarDay,
    tomorrow: _SolarDay,
    *,
    tz_name: str,
    ayanamsa: str,
    festivals: list[dict],
) -> LaghuDay:
    sunrise, next_sunrise, midnight = today.sunrise_jd, tomorrow.sunrise_jd, today.midnight_jd
    panchang = generate_daily_panchang(sunrise, ayanamsa, local_date=today.date)
    yogas = detect_all_yogas_for_day(
        date_obj=today.date, sunrise_jd=sunrise, next_sunrise_jd=next_sunrise,
        tz_name=tz_name, ayanamsa=ayanamsa,
    )
    rashi, new_rashi, entry_jd = find_moon_rashi_change(sunrise, next_sunrise, ayanamsa)
    events = (
        festival_text(festivals),
        bhadra_text(calculate_bhadra_kaal(sunrise, next_sunrise, ayanamsa), midnight_jd=midnight),
        panchak_text(calculate_panchak_kaal(sunrise, next_sunrise, ayanamsa)["windows"], midnight_jd=midnight),
    )
    return LaghuDay(
        date=today.date,
        shubh=shubh_mark(yogas, sunrise),
        jain_tithi=tithi_cell(
            today.jain_tithi, month_name=today.jain_month,
            kshaya_index=kshaya_tithi_between(today.jain_tithi, tomorrow.jain_tithi),
        ),
        udaya_tithi=tithi_cell(
            today.udaya_tithi, month_name=today.udaya_month,
            kshaya_index=kshaya_tithi_between(today.udaya_tithi, tomorrow.udaya_tithi),
        ),
        vara=VARA_ABBR[get_vara_from_date(today.date)],
        tithi_end=end_time_cell(panchang["Tithi_End_JD"], midnight_jd=midnight, next_sunrise_jd=next_sunrise),
        nakshatra=NAKSHATRA_ABBR[panchang["Nakshatra_Index"] - 1],
        nakshatra_end=end_time_cell(panchang["Nakshatra_End_JD"], midnight_jd=midnight, next_sunrise_jd=next_sunrise),
        yoga=YOGA_ABBR[panchang["Yoga_Index"] - 1],
        moon_sign=moon_sign_cell(rashi, new_rashi, entry_jd, midnight_jd=midnight),
        events=", ".join(part for part in events if part),
    )


def _year_span(first: int, last: int) -> str:
    return str(first) if first == last else f"{first}–{last % 100:02d}"


def _tithi_name(solar: _SolarDay) -> str:
    paksha, name = _paksha_and_name(solar.udaya_tithi)
    is_adhika = solar.udaya_month.startswith("Adhika ")
    month = hindi_month_name(solar.udaya_month, is_adhika)
    return f"{month} {paksha} {name.split(' (')[0]}"


def _half(
    solar_days: list[_SolarDay],
    days: tuple[LaghuDay, ...],
    *,
    lat: float,
    lon: float,
    chaitra_shukla_1: date,
    diwali: date,
) -> LaghuHalf:
    first, last = solar_days[0], solar_days[-1]
    vira = [get_vira_nirvana_samvat(s.date, diwali) for s in solar_days]
    vikram = [get_vikram_samvat(s.date, chaitra_shukla_1) for s in solar_days]
    month = GREG_MONTHS_HINDI[first.date.month - 1]
    sunrise = clock_from_midnight(first.sunrise_jd, first.midnight_jd)
    sunset = clock_from_midnight(get_sunset(first.sunrise_jd, lat, lon), first.midnight_jd)
    return LaghuHalf(
        samvat=(
            f"वीर निर्वाण सं. {_year_span(min(vira), max(vira))}   "
            f"विक्रम संवत् {_year_span(min(vikram), max(vikram))}"
        ),
        date_range=f"{first.date.day} {month} से {last.date.day} {month} {first.date.year} तक।",
        tithi_range=f"{_tithi_name(first)} से {_tithi_name(last)} तक",
        sun_times=f"सूर्योदय – {sunrise} बजे, सूर्यास्त – {sunset} बजे",
        days=days,
    )


def build_laghu_year(
    *,
    year: int,
    lat: float,
    lon: float,
    tz_name: str,
    ayanamsa: str = "Lahiri",
    profile: str = "shwetambar_murtipujak_tapagachchha",
    months: Iterable[int] = range(1, 13),
) -> tuple[LaghuHalf, ...]:
    """The booklet's half-month tables, two per requested month, in order."""
    month_list = sorted(months)
    first_day = date(year, month_list[0], 1)
    last_day = date(year, month_list[-1], calendar.monthrange(year, month_list[-1])[1])
    # One day past the end: each row needs the next sunrise and next Tithi.
    span = [first_day + timedelta(days=n) for n in range((last_day - first_day).days + 2)]
    solar = [_solar_day(day, lat=lat, lon=lon, tz_name=tz_name, ayanamsa=ayanamsa) for day in span]
    solar_by_date = {s.date: s for s in solar}

    date_to_fests, _ = build_festival_index([generate_jain_festivals(year, lat, lon, ayanamsa, profile)])
    january_offset = _utc_offset_hours(date(year, 1, 1), tz_name)
    chaitra_shukla_1 = find_chaitra_shukla_1(year, lat, lon, january_offset, ayanamsa)
    diwali = find_diwali(year, lat, lon, january_offset, ayanamsa)

    rows = {
        today.date: _laghu_day(
            today, tomorrow, tz_name=tz_name, ayanamsa=ayanamsa,
            festivals=date_to_fests.get(today.date.isoformat(), []),
        )
        for today, tomorrow in zip(solar, solar[1:])
    }

    def half(month: int, first: int, last: int) -> LaghuHalf:
        dates = [date(year, month, d) for d in range(first, last + 1)]
        return _half(
            [solar_by_date[d] for d in dates], tuple(rows[d] for d in dates),
            lat=lat, lon=lon, chaitra_shukla_1=chaitra_shukla_1, diwali=diwali,
        )

    return tuple(
        half(month, first, last)
        for month in month_list
        for first, last in ((1, 15), (16, calendar.monthrange(year, month)[1]))
    )
