"""yoga_service.py — Public API for all yoga/muhurta detection.

Single entry point: detect_all_yogas_for_day().

Returns a dict with three categories of yogas (backward-compatible with
the prior three-service API):
  yogas                    — Dainika (vara-based)
  aanandadi_yogas          — Aanandadi (planet-nakshatra based)
  special_yogas            — Special (Moon-position based, no vara)

Each yoga entry includes formatted time strings (HH:MM, ISO) for display.
"""

from __future__ import annotations

from datetime import date as date_type

from astronomy import jd_to_zoned_datetime, get_planetary_longitude
from panchang import get_vara_from_date, calculate_bhadra_kaal, calculate_panchak_kaal
from panchang_service import _collect_all_tithis_in_day, collect_all_nakshatras_in_day

from yoga_engine import (
    match_aanandadi, match_dainika, apply_dainika_overrides, compute_recommendation,
    varjya_minutes,
)
from yoga_rules import AANANDADI_YOGAS, DAINIKA_RULES

# Nakshatra names (1-indexed via [idx - 1])
_NAK_NAMES: tuple[str, ...] = (
    "Ashvini", "Bharani", "Kritika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati", "Abhijit",
)

# Gandmool nakshatras (Moon at a rashi junction)
_GANDMOOL_NAKSHATRAS: frozenset[int] = frozenset({1, 9, 10, 18, 19, 27})
_GANDMOOL_NAK_NAMES: dict[int, str] = {
    1: "Ashvini", 9: "Ashlesha", 10: "Magha",
    18: "Jyeshtha", 19: "Mula", 27: "Revati",
}

# Tithi names (Shukla 1–15); index 0 = Pratipada
_TITHI_NAMES: tuple[str, ...] = (
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
)

