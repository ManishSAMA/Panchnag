"""One sunrise-to-sunrise day's muhurats, as the app's Muhurat section reads them.

These are invariants over a month of Delhi days, not golden times: each window
lies in its day, each agrees with the calculation it comes from, and over a
lunar month every recurring muhurat (Panchak, Bhadra, Gandmool) shows up.
Design: plans/muhurat-section.md.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import cache

import pytest

from astronomy import get_planetary_longitude
from muhurat_day import MuhuratDay, muhurat_day
from panchang import (
    calculate_abhijit,
    calculate_agni_vaas,
    calculate_gulika,
    calculate_rahu_kaal,
    calculate_yamaganda,
    chandra_bal_rashis,
    get_nakshatra_at_jd,
    get_tithi_at_jd,
)
from panchang_service import generate_location_panchang
from yoga_service import detect_all_yogas_for_day

DELHI = {"lat": 28.6139, "lon": 77.2090}
FIRST_DAY = date(2026, 10, 1)
MONTH = tuple(FIRST_DAY + timedelta(days=n) for n in range(30))
GANDMOOL = {1, 9, 10, 18, 19, 27}
KINDS = {"dainika", "aanandadi", "ravi", "jwalamukhi"}


@cache
def _events(local_date: date) -> tuple[float, float, float, int]:
    payload = generate_location_panchang(local_date, **DELHI)
    events = payload["events"]
    return (
        events["sunrise"]["jd"],
        events["sunset"]["jd"],
        events["next_sunrise"]["jd"],
        payload["panchang"]["vara"]["index"],
    )


@cache
def _day(local_date: date) -> MuhuratDay:
    sunrise, sunset, next_sunrise, _ = _events(local_date)
    return muhurat_day(
        local_date=local_date,
        sunrise_jd=sunrise,
        sunset_jd=sunset,
        next_sunrise_jd=next_sunrise,
        tz_name="Asia/Kolkata",
    )


def _inside_day(local_date: date, start: float, end: float) -> bool:
    sunrise, _, next_sunrise, _ = _events(local_date)
    return sunrise - 1e-9 <= start < end <= next_sunrise + 1e-9


@pytest.mark.parametrize("local_date", MONTH[:7])
def test_daylight_windows_follow_their_rules(local_date: date) -> None:
    sunrise, sunset, _, vara = _events(local_date)
    day = _day(local_date)
    assert (day.rahu_kaal.start_jd, day.rahu_kaal.end_jd) == tuple(
        calculate_rahu_kaal(sunrise, sunset, vara).values()
    )
    assert (day.yamaganda.start_jd, day.yamaganda.end_jd) == tuple(
        calculate_yamaganda(sunrise, sunset, vara).values()
    )
    assert (day.gulika.start_jd, day.gulika.end_jd) == tuple(
        calculate_gulika(sunrise, sunset, vara).values()
    )
    assert (day.abhijit.start_jd, day.abhijit.end_jd) == tuple(
        calculate_abhijit(sunrise, sunset).values()
    )


@pytest.mark.parametrize("local_date", MONTH)
def test_every_window_lies_in_its_day(local_date: date) -> None:
    day = _day(local_date)
    windows = [
        *day.bhadra,
        *day.gandmool,
        *day.yogas,
        *([day.panchak.window] if day.panchak.window else []),
    ]
    assert all(_inside_day(local_date, w.start_jd, w.end_jd) for w in windows)


def test_panchak_bhadra_and_gandmool_each_come_in_a_month() -> None:
    days = [_day(d) for d in MONTH]
    assert any(day.panchak.window for day in days)
    assert any(day.bhadra for day in days)
    assert any(day.gandmool for day in days)


@pytest.mark.parametrize("local_date", MONTH)
def test_panchak_window_or_next_period(local_date: date) -> None:
    panchak = _day(local_date).panchak
    if panchak.window is None:
        assert panchak.period is None
        assert panchak.next_period is not None
        assert panchak.next_period.start_jd > _events(local_date)[2]
        return
    assert panchak.period is not None
    assert panchak.period.start_jd <= panchak.window.start_jd
    assert panchak.window.end_jd <= panchak.period.end_jd


@pytest.mark.parametrize("local_date", MONTH)
def test_panchak_is_the_moon_in_its_last_sixty_degrees(local_date: date) -> None:
    window = _day(local_date).panchak.window
    if window is None:
        return
    middle = (window.start_jd + window.end_jd) / 2
    assert get_planetary_longitude(middle, "Moon", "Lahiri") >= 300.0


@pytest.mark.parametrize("local_date", MONTH)
def test_bhadra_residence_follows_the_moon_rashi(local_date: date) -> None:
    for window in _day(local_date).bhadra:
        middle = (window.start_jd + window.end_jd) / 2
        assert int(get_planetary_longitude(middle, "Moon", "Lahiri") // 30) == window.moon_rashi
        assert window.residence in {"Earth", "Heaven", "Underworld"}


@pytest.mark.parametrize("local_date", MONTH)
def test_gandmool_names_the_moons_nakshatra(local_date: date) -> None:
    for window in _day(local_date).gandmool:
        assert window.nakshatra in GANDMOOL
        middle = (window.start_jd + window.end_jd) / 2
        assert get_nakshatra_at_jd(middle, "Lahiri") == window.nakshatra


@pytest.mark.parametrize("local_date", MONTH)
def test_chandra_bal_covers_the_day(local_date: date) -> None:
    sunrise, _, next_sunrise, _ = _events(local_date)
    spans = _day(local_date).chandra_bal
    assert spans[0].moon_rashi == int(get_planetary_longitude(sunrise, "Moon", "Lahiri") // 30)
    assert spans[-1].ends_jd is None
    assert all(span.rashis == chandra_bal_rashis(span.moon_rashi) for span in spans)
    assert all(sunrise < span.ends_jd < next_sunrise for span in spans[:-1])
    assert len(spans) <= 2


@pytest.mark.parametrize("local_date", MONTH[:7])
def test_agni_vaas_reads_the_sunrise_tithi(local_date: date) -> None:
    sunrise, _, _, vara = _events(local_date)
    expected = calculate_agni_vaas(get_tithi_at_jd(sunrise, "Lahiri"), vara)
    agni = _day(local_date).agni_vaas
    assert (agni.residence, agni.is_auspicious) == (expected["residence"], expected["is_auspicious"])


@pytest.mark.parametrize("local_date", MONTH)
def test_every_day_has_an_aanandadi_yoga(local_date: date) -> None:
    yogas = _day(local_date).yogas
    assert {y.kind for y in yogas} <= KINDS
    assert any(y.kind == "aanandadi" for y in yogas)
    assert all(y.nature in {"shubh", "ashubh", "mishra"} for y in yogas)


def test_good_and_bad_dainika_yogas_both_come_in_a_month() -> None:
    natures = {y.nature for d in MONTH for y in _day(d).yogas if y.kind == "dainika"}
    assert {"shubh", "ashubh"} <= natures


def _source_yogas(local_date: date) -> list[tuple]:
    sunrise, _, next_sunrise, _ = _events(local_date)
    found = detect_all_yogas_for_day(
        date_obj=local_date, sunrise_jd=sunrise, next_sunrise_jd=next_sunrise, tz_name="Asia/Kolkata"
    )
    entries = [
        *found["yogas"],
        *found["aanandadi_yogas"],
        *found["ravi_yogas"],
        *(y for y in found["special_yogas"] if y["name"] == "Jwalamukhi"),
    ]
    return [
        (
            y["name"], y["start_jd"], y["end_jd"],
            y.get("is_nullified", False), y.get("cancelled", False), y.get("diminished", False),
            y.get("varjya_start_jd"), y.get("varjya_end_jd"),
        )
        for y in entries
    ]


@pytest.mark.parametrize("local_date", MONTH)
def test_yogas_are_the_yoga_services_with_their_flags_and_varjya(local_date: date) -> None:
    shown = [
        (
            y.name, y.start_jd, y.end_jd, y.is_nullified, y.cancelled, y.diminished,
            y.varjya.start_jd if y.varjya else None, y.varjya.end_jd if y.varjya else None,
        )
        for y in _day(local_date).yogas
    ]
    assert shown == _source_yogas(local_date)


def test_a_month_holds_a_flagged_yoga_and_a_varjya() -> None:
    yogas = [y for d in MONTH for y in _day(d).yogas]
    assert any(y.varjya for y in yogas)
    assert any(y.is_nullified or y.cancelled or y.diminished for y in yogas)
