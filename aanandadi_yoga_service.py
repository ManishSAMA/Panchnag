"""
Aanandadi Yoga Service — 28 Aanandadi Yogas (आनन्दादि योग)

Source: Aanandadi Yoga Bodhak Koshthaк, Ruchika Publications, Delhi, p.110

Each yoga fires when ANY of the 7 Jyotish planets occupies its designated
nakshatra. Unlike the 31 Vara-Tithi-Nakshatra system, these yogas are triggered
purely by planet positions, not weekday or lunar phase.

Abhijit (28th nakshatra) occupies ~276°40'–280°53'20" sidereal; get_nakshatra()
only returns 1-27, so _lon_to_nakshatra() adds the Abhijit check.

Varjya duration is stored as (ghati, pala) tuples:
  1 ghati = 24 minutes, 1 pala = 24 seconds (= 24/60 = 0.4 minutes)
  total_minutes = ghati * 24 + pala * 0.4
Using pala (not minutes) for the second element avoids the collision
between (0, 48) = 19.2 min and (2, 0) = 48 min.
"""

from __future__ import annotations

from astronomy import get_planetary_longitude, jd_to_zoned_datetime
from panchang import get_nakshatra
from panchang_service import collect_all_nakshatras_in_day


# ---------------------------------------------------------------------------
# Abhijit constants (sidereal degrees)
# ---------------------------------------------------------------------------

_ABHIJIT_START: float = 276 + 40 / 60               # 276.6667°
_ABHIJIT_END: float   = 280 + 53 / 60 + 20 / 3600   # 280.8889°

# ---------------------------------------------------------------------------
# Nakshatra name list — 28 entries (1-indexed via [idx - 1])
# ---------------------------------------------------------------------------

_NAK_NAMES: tuple[str, ...] = (
    "Ashvini", "Bharani", "Kritika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati", "Abhijit",
)

_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

# ---------------------------------------------------------------------------
# 28 Aanandadi Yoga rules
# ---------------------------------------------------------------------------

