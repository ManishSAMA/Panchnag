"""Rahu Kaal, Yamaganda, Gulika and Abhijit: fixed parts of the daylight.

Rahu Kaal, Yamaganda and Gulika each take one of eight equal parts of
sunrise-to-sunset, the part set by the weekday; Abhijit is the eighth of
fifteen equal parts (the muhurta around local noon). Weekday tables:
Drik Panchang, "Rahu Kalam" tutorial (Yamardha method), and Hindutone,
"Rahu Kalam, Yamagandam and Gulika Kalam Explained" (weekday tables).
Design: plans/muhurat-section.md.
"""

from __future__ import annotations

import pytest

from panchang import (
    calculate_abhijit,
    calculate_gulika,
    calculate_rahu_kaal,
    calculate_yamaganda,
)

SUNRISE_JD = 2461354.5 + 6.2 / 24
SUNSET_JD = 2461354.5 + 17.6 / 24
WEEK = range(7)  # 0 = Sunday … 6 = Saturday

EIGHTH_PART_WINDOWS = {
    "rahu_kaal": calculate_rahu_kaal,
    "yamaganda": calculate_yamaganda,
    "gulika": calculate_gulika,
}

# Part (1-based, of eight) for Sunday … Saturday.
EXPECTED_PART = {
    "rahu_kaal": (8, 2, 7, 5, 6, 4, 3),
    "yamaganda": (5, 4, 3, 2, 1, 7, 6),
    "gulika": (7, 6, 5, 4, 3, 2, 1),
}


def _part_of(window: dict[str, float], parts: int) -> float:
    part_length = (SUNSET_JD - SUNRISE_JD) / parts
    return (window["start_jd"] - SUNRISE_JD) / part_length + 1


@pytest.mark.parametrize("name", EIGHTH_PART_WINDOWS)
@pytest.mark.parametrize("weekday", WEEK)
def test_window_is_one_eighth_of_the_daylight(name: str, weekday: int) -> None:
    window = EIGHTH_PART_WINDOWS[name](SUNRISE_JD, SUNSET_JD, weekday)
    assert window["end_jd"] - window["start_jd"] == pytest.approx((SUNSET_JD - SUNRISE_JD) / 8)


@pytest.mark.parametrize("name", EIGHTH_PART_WINDOWS)
@pytest.mark.parametrize("weekday", WEEK)
def test_window_lies_inside_the_daylight(name: str, weekday: int) -> None:
    window = EIGHTH_PART_WINDOWS[name](SUNRISE_JD, SUNSET_JD, weekday)
    assert SUNRISE_JD <= window["start_jd"] < window["end_jd"] <= SUNSET_JD + 1e-9


@pytest.mark.parametrize("name", EIGHTH_PART_WINDOWS)
def test_the_weekday_picks_the_part(name: str) -> None:
    parts = tuple(
        round(_part_of(EIGHTH_PART_WINDOWS[name](SUNRISE_JD, SUNSET_JD, weekday), 8))
        for weekday in WEEK
    )
    assert parts == EXPECTED_PART[name]


@pytest.mark.parametrize("weekday", WEEK)
def test_rahu_yamaganda_and_gulika_never_share_a_part(weekday: int) -> None:
    starts = {
        round(window(SUNRISE_JD, SUNSET_JD, weekday)["start_jd"], 9)
        for window in EIGHTH_PART_WINDOWS.values()
    }
    assert len(starts) == 3


def test_abhijit_is_the_eighth_of_fifteen_parts() -> None:
    window = calculate_abhijit(SUNRISE_JD, SUNSET_JD)
    assert window["end_jd"] - window["start_jd"] == pytest.approx((SUNSET_JD - SUNRISE_JD) / 15)
    assert round(_part_of(window, 15)) == 8


def test_abhijit_is_centred_on_local_noon() -> None:
    window = calculate_abhijit(SUNRISE_JD, SUNSET_JD)
    assert (window["start_jd"] + window["end_jd"]) / 2 == pytest.approx((SUNRISE_JD + SUNSET_JD) / 2)


def test_a_shorter_day_gives_a_shorter_abhijit() -> None:
    long_day = calculate_abhijit(SUNRISE_JD, SUNSET_JD)
    short_day = calculate_abhijit(SUNRISE_JD + 0.02, SUNSET_JD - 0.02)
    assert short_day["end_jd"] - short_day["start_jd"] < long_day["end_jd"] - long_day["start_jd"]
