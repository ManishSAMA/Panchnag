"""One sunrise-to-sunrise day's muhurats, as the app's Muhurat section reads them.

- Rahu Kaal, Yamaganda, Gulika: one eighth of the daylight each, by weekday.
- Abhijit: the 8th of the 15 daylight muhurtas.
- Panchak: the Moon in sidereal 300°–360°; today's window and its whole period,
  or the next period when today has none.
- Bhadra: the Vishti karana windows, with the Moon's Rashi and residence.
- Gandmool: the windows of the Moon in the six junction nakshatras.
- Chandra Bal: the Moon's Rashi through the day (one or two spans) and the
  birth Rashis that have Chandra Bal in each.
- Agni Vaas: from the tithi at sunrise and the weekday.
- Yogas: the Dainika, Aanandadi, Ravi and Jwalamukhi yogas of `yoga_service`.

Every instant is a UT Julian Day, so the display clock never changes a reading.
Rashi indices are 0-based (0 = Mesha), nakshatras 1-based. Design:
plans/muhurat-section.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from astronomy import RASHI_NAMES
from panchang import (
    calculate_abhijit,
    calculate_agni_vaas,
    calculate_bhadra_kaal,
    calculate_gulika,
    calculate_panchak_kaal,
    calculate_rahu_kaal,
    calculate_yamaganda,
    chandra_bal_rashis,
    find_moon_rashi_change,
    get_tithi_at_jd,
    get_vara_from_date,
)
from yoga_service import detect_all_yogas_for_day

_AYANAMSA = "Lahiri"


@dataclass(frozen=True)
class Window:
    start_jd: float
    end_jd: float


@dataclass(frozen=True)
class PanchakReading:
    window: Window | None
    period: Window | None
    next_period: Window | None


@dataclass(frozen=True)
class BhadraWindow:
    start_jd: float
    end_jd: float
    moon_rashi: int
    residence: str


@dataclass(frozen=True)
class GandmoolWindow:
    start_jd: float
    end_jd: float
    nakshatra: int


@dataclass(frozen=True)
class ChandraBalSpan:
    """The Moon's Rashi until ends_jd (None: past the next sunrise)."""

    moon_rashi: int
    ends_jd: float | None
    rashis: tuple[int, ...]


@dataclass(frozen=True)
class AgniVaas:
    residence: str
    is_auspicious: bool


@dataclass(frozen=True)
class DayYoga:
    kind: str  # dainika | aanandadi | ravi | jwalamukhi
    name: str
    nature: str  # shubh | ashubh
    start_jd: float
    end_jd: float
    is_nullified: bool
    cancelled: bool
    diminished: bool
    varjya: Window | None


@dataclass(frozen=True)
class MuhuratDay:
    rahu_kaal: Window
    yamaganda: Window
    gulika: Window
    abhijit: Window
    panchak: PanchakReading
    bhadra: tuple[BhadraWindow, ...]
    gandmool: tuple[GandmoolWindow, ...]
    chandra_bal: tuple[ChandraBalSpan, ...]
    agni_vaas: AgniVaas
    yogas: tuple[DayYoga, ...]


def muhurat_day(
    *,
    local_date: date,
    sunrise_jd: float,
    sunset_jd: float,
    next_sunrise_jd: float,
    tz_name: str,
) -> MuhuratDay:
    vara = get_vara_from_date(local_date)
    found = detect_all_yogas_for_day(
        date_obj=local_date,
        sunrise_jd=sunrise_jd,
        next_sunrise_jd=next_sunrise_jd,
        tz_name=tz_name,
    )
    agni = calculate_agni_vaas(get_tithi_at_jd(sunrise_jd, _AYANAMSA), vara)
    return MuhuratDay(
        rahu_kaal=_window(calculate_rahu_kaal(sunrise_jd, sunset_jd, vara)),
        yamaganda=_window(calculate_yamaganda(sunrise_jd, sunset_jd, vara)),
        gulika=_window(calculate_gulika(sunrise_jd, sunset_jd, vara)),
        abhijit=_window(calculate_abhijit(sunrise_jd, sunset_jd)),
        panchak=_panchak(calculate_panchak_kaal(sunrise_jd, next_sunrise_jd, _AYANAMSA)),
        bhadra=tuple(
            BhadraWindow(
                start_jd=w["start_jd"],
                end_jd=w["end_jd"],
                moon_rashi=RASHI_NAMES.index(w["moon_rashi"]),
                residence=w["residence"],
            )
            for w in calculate_bhadra_kaal(sunrise_jd, next_sunrise_jd, _AYANAMSA)
        ),
        gandmool=tuple(
            GandmoolWindow(start_jd=y["start_jd"], end_jd=y["end_jd"], nakshatra=y["nakshatra"])
            for y in found["special_yogas"]
            if y["name"] == "Gandmool Nakshatra"
        ),
        chandra_bal=_chandra_bal(sunrise_jd, next_sunrise_jd),
        agni_vaas=AgniVaas(residence=agni["residence"], is_auspicious=agni["is_auspicious"]),
        yogas=(
            *(_yoga("dainika", y) for y in found["yogas"]),
            *(_yoga("aanandadi", y) for y in found["aanandadi_yogas"]),
            *(_yoga("ravi", y) for y in found["ravi_yogas"]),
            *(_yoga("jwalamukhi", y) for y in found["special_yogas"] if y["name"] == "Jwalamukhi"),
        ),
    )


def _window(raw: dict[str, float]) -> Window:
    return Window(start_jd=raw["start_jd"], end_jd=raw["end_jd"])


def _period(raw: dict | None) -> Window | None:
    return Window(start_jd=raw["entry_jd"], end_jd=raw["exit_jd"]) if raw else None


def _panchak(raw: dict) -> PanchakReading:
    window = _window(raw["windows"][0]) if raw["windows"] else None
    return PanchakReading(
        window=window, period=_period(raw["period"]), next_period=_period(raw["next_period"])
    )


def _chandra_bal(sunrise_jd: float, next_sunrise_jd: float) -> tuple[ChandraBalSpan, ...]:
    first, entered, entry_jd = find_moon_rashi_change(sunrise_jd, next_sunrise_jd, _AYANAMSA)
    if entered is None:
        return (ChandraBalSpan(moon_rashi=first, ends_jd=None, rashis=chandra_bal_rashis(first)),)
    return (
        ChandraBalSpan(moon_rashi=first, ends_jd=entry_jd, rashis=chandra_bal_rashis(first)),
        ChandraBalSpan(moon_rashi=entered, ends_jd=None, rashis=chandra_bal_rashis(entered)),
    )


def _yoga(kind: str, raw: dict) -> DayYoga:
    has_varjya = raw.get("varjya_start_jd") is not None
    return DayYoga(
        kind=kind,
        name=raw["name"],
        nature=raw["nature"],
        start_jd=raw["start_jd"],
        end_jd=raw["end_jd"],
        is_nullified=raw.get("is_nullified", False),
        cancelled=raw.get("cancelled", False),
        diminished=raw.get("diminished", False),
        varjya=(
            Window(start_jd=raw["varjya_start_jd"], end_jd=raw["varjya_end_jd"])
            if has_varjya
            else None
        ),
    )