AANANDADI_RULES: list[dict] = [
    {
        "name": "Aanand", "nature": "shubh", "severe": False,
        "severity": "highly_auspicious", "fal": "Siddhi", "varjya": None,
        "meaning": "Joy and accomplishment; brings success and positive outcomes in all endeavors.",
        "planet_map": {"Sun": 1, "Moon": 5, "Mars": 9, "Mercury": 13, "Jupiter": 17, "Venus": 21, "Saturn": 24},
    },
    {
        "name": "Kaladand", "nature": "ashubh", "severe": True,
        "severity": "highly_inauspicious", "fal": "Haani", "varjya": "full_day",
        "meaning": "Staff of Time; entire period is forbidden — signifies severe loss and destruction.",
        "planet_map": {"Sun": 2, "Moon": 6, "Mars": 10, "Mercury": 14, "Jupiter": 18, "Venus": 28, "Saturn": 25},
    },
    {
        "name": "Dhumraksh", "nature": "ashubh", "severe": False,
        "severity": "highly_inauspicious", "fal": "Dukh", "varjya": (0, 24),
        "meaning": "Smoky-eyed; brings sorrow and suffering; avoid commencement during varjya.",
        "planet_map": {"Sun": 3, "Moon": 7, "Mars": 11, "Mercury": 15, "Jupiter": 19, "Venus": 22, "Saturn": 26},
    },
    {
        "name": "Prajapati", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Laabh", "varjya": None,
        "meaning": "Lord of Creatures; favorable for new ventures; brings gain and prosperity.",
        "planet_map": {"Sun": 4, "Moon": 8, "Mars": 12, "Mercury": 16, "Jupiter": 20, "Venus": 23, "Saturn": 27},
    },
    {
        "name": "Saumya", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Shubh", "varjya": None,
        "meaning": "Gentle and benefic; bestows general well-being and auspiciousness.",
        "planet_map": {"Sun": 5, "Moon": 9, "Mars": 13, "Mercury": 17, "Jupiter": 21, "Venus": 24, "Saturn": 1},
    },
    {
        "name": "Dhwanksh", "nature": "ashubh", "severe": False,
        "severity": "inauspicious", "fal": "Kshati", "varjya": (2, 0),
        "meaning": "Crow; ominous sign indicating loss and injury; avoid the varjya period.",
        "planet_map": {"Sun": 6, "Moon": 10, "Mars": 14, "Mercury": 18, "Jupiter": 28, "Venus": 25, "Saturn": 2},
    },
    {
        "name": "Dhwaj", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Shubh", "varjya": None,
        "meaning": "Flag of victory; auspicious for undertakings; brings success and recognition.",
        "planet_map": {"Sun": 7, "Moon": 11, "Mars": 15, "Mercury": 19, "Jupiter": 22, "Venus": 26, "Saturn": 3},
    },
    {
        "name": "Shrivatsa", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Sukh", "varjya": None,
        "meaning": "Auspicious mark of Vishnu; brings happiness, comfort, and domestic harmony.",
        "planet_map": {"Sun": 8, "Moon": 12, "Mars": 16, "Mercury": 20, "Jupiter": 23, "Venus": 27, "Saturn": 4},
    },
    {
        "name": "Vajra", "nature": "ashubh", "severe": False,
        "severity": "inauspicious", "fal": "Kshati", "varjya": (2, 0),
        "meaning": "Thunderbolt; harsh destructive energy; avoid important starts during varjya.",
        "planet_map": {"Sun": 9, "Moon": 13, "Mars": 17, "Mercury": 21, "Jupiter": 24, "Venus": 1, "Saturn": 5},
    },
    {
        "name": "Mudgar", "nature": "ashubh", "severe": False,
        "severity": "inauspicious", "fal": "Haani", "varjya": (2, 0),
        "meaning": "Mace of suffering; brings hardship and harm; indicates a difficult period.",
        "planet_map": {"Sun": 10, "Moon": 14, "Mars": 18, "Mercury": 28, "Jupiter": 25, "Venus": 2, "Saturn": 6},
    },
    {
        "name": "Chatra", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Samman", "varjya": None,
        "meaning": "Royal umbrella; brings honor, respect, and protection; good for official matters.",
        "planet_map": {"Sun": 11, "Moon": 15, "Mars": 19, "Mercury": 22, "Jupiter": 26, "Venus": 3, "Saturn": 7},
    },
    {
        "name": "Mitra", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Laabh", "varjya": None,
        "meaning": "Friend; brings beneficial relationships, profit, and cooperative success.",
        "planet_map": {"Sun": 12, "Moon": 16, "Mars": 20, "Mercury": 23, "Jupiter": 27, "Venus": 4, "Saturn": 8},
    },
    {
        "name": "Manas", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Shubh", "varjya": None,
        "meaning": "Mind; bestows clarity, wisdom, and mental well-being; auspicious for study.",
        "planet_map": {"Sun": 13, "Moon": 17, "Mars": 21, "Mercury": 24, "Jupiter": 1, "Venus": 5, "Saturn": 9},
    },
    {
        "name": "Padmaksh", "nature": "ashubh", "severe": False,
        "severity": "highly_inauspicious", "fal": "Dhannash", "varjya": (1, 36),
        "meaning": "Lotus-eyed destroyer; indicates serious financial loss and destruction of wealth.",
        "planet_map": {"Sun": 14, "Moon": 18, "Mars": 28, "Mercury": 25, "Jupiter": 2, "Venus": 6, "Saturn": 10},
    },
    {
        "name": "Lumbak", "nature": "ashubh", "severe": False,
        "severity": "highly_inauspicious", "fal": "Kshay", "varjya": (1, 36),
        "meaning": "Decay and decline; causes diminishment of resources and lasting deterioration.",
        "planet_map": {"Sun": 15, "Moon": 19, "Mars": 22, "Mercury": 26, "Jupiter": 3, "Venus": 7, "Saturn": 11},
    },
    {
        "name": "Utpat", "nature": "ashubh", "severe": True,
        "severity": "highly_inauspicious", "fal": "Kasht", "varjya": "full_day",
        "meaning": "Calamity; entire period forbidden — portends trouble, upheaval, and hardship.",
        "planet_map": {"Sun": 16, "Moon": 20, "Mars": 23, "Mercury": 27, "Jupiter": 4, "Venus": 8, "Saturn": 12},
    },
    {
        "name": "Mrityu", "nature": "ashubh", "severe": True,
        "severity": "highly_inauspicious", "fal": "Maran", "varjya": "full_day",
        "meaning": "Death; entire period strictly forbidden — the most inauspicious yoga; avoid all auspicious work.",
        "planet_map": {"Sun": 17, "Moon": 21, "Mars": 24, "Mercury": 1, "Jupiter": 5, "Venus": 9, "Saturn": 13},
    },
    {
        "name": "Kaan", "nature": "ashubh", "severe": False,
        "severity": "inauspicious", "fal": "Kasht", "varjya": (0, 48),
        "meaning": "Ear; brings difficulty and trouble; avoid undertakings during the varjya window.",
        "planet_map": {"Sun": 18, "Moon": 28, "Mars": 25, "Mercury": 2, "Jupiter": 6, "Venus": 10, "Saturn": 14},
    },
    {
        "name": "Siddhi", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Siddhi", "varjya": None,
        "meaning": "Achievement; ensures accomplishment of goals; excellent for starting important work.",
        "planet_map": {"Sun": 19, "Moon": 22, "Mars": 26, "Mercury": 3, "Jupiter": 7, "Venus": 11, "Saturn": 15},
    },
    {
        "name": "Shubh", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Shubh", "varjya": None,
        "meaning": "Auspicious; bestows general good fortune and positive outcomes.",
        "planet_map": {"Sun": 20, "Moon": 23, "Mars": 27, "Mercury": 4, "Jupiter": 8, "Venus": 12, "Saturn": 16},
    },
    {
        "name": "Amrit", "nature": "shubh", "severe": False,
        "severity": "highly_auspicious", "fal": "Bhog", "varjya": None,
        "meaning": "Nectar of immortality; highly auspicious; brings joy, abundance, and excellent results.",
        "planet_map": {"Sun": 21, "Moon": 24, "Mars": 1, "Mercury": 5, "Jupiter": 9, "Venus": 13, "Saturn": 17},
    },
    {
        "name": "Musal", "nature": "ashubh", "severe": False,
        "severity": "inauspicious", "fal": "Kshati", "varjya": (0, 48),
        "meaning": "Pestle; causes damage and loss; inauspicious for new ventures.",
        "planet_map": {"Sun": 28, "Moon": 25, "Mars": 2, "Mercury": 6, "Jupiter": 10, "Venus": 14, "Saturn": 18},
    },
    {
        "name": "Gad", "nature": "ashubh", "severe": False,
        "severity": "highly_inauspicious", "fal": "Rog", "varjya": (2, 48),
        "meaning": "Club; brings disease and ill health; particularly inauspicious for health-related matters.",
        "planet_map": {"Sun": 22, "Moon": 26, "Mars": 3, "Mercury": 7, "Jupiter": 11, "Venus": 15, "Saturn": 19},
    },
    {
        "name": "Matang", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Vriddhi", "varjya": None,
        "meaning": "Elephant; brings growth, abundance, and increase; auspicious for wealth and expansion.",
        "planet_map": {"Sun": 23, "Moon": 27, "Mars": 4, "Mercury": 8, "Jupiter": 12, "Venus": 16, "Saturn": 20},
    },
    {
        "name": "Rakshas", "nature": "ashubh", "severe": True,
        "severity": "highly_inauspicious", "fal": "Kasht", "varjya": "full_day",
        "meaning": "Demon; entire period strictly forbidden — brings great suffering and inauspiciousness.",
        "planet_map": {"Sun": 24, "Moon": 1, "Mars": 5, "Mercury": 9, "Jupiter": 13, "Venus": 17, "Saturn": 21},
    },
    {
        "name": "Char", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Laabh", "varjya": None,
        "meaning": "Movement; brings profitable motion and change; auspicious for travel and transitions.",
        "planet_map": {"Sun": 25, "Moon": 2, "Mars": 6, "Mercury": 10, "Jupiter": 14, "Venus": 18, "Saturn": 28},
    },
    {
        "name": "Sthir", "nature": "shubh", "severe": False,
        "severity": "auspicious", "fal": "Sukh", "varjya": None,
        "meaning": "Stability; brings lasting happiness and enduring results; excellent for permanent matters.",
        "planet_map": {"Sun": 26, "Moon": 3, "Mars": 7, "Mercury": 11, "Jupiter": 15, "Venus": 19, "Saturn": 22},
    },
    {
        "name": "Vardhamaan", "nature": "shubh", "severe": False,
        "severity": "highly_auspicious", "fal": "Vriddhi", "varjya": None,
        "meaning": "Ever-increasing; the most auspicious of Aanandadi yogas; brings great growth and prosperity.",
        "planet_map": {"Sun": 27, "Moon": 4, "Mars": 8, "Mercury": 12, "Jupiter": 16, "Venus": 20, "Saturn": 23},
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lon_to_nakshatra(lon: float) -> int:
    """Return nakshatra index 1-27, or 28 for Abhijit.

    Abhijit occupies ~276°40' – ~280°53'20" sidereal. get_nakshatra() returns
    only 1-27, so check the Abhijit range first.
    """
    normalized = lon % 360.0
    if _ABHIJIT_START <= normalized < _ABHIJIT_END:
        return 28
    return get_nakshatra(normalized)


def _varjya_total_minutes(spec: tuple[int, int]) -> float:
    """Return forbidden window length in minutes from a (ghati, pala) tuple."""
    ghati, pala = spec
    return ghati * 24.0 + pala * (24.0 / 60.0)


def _build_varjya(
    spec: None | str | tuple[int, int],
    yoga_start_jd: float,
    start_dt,
    tz_name: str,
) -> dict:
    """Return varjya timing fields from the rule's varjya spec."""
    if spec is None:
        return {"varjya_minutes": None, "varjya_start_time": None, "varjya_end_time": None}

    if spec == "full_day":
        return {"varjya_minutes": "full_day", "varjya_start_time": None, "varjya_end_time": None}

    dur_min = _varjya_total_minutes(spec)
    end_dt = jd_to_zoned_datetime(yoga_start_jd + dur_min / 1440.0, tz_name)
    return {
        "varjya_minutes":    dur_min,
        "varjya_start_time": start_dt.strftime("%H:%M") if start_dt else "",
        "varjya_end_time":   end_dt.strftime("%H:%M")   if end_dt else "",
    }


def _compute_rec(yogas: list[dict]) -> str:
    """Derive day recommendation from the list of active Aanandadi yogas."""
    if not yogas:
        return "neutral"
    if any(y["severe"] for y in yogas):
        return "avoid"
    ashubh = [y for y in yogas if y["nature"] == "ashubh"]
    shubh  = [y for y in yogas if y["nature"] == "shubh"]
    if shubh and not ashubh:
        ha = [y for y in shubh if y["severity"] == "highly_auspicious"]
        return "highly_auspicious" if ha else "auspicious"
    return "caution"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_planet_nakshatras(jd: float, ayanamsa: str) -> dict[str, int]:
    """Return the nakshatra index (1–28) for each of the 7 Jyotish planets at jd."""
    return {
        p: _lon_to_nakshatra(get_planetary_longitude(jd, p, ayanamsa))
        for p in _PLANETS
    }


def detect_aanandadi_yogas_for_day(
    *,
    sunrise_jd: float,
    next_sunrise_jd: float,
    tz_name: str,
    ayanamsa: str = "Lahiri",
) -> dict:
    """Return all Aanandadi yogas active on the day defined by sunrise_jd.

    Each of the 7 planets always occupies exactly one of 28 yoga nakshatras,
    so the result always contains exactly 7 entries (one per planet).

    Moon entries use precise nakshatra-segment timing from collect_all_nakshatras_in_day.
    Slow planet entries span the full day (sunrise → next sunrise).
    """
    planet_naks = get_planet_nakshatras(sunrise_jd, ayanamsa)

    moon_segs = collect_all_nakshatras_in_day(
        sunrise_jd, next_sunrise_jd, ayanamsa, tz_name
    )
    # Augment Moon segments with start_jd / end_jd
    aug_moon: list[dict] = []
    seg_start = sunrise_jd
    for seg in moon_segs:
        seg_end = next_sunrise_jd if seg["continues_past_next_sunrise"] else seg["ends"]["jd"]
        aug_moon.append({**seg, "start_jd": seg_start, "end_jd": seg_end})
        seg_start = seg_end

    # Build nakshatra-index → Moon segment map for fast lookup
    moon_seg_by_nak: dict[int, list[dict]] = {}
    for seg in aug_moon:
        moon_seg_by_nak.setdefault(seg["index"], []).append(seg)

    active: list[dict] = []
    for rule in AANANDADI_RULES:
        for planet in _PLANETS:
            expected_nak = rule["planet_map"][planet]
            if planet_naks[planet] != expected_nak:
                continue

            if planet == "Moon":
                matching = moon_seg_by_nak.get(expected_nak, [])
                if not matching:
                    continue
                start_jd = matching[0]["start_jd"]
                end_jd   = matching[-1]["end_jd"]
            else:
                start_jd = sunrise_jd
                end_jd   = next_sunrise_jd

            start_dt = jd_to_zoned_datetime(start_jd, tz_name)
            end_dt   = jd_to_zoned_datetime(end_jd,   tz_name)
            varjya   = _build_varjya(rule["varjya"], start_jd, start_dt, tz_name)

            active.append({
                "name":                    rule["name"],
                "nature":                  rule["nature"],
                "severity":                rule["severity"],
                "fal":                     rule["fal"],
                "meaning":                 rule["meaning"],
                "severe":                  rule["severe"],
                "triggering_planet":       planet,
                "trigger_nakshatra":       _NAK_NAMES[expected_nak - 1],
                "trigger_nakshatra_index": expected_nak,
                "start_time":  start_dt.strftime("%H:%M") if start_dt else "",
                "end_time":    end_dt.strftime("%H:%M")   if end_dt else "",
                "start_local": start_dt.isoformat(timespec="seconds") if start_dt else "",
                "end_local":   end_dt.isoformat(timespec="seconds")   if end_dt else "",
                **varjya,
            })

    return {
        "aanandadi_yogas":          active,
        "aanandadi_recommendation": _compute_rec(active),
    }
