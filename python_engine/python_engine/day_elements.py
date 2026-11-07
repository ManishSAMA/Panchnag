"""Panchang elements across one sunrise-to-sunrise day, as the app's Panchang section reads them.

- Tithi, nakshatra, yoga and the Moon's Rashi: the one holding at the start
  instant and the one after it, each with its real end, even when that end
  falls after the next sunrise ("तृतीया 13:10 तक, कल").
- Karana: every Karana holding between sunrise and the next sunrise. A Karana
  is half a tithi (6° of Moon − Sun) and lasts 9.4–13 hours, so a day holds
  two to four of them.
- The Sun's Rashi, and the gata: how many days the Sun has been in it, the
  day holding the Sankranti (the Sun's entry) being day 1.

Rashi indices are 0-based (0 = Mesha … 11 = Meena), as `astronomy.RASHI_NAMES`;
tithi 1–30, nakshatra 1–27, yoga 1–27 and karana 1–60 are 1-based, as `panchang.py`.
Design: plans/panchang-section-and-pothi.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from astronomy import get_planetary_longitude, get_sunrise
from panchang import (
    _find_exact_end_time,
    get_karana_index_at_jd,
    get_nakshatra_at_jd,
    get_tithi_at_jd,
    get_yoga_at_jd,
)

_AYANAMSA = "Lahiri"
# Step past an end before reading the next element, as panchang_service does.
_NUDGE_DAYS = 30.0 / 86400.0
_BISECTION_STEPS = 50


@dataclass(frozen=True)
class Span:
    index: int
    ends_jd: float


@dataclass(frozen=True)
class DaySpan:
    """An element within a day; ends_jd is None when it lasts past the next sunrise."""

    index: int
    ends_jd: float | None


@dataclass(frozen=True)
class Gata:
    rashi: int
    day: int


def moon_rashi_at(jd: float) -> int:
    return int(get_planetary_longitude(jd, "Moon", _AYANAMSA) / 30.0) % 12


def sun_rashi_at(jd: float) -> int:
    return int(get_planetary_longitude(jd, "Sun", _AYANAMSA) / 30.0) % 12


def _span_at(jd: float, index_at: Callable[[float, str], int]) -> Span:
    index = index_at(jd, _AYANAMSA)
    return Span(index=index, ends_jd=_find_exact_end_time(jd, index_at, index, _AYANAMSA))


def _pair(start_jd: float, index_at: Callable[[float, str], int]) -> tuple[Span, Span]:
    current = _span_at(start_jd, index_at)
    return current, _span_at(current.ends_jd + _NUDGE_DAYS, index_at)


def tithi_pair(reference_jd: float) -> tuple[Span, Span]:
    """The tithi holding at the Jain reference instant (sunrise + 6 ghati) and the next."""
    return _pair(reference_jd, get_tithi_at_jd)


def nakshatra_pair(sunrise_jd: float) -> tuple[Span, Span]:
    return _pair(sunrise_jd, get_nakshatra_at_jd)


def yoga_pair(sunrise_jd: float) -> tuple[Span, Span]:
    return _pair(sunrise_jd, get_yoga_at_jd)


def moon_rashi_pair(sunrise_jd: float) -> tuple[Span, Span]:
    # A Rashi is 30° of Moon, up to 2.7 days: the 3-day bracket of
    # _find_exact_end_time still holds it.
    return _pair(sunrise_jd, lambda jd, _ayanamsa: moon_rashi_at(jd))


def karanas_in_day(sunrise_jd: float, next_sunrise_jd: float) -> tuple[Span, ...]:
    def from_(jd: float) -> tuple[Span, ...]:
        span = _span_at(jd, get_karana_index_at_jd)
        if span.ends_jd >= next_sunrise_jd:
            return (span,)
        return (span, *from_(span.ends_jd + _NUDGE_DAYS))

    return from_(sunrise_jd)


def _sign_change(low: float, high: float, at: Callable[[float], int]) -> float:
    """The instant in (low, high] where at() leaves the value it has at low."""
    before = at(low)
    for _ in range(_BISECTION_STEPS):
        mid = (low + high) / 2.0
        if at(mid) == before:
            low = mid
        else:
            high = mid
    return high


def sun_rashis_in_day(sunrise_jd: float, next_sunrise_jd: float) -> tuple[DaySpan, ...]:
    """The Sun's Rashi, and on a Sankranti day the one it enters (it moves 1° a day)."""
    first = sun_rashi_at(sunrise_jd)
    if sun_rashi_at(next_sunrise_jd) == first:
        return (DaySpan(index=first, ends_jd=None),)
    sankranti = _sign_change(sunrise_jd, next_sunrise_jd, sun_rashi_at)
    return (DaySpan(index=first, ends_jd=sankranti), DaySpan(index=(first + 1) % 12, ends_jd=None))


# The Sun moves 0.95–1.02° a day: 30° of Rashi takes at most 32 days.
_LONGEST_RASHI_DAYS = 32.0


def gata(next_sunrise_jd: float, *, lat: float, lon: float, rule: str) -> Gata:
    """Days the Sun has been in its Rashi on the day ending at next_sunrise_jd.

    The day holding the Sankranti is day 1. The first sunrise after the
    Sankranti closes that day, so the count is the whole days from that
    sunrise to next_sunrise_jd, plus one.
    """
    rashi = sun_rashi_at(next_sunrise_jd)
    sankranti = _sign_change(next_sunrise_jd - _LONGEST_RASHI_DAYS, next_sunrise_jd, _entered(rashi))
    first_sunrise = get_sunrise(sankranti, lat, lon, rule)
    return Gata(rashi=rashi, day=round(next_sunrise_jd - first_sunrise) + 1)


def _entered(rashi: int) -> Callable[[float], int]:
    """1 once the Sun is in rashi, else 0, so the bisection finds the entry."""
    return lambda jd: int(sun_rashi_at(jd) == rashi)
