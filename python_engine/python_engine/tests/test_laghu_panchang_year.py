"""The Laghu Panchang year: 24 half-month tables built from the app's own engine.

Invariants only -- the numbers come from the ephemeris and are covered by the
engine's own tests. Festival placement is checked against the festival service
itself, so the booklet and the app's calendar cannot drift apart.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from functools import cache

from hindi_export import RASHI_HI
from jain_observances.festival_service import generate_jain_festivals
from laghu_panchang import AHORATRA, COLUMN_HEADERS, LaghuHalf, build_laghu_year

DELHI = {"lat": 28.6139, "lon": 77.2090, "tz_name": "Asia/Kolkata"}
TRENTON = {"lat": 40.2203, "lon": -74.7658, "tz_name": "America/New_York"}
PROFILE = "shwetambar_murtipujak_tapagachchha"
VARA_ABBR = ("र", "सो", "मं", "बु", "बृ", "शु", "श")  # Sunday first
TIME = re.compile(r"^(\d{2}):(\d{2})$")
TITHI = re.compile(r"^(\d{1,2}|(अ\.)?\S+\.(शु|कृ)\. 01)(-\d{1,2})?$")


@cache
def delhi_2027() -> tuple[LaghuHalf, ...]:
    return build_laghu_year(year=2027, ayanamsa="Lahiri", profile=PROFILE, **DELHI)


def _days():
    return [day for half in delhi_2027() for day in half.days]


def test_the_year_is_24_half_months_covering_every_date_once_in_order():
    halves = delhi_2027()
    expected = [date(2027, 1, 1) + timedelta(days=n) for n in range(365)]

    assert len(halves) == 24
    assert [day.date for day in _days()] == expected


def test_each_month_splits_at_the_15th():
    for half in delhi_2027():
        first, last = half.days[0].date, half.days[-1].date
        assert first.month == last.month
        assert (first.day, last.day <= 15) in {(1, True), (16, False)}


def test_every_row_has_one_cell_per_column():
    assert len(COLUMN_HEADERS) == 11
    assert all(len(day.cells) == len(COLUMN_HEADERS) for day in _days())


def test_shubh_is_either_swastika_or_dash_and_both_occur():
    marks = [day.shubh for day in _days()]

    assert set(marks) == {"卐", "-"}


def test_weekday_matches_the_date():
    assert all(day.vara == VARA_ABBR[(day.date.weekday() + 1) % 7] for day in _days())


def test_time_cells_are_clock_readings_within_the_solar_day_or_ahoratra():
    for day in _days():
        for cell in (day.tithi_end, day.nakshatra_end):
            if cell == AHORATRA:
                continue
            hours, minutes = map(int, TIME.match(cell).groups())
            assert 0 <= hours < 32 and minutes < 60, (day.date, cell)


def test_tithi_cells_are_paksha_numbers_or_a_month_marked_pratipada():
    for day in _days():
        assert TITHI.match(day.jain_tithi), (day.date, day.jain_tithi)
        assert TITHI.match(day.udaya_tithi), (day.date, day.udaya_tithi)


def test_every_lunar_fortnight_starts_with_a_marked_pratipada():
    pratipadas = [day for day in _days() if day.udaya_tithi.endswith(" 01") or " 01-" in day.udaya_tithi]

    # 12-13 lunations a year, two pakshas each; a kshaya Pratipada can drop one.
    assert 22 <= len(pratipadas) <= 27


def test_moon_cell_is_a_full_sign_or_an_abbreviated_entry_with_time():
    entry = re.compile(r"^\S+-\d{2}:\d{2}$")

    assert all(day.moon_sign in RASHI_HI or entry.match(day.moon_sign) for day in _days())


def test_headers_name_the_gregorian_span_and_both_samvats():
    january_first, january_second = delhi_2027()[:2]

    assert january_first.date_range == "1 जनवरी से 15 जनवरी 2027 तक।"
    assert january_second.date_range == "16 जनवरी से 31 जनवरी 2027 तक।"
    assert re.fullmatch(r"वीर निर्वाण सं\. \d{4}(–\d{2})?\s+विक्रम संवत् \d{4}(–\d{2})?", january_first.samvat)
    assert re.fullmatch(r"\S+ (शुक्ल|कृष्ण) \S+ से \S+ (शुक्ल|कृष्ण) \S+ तक", january_first.tithi_range)
    assert re.fullmatch(r"सूर्योदय – \d{2}:\d{2} बजे, सूर्यास्त – \d{2}:\d{2} बजे", january_first.sun_times)


def test_the_app_calendars_kalyanaks_appear_on_their_dates():
    calendar = generate_jain_festivals(2027, DELHI["lat"], DELHI["lon"], "Lahiri", PROFILE)
    by_date = {day.date.isoformat(): day.events for day in _days()}
    single_day = [f for f in calendar["festivals"] if f["start_date"] == f["end_date"] and f.get("name_hindi")]

    assert single_day
    for festival in single_day:
        assert festival["name_hindi"] in by_date[festival["start_date"]], festival["name"]


def _sunrise_minutes(half: LaghuHalf) -> int:
    hours, minutes = re.search(r"सूर्योदय – (\d{2}):(\d{2})", half.sun_times).groups()
    return int(hours) * 60 + int(minutes)


def _march(place: dict, **settings) -> tuple[LaghuHalf, LaghuHalf]:
    return build_laghu_year(year=2027, ayanamsa="Lahiri", profile=PROFILE, months=(3,), **place, **settings)


def test_daylight_clock_jumps_the_header_sunrise_by_the_dst_hour():
    """US DST starts 14 Mar 2027: on the wall clock, sunrise on the 16th is later than on the 1st."""
    march_first, march_second = _march(TRENTON, clock="daylight")

    assert _sunrise_minutes(march_second) - _sunrise_minutes(march_first) > 20


def test_standard_clock_is_the_default_and_moves_smoothly_through_march():
    """In standard time the March sunrise just keeps getting earlier, as in the NJ reference sheet."""
    default = _march(TRENTON)
    march_first, march_second = _march(TRENTON, clock="standard")

    assert default == (march_first, march_second)
    assert 0 < _sunrise_minutes(march_first) - _sunrise_minutes(march_second) < 30


NEW_JERSEY = {"lat": 40 + 50 / 60, "lon": -(74 + 6 / 60), "tz_name": "America/New_York"}


def _minutes(cell: str) -> int:
    hours, minutes = map(int, re.search(r"(\d{2}):(\d{2})", cell).groups())
    return hours * 60 + minutes


def test_standard_time_matches_the_new_jersey_reference_after_the_dst_change():
    """PanchangReport_2654.pdf (40°50'N 74°06'W, 2027, EST all year), March page.

    These days fall after the 14 Mar DST change, where the wall clock reads an
    hour later; in standard time we agree with the sheet to a few minutes.
    """
    days = {day.date.day: day for half in _march(NEW_JERSEY, clock="standard") for day in half.days}
    reference = [
        (days[14].tithi_end, "24:24"),     # 14 Mar, Saptami ends 24:24:59
        (days[15].moon_sign, "10:24"),     # 15 Mar, Moon enters Mithuna 10:24:58
        (days[22].nakshatra_end, "10:19"), # 22 Mar, Uttara Phalguni ends 10:19:27
        (days[30].tithi_end, "09:13"),     # 30 Mar, Ashtami ends 09:13:37
    ]

    for ours, theirs in reference:
        assert abs(_minutes(ours) - _minutes(theirs)) <= 5, (ours, theirs)


def test_traditional_sunrise_matches_the_new_jersey_reference_header():
    """PanchangReport_2654.pdf, March: sunrise 1 Mar 06:34, 16 Mar 06:10 (EST)."""
    march_first, march_second = _march(NEW_JERSEY, clock="standard", sunrise_rule="traditional")

    assert abs(_sunrise_minutes(march_first) - (6 * 60 + 34)) <= 1
    assert abs(_sunrise_minutes(march_second) - (6 * 60 + 10)) <= 1


def test_the_traditional_rule_moves_sunrise_later_than_the_modern_one():
    modern, _ = _march(NEW_JERSEY, clock="standard", sunrise_rule="modern")
    traditional, _ = _march(NEW_JERSEY, clock="standard", sunrise_rule="traditional")

    assert 2 <= _sunrise_minutes(traditional) - _sunrise_minutes(modern) <= 8