# Jwalamukhi (tithi, nakshatra) pairs — no vara constraint
_JWALAMUKHI_PAIRS: frozenset[tuple[int, int]] = frozenset({
    (1, 19),   # Pratipada  + Moola
    (5, 2),    # Panchami   + Bharani
    (8, 3),    # Ashtami    + Kritika
    (9, 4),    # Navami     + Rohini
    (10, 9),   # Dashami    + Ashlesha
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_all_yogas_for_day(
    *,
    date_obj: date_type,
    sunrise_jd: float,
    next_sunrise_jd: float,
    tz_name: str,
    ayanamsa: str = "Lahiri",
) -> dict:
    """Detect all yogas active during the solar day (sunrise → next sunrise).

    Returns:
        {
            "vara": int,             # 0=Sunday … 6=Saturday
            "tithi": int,            # 1–30 at sunrise
            "nakshatra": int,        # 1–28 at sunrise
            "yogas": [...],          # Dainika matches with time strings
            "recommendation": str,
            "aanandadi_yogas": [...], # Aanandadi matches with time strings
            "aanandadi_recommendation": str,
            "special_yogas": [...],   # Special matches with time strings
        }
    """
    vara = get_vara_from_date(date_obj)

    tithi_segments, nakshatra_segments = _get_segments(
        sunrise_jd, next_sunrise_jd, ayanamsa, tz_name
    )

    sunrise_tithi = tithi_segments[0]["index"]
    sunrise_nakshatra = nakshatra_segments[0]["index"]

    # ── Dainika (vara-based) ─────────────────────────────────────────────
    raw_dainika = match_dainika(DAINIKA_RULES, vara, tithi_segments, nakshatra_segments)
    dainika_with_overrides = apply_dainika_overrides(raw_dainika)
    dainika_with_dosha_bhanga = _apply_dainika_dosha_bhanga(dainika_with_overrides)
    dainika_formatted = [_fmt_dainika(m, tz_name) for m in dainika_with_dosha_bhanga]
    dainika_rec = compute_recommendation(dainika_with_overrides)

    # ── Aanandadi (Vara + Moon nakshatra formula) ────────────────────────
    moon_segs = _moon_segments(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name)
    raw_aanandadi = match_aanandadi(AANANDADI_YOGAS, vara, moon_segs)
    aanandadi_formatted = [_fmt_aanandadi(m, tz_name) for m in raw_aanandadi]
    aanandadi_with_nullification = _apply_supreme_nullification(dainika_formatted, aanandadi_formatted)
    aanandadi_rec = compute_recommendation(raw_aanandadi)

    # ── Ravi Yoga (Sun + Moon nakshatra distance formula) ────────────────
    ravi_yogas = _detect_ravi_yoga(sunrise_jd, moon_segs, ayanamsa, tz_name, dainika_formatted, vara)

    # ── Special (Moon-position based) ────────────────────────────────────
    special = _detect_special(
        tithi_segments, nakshatra_segments,
        sunrise_jd, next_sunrise_jd, ayanamsa, tz_name,
    )

    return {
        "vara": vara,
        "tithi": sunrise_tithi,
        "nakshatra": sunrise_nakshatra,
        "yogas": dainika_formatted,
        "recommendation": dainika_rec,
        "aanandadi_yogas": aanandadi_with_nullification,
        "aanandadi_recommendation": aanandadi_rec,
        "ravi_yogas": ravi_yogas,
        "special_yogas": special,
    }


# ---------------------------------------------------------------------------
# Segment helpers
# ---------------------------------------------------------------------------

def _get_segments(
    sunrise_jd: float,
    next_sunrise_jd: float,
    ayanamsa: str,
    tz_name: str,
) -> tuple[list[dict], list[dict]]:
    tithi_list = _collect_all_tithis_in_day(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name)
    nak_list = collect_all_nakshatras_in_day(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name)

    def to_segments(entries: list[dict]) -> list[dict]:
        segs: list[dict] = []
        cursor = sunrise_jd
        for entry in entries:
            end_jd = entry["ends"]["jd"] if entry["ends"] else next_sunrise_jd
            segs.append({
                "index": entry["index"],
                "start_jd": cursor,
                "end_jd": min(end_jd, next_sunrise_jd),
            })
            cursor = end_jd
        if segs:
            segs[-1]["end_jd"] = next_sunrise_jd
        return segs

    return to_segments(tithi_list), to_segments(nak_list)


def _moon_segments(
    sunrise_jd: float,
    next_sunrise_jd: float,
    ayanamsa: str,
    tz_name: str,
) -> list[dict]:
    raw = collect_all_nakshatras_in_day(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name)
    segs: list[dict] = []
    cursor = sunrise_jd
    for entry in raw:
        end_jd = next_sunrise_jd if entry.get("continues_past_next_sunrise") else entry["ends"]["jd"]
        segs.append({"index": entry["index"], "start_jd": cursor, "end_jd": end_jd})
        cursor = end_jd
    return segs


# ---------------------------------------------------------------------------
# Supreme-yoga nullification
# ---------------------------------------------------------------------------

_SUPREME_OVERRIDERS: frozenset[str] = frozenset({
    "Guru Pushya Amrit",
    "Ravi Pushya Amrit",
    "Sarvartha Siddhi",
    "Amrit Siddhi",
})

# Ravi Yoga: Sun-Moon nakshatra distance formula (27-nakshatra system, Abhijit excluded).
# distance = ((moon_nak - sun_nak) % 27) + 1.  Active when distance ∈ {4,6,9,10,13,20}.
# Source: Ruchika Publications, Delhi, Page 112.
_RAVI_YOGA_DISTANCES: frozenset[int] = frozenset({4, 6, 9, 10, 13, 20})
_RAVI_YOGA_MEANING = (
    "Dosha Nashak (Solar Shield) — highly auspicious Sun-Moon nakshatra yoga. "
    "Neutralizes minor negative effects and flaws (like unfavorable Tithi or Karan). "
    "Ideal for high-value purchases, business actions, and official decisions."
)


def _lon_to_27_nakshatra(lon: float) -> int:
    """Convert sidereal longitude [0, 360) to 27-nakshatra index 1–27 (Abhijit excluded)."""
    return int(lon * 27 / 360) % 27 + 1


def _detect_ravi_yoga(
    sunrise_jd: float,
    moon_segs: list[dict],
    ayanamsa: str,
    tz_name: str,
    dainika_yogas: list[dict],
    vara: int,
) -> list[dict]:
    """Detect Ravi Yoga windows for the day using the Sun-Moon nakshatra distance formula.

    The Sun stays in one nakshatra for ~13 days, so its position at sunrise is stable
    for the entire day. The Moon's segments (already computed) are iterated; each segment
    where the distance falls in _RAVI_YOGA_DISTANCES produces one yoga entry.

    Distances 9 and 10 are consecutive: when Moon crosses from the dist-9 to the dist-10
    nakshatra the windows are back-to-back with no gap. They are emitted as two separate
    entries (one per Moon nakshatra segment) — contiguous in time but not merged.

    Ravi Yoga is never nullified by supreme overriders (unlike inauspicious Dainika yogas).
    Instead, when it overlaps a supreme yoga it gets flagged `is_conflict=True` so the
    user sees the tension explicitly.
    """
    sun_lon = get_planetary_longitude(sunrise_jd, "Sun", ayanamsa)
    sun_nak = _lon_to_27_nakshatra(sun_lon)

    supreme_windows = [
        m for m in dainika_yogas
        if m["name"] in _SUPREME_OVERRIDERS and not m.get("cancelled", False)
    ]

    results: list[dict] = []
    for seg in moon_segs:
        moon_nak = seg["index"]
        if moon_nak > 27:
            continue  # Abhijit (28) — excluded from the 27-nakshatra formula
        distance = ((moon_nak - sun_nak) % 27) + 1
        if distance not in _RAVI_YOGA_DISTANCES:
            continue

        start_jd, end_jd = seg["start_jd"], seg["end_jd"]
        conflicting = [
            s["name"] for s in supreme_windows
            if start_jd < s["end_jd"] and s["start_jd"] < end_jd
        ]

        is_exception = False
        exception_name = ""
        if vara == 0:
            if moon_nak == 9:  # Ashlesha
                is_exception = True
                exception_name = "Vajra Yog"
            elif moon_nak == 10:  # Magha
                is_exception = True
                exception_name = "Mudgar Yog"

        if is_exception:
            name = f"Ravi Yoga ({exception_name})"
            nature = "ashubh"
            severity = "inauspicious"
            meaning = f"Sunday exception: {exception_name} forms, compromising the positive effects."
        else:
            name = "Ravi Yoga"
            nature = "shubh"
            severity = "auspicious"
            meaning = _RAVI_YOGA_MEANING

        st, sl = _fmt(start_jd, tz_name)
        et, el = _fmt(end_jd, tz_name)
        results.append({
            "name": name,
            "nature": nature,
            "severity": severity,
            "meaning": meaning,
            "trigger_kind": "sun_moon_nakshatra",
            "trigger_detail": (
                f"Sun in {_NAK_NAMES[sun_nak - 1]}, "
                f"Moon in {_NAK_NAMES[moon_nak - 1]} (distance: {distance})"
            ),
            "start_jd": start_jd,
            "end_jd": end_jd,
            "start_time": st,
            "start_local": sl,
            "end_time": et,
            "end_local": el,
            "is_nullified": False,
            "nullified_by": None,
            "is_conflict": bool(conflicting),
            "conflicts_with": conflicting,
            "cancelled": False,
        })
    return results


def _apply_dainika_dosha_bhanga(matches: list[dict]) -> list[dict]:
    """Mark inauspicious Dainika yogas as nullified when they time-overlap a supreme yoga.

    Uses _SUPREME_OVERRIDERS (same set as Aanandadi nullification).
    Cancelled yogas are excluded from the supreme-window pool.
    Every entry receives is_nullified (bool) and nullified_by (str | None).
    """
    supreme_windows = [
        m for m in matches
        if m["name"] in _SUPREME_OVERRIDERS and not m.get("cancelled", False)
    ]
    result: list[dict] = []
    for yoga in matches:
        if yoga["nature"] == "ashubh" and not yoga.get("cancelled", False):
            nullifier = next(
                (s for s in supreme_windows
                 if yoga["start_jd"] < s["end_jd"] and s["start_jd"] < yoga["end_jd"]),
                None,
            )
            result.append({**yoga,
                           "is_nullified": nullifier is not None,
                           "nullified_by": nullifier["name"] if nullifier else None})
        else:
            result.append({**yoga, "is_nullified": False, "nullified_by": None})
    return result


def _apply_supreme_nullification(
    dainika: list[dict],
    aanandadi: list[dict],
) -> list[dict]:
    """Mark inauspicious Aanandadi yogas as nullified when they time-overlap
    with an active supreme Dainika overrider.

    Returns a copy — originals not mutated.
    Adds is_nullified (bool) and nullified_by (str | None) to every entry.
    """
    supreme_windows = [
        m for m in dainika
        if m["name"] in _SUPREME_OVERRIDERS and not m.get("cancelled", False)
    ]

    result: list[dict] = []
    for yoga in aanandadi:
        if yoga["nature"] == "ashubh":
            nullifier = next(
                (s for s in supreme_windows
                 if yoga["start_jd"] < s["end_jd"] and s["start_jd"] < yoga["end_jd"]),
                None,
            )
            result.append({**yoga, "is_nullified": nullifier is not None,
                            "nullified_by": nullifier["name"] if nullifier else None})
        else:
            result.append({**yoga, "is_nullified": False, "nullified_by": None})

    return result


# ---------------------------------------------------------------------------
# Time formatting helpers
# ---------------------------------------------------------------------------

def _fmt(jd: float, tz_name: str) -> tuple[str, str]:
    """Return (HH:MM, ISO) for a JD. Returns ('', '') on failure."""
    dt = jd_to_zoned_datetime(jd, tz_name)
    if dt is None:
        return "", ""
    return dt.strftime("%H:%M"), dt.isoformat(timespec="seconds")


def _fmt_dainika(match: dict, tz_name: str) -> dict:
    st, sl = _fmt(match["start_jd"], tz_name)
    et, el = _fmt(match["end_jd"], tz_name)
    return {**match, "start_time": st, "start_local": sl, "end_time": et, "end_local": el}


def _fmt_aanandadi(match: dict, tz_name: str) -> dict:
    st, sl = _fmt(match["start_jd"], tz_name)
    et, el = _fmt(match["end_jd"], tz_name)
    # trigger_nakshatra_index uses standard 1-27 (or 28=Abhijit) — same offset for name lookup
    nak_name = _NAK_NAMES[match["trigger_nakshatra_index"] - 1]

    v_start_time: str | None = None
    v_end_time: str | None = None
    if match["varjya_start_jd"] is not None:
        v_start_time, _ = _fmt(match["varjya_start_jd"], tz_name)
    if match["varjya_end_jd"] is not None:
        v_end_time, _ = _fmt(match["varjya_end_jd"], tz_name)

    return {
        **match,
        "trigger_nakshatra": nak_name,
        "triggering_planet": "Moon",
        "start_time": st,
        "start_local": sl,
        "end_time": et,
        "end_local": el,
        "varjya_start_time": v_start_time,
        "varjya_end_time": v_end_time,
    }


# ---------------------------------------------------------------------------
# Special yoga detection (Moon-position based, no vara constraint)
# ---------------------------------------------------------------------------

_GANDMOOL_MEANING = (
    "Junction nakshatra — inauspicious for births and new beginnings. "
    "Purification rites advised."
)
_PANCHAK_MEANING = (
    "Last 5 nakshatras — avoid funeral rites, travel south, collecting wood, "
    "construction, and marriage."
)
_BHADRA_MEANING = (
    "Vishti Karana — inauspicious half-tithi period. "
    "Avoid all new undertakings, travel, and auspicious ceremonies."
)
_JWALAMUKHI_MEANING = (
    "Volcano — any work started here faces major obstacles and goes to waste. "
    "Avoid all auspicious muhurtas, marriages, construction, and agriculture. "
    "Exception: auspicious only for defeating enemies or hostile acts."
)


def _detect_special(
    tithi_segments: list[dict],
    nakshatra_segments: list[dict],
    sunrise_jd: float,
    next_sunrise_jd: float,
    ayanamsa: str,
    tz_name: str,
) -> list[dict]:
    results: list[dict] = []
    results.extend(_gandmool(nakshatra_segments, sunrise_jd, next_sunrise_jd, tz_name))
    results.extend(_panchak(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name))
    results.extend(_bhadra(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name))
    results.extend(_jwalamukhi(tithi_segments, nakshatra_segments, tz_name))
    return results


def _gandmool(
    nak_segments: list[dict],
    sunrise_jd: float,
    next_sunrise_jd: float,
    tz_name: str,
) -> list[dict]:
    gandmool_segs = [s for s in nak_segments if s["index"] in _GANDMOOL_NAKSHATRAS]
    if not gandmool_segs:
        return []

    # Each Gandmool nakshatra gets its own separate entry.
    # Adjacent Gandmool nakshatras (Gandanta junctions) must NOT be merged —
    # the transition moment between them (e.g. Ashlesha→Magha at the Cancer/Leo cusp)
    # is itself an astrologically significant Gandanta point.
    windows: list[tuple[float, float, list[int]]] = [
        (seg["start_jd"], seg["end_jd"], [seg["index"]]) for seg in gandmool_segs
    ]

    results: list[dict] = []
    for w_start, w_end, nak_indices in windows:
        st, sl = _fmt(w_start, tz_name)
        et, el = _fmt(w_end, tz_name)
        naks = ", ".join(_GANDMOOL_NAK_NAMES[i] for i in nak_indices if i in _GANDMOOL_NAK_NAMES)
        results.append({
            "name": "Gandmool Nakshatra",
            "nature": "ashubh",
            "severity": "inauspicious",
            "meaning": _GANDMOOL_MEANING,
            "start_time": st,
            "end_time": et,
            "start_local": sl,
            "end_local": el,
            "start_jd": w_start,
            "end_jd": w_end,
            "clipped_start": w_start == sunrise_jd,
            "clipped_end": w_end == next_sunrise_jd,
            "trigger_detail": f"Moon in {naks}",
        })
    return results


def _panchak(
    sunrise_jd: float,
    next_sunrise_jd: float,
    ayanamsa: str,
    tz_name: str,
) -> list[dict]:
    panchak = calculate_panchak_kaal(sunrise_jd, next_sunrise_jd, ayanamsa)
    results: list[dict] = []
    for pw in panchak.get("windows", []):
        st, sl = _fmt(pw["start_jd"], tz_name)
        et, el = _fmt(pw["end_jd"], tz_name)
        results.append({
            "name": "Panchak",
            "nature": "ashubh",
            "severity": "inauspicious",
            "meaning": _PANCHAK_MEANING,
            "start_time": st,
            "end_time": et,
            "start_local": sl,
            "end_local": el,
            "start_jd": pw["start_jd"],
            "end_jd": pw["end_jd"],
            "clipped_start": pw.get("clipped_start", False),
            "clipped_end": pw.get("clipped_end", False),
            "trigger_detail": f"Moon in {pw.get('nakshatra', 'Panchak zone')}",
        })
    return results


def _bhadra(
    sunrise_jd: float,
    next_sunrise_jd: float,
    ayanamsa: str,
    tz_name: str,
) -> list[dict]:
    results: list[dict] = []
    for w in calculate_bhadra_kaal(sunrise_jd, next_sunrise_jd, ayanamsa):
        st, sl = _fmt(w["start_jd"], tz_name)
        et, el = _fmt(w["end_jd"], tz_name)
        results.append({
            "name": "Bhadra (Vishti)",
            "nature": "ashubh",
            "severity": "inauspicious",
            "meaning": _BHADRA_MEANING,
            "start_time": st,
            "end_time": et,
            "start_local": sl,
            "end_local": el,
            "start_jd": w["start_jd"],
            "end_jd": w["end_jd"],
            "clipped_start": w.get("clipped_start", False),
            "clipped_end": w.get("clipped_end", False),
            "trigger_detail": (
                f"Vishti Karana — Moon in {w.get('residence', '')} rashi "
                f"(risk: {w.get('risk_level', '')})"
            ),
        })
    return results


def _jwalamukhi(
    tithi_segments: list[dict],
    nak_segments: list[dict],
    tz_name: str,
) -> list[dict]:
    results: list[dict] = []
    for t_seg in tithi_segments:
        for n_seg in nak_segments:
            if (t_seg["index"], n_seg["index"]) not in _JWALAMUKHI_PAIRS:
                continue
            start_jd = max(t_seg["start_jd"], n_seg["start_jd"])
            end_jd = min(t_seg["end_jd"], n_seg["end_jd"])
            if end_jd <= start_jd:
                continue
            st, sl = _fmt(start_jd, tz_name)
            et, el = _fmt(end_jd, tz_name)
            t_idx, n_idx = t_seg["index"], n_seg["index"]
            tithi_name = _TITHI_NAMES[t_idx - 1] if 1 <= t_idx <= 15 else f"Tithi {t_idx}"
            nak_name = _NAK_NAMES[n_idx - 1]
            results.append({
                "name": "Jwalamukhi",
                "nature": "ashubh",
                "severity": "inauspicious",
                "meaning": _JWALAMUKHI_MEANING,
                "start_time": st,
                "end_time": et,
                "start_local": sl,
                "end_local": el,
                "start_jd": start_jd,
                "end_jd": end_jd,
                "clipped_start": False,
                "clipped_end": False,
                "trigger_detail": f"{tithi_name} + {nak_name}",
            })
    return results
