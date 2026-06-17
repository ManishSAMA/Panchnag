"""yoga_engine.py — Pure matching functions for all yoga systems.

No ephemeris, no I/O, no side effects.
All functions take plain Python values and return plain Python values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Shared types (dicts with known keys — no TypedDict imports needed at runtime)
# Segment = {"index": int, "start_jd": float, "end_jd": float}
# YogaMatch = {"name": ..., "start_jd": float, "end_jd": float, ...}
# ---------------------------------------------------------------------------

_PLANETS: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Abhijit sidereal bounds — used by consumers, exposed for convenience
ABHIJIT_START: float = 276 + 40 / 60
ABHIJIT_END: float = 280 + 53 / 60 + 20 / 3600


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def overlap(a: dict, b: dict) -> tuple[float, float] | None:
    """Return the (start_jd, end_jd) intersection of two segments, or None.

    Returns None when the intersection is zero-length (touching edges).
    """
    start = max(a["start_jd"], b["start_jd"])
    end = min(a["end_jd"], b["end_jd"])
    return (start, end) if end > start else None


def varjya_minutes(spec: tuple[int, int]) -> float:
    """Convert a (ghati, pala) varjya spec to total minutes.

    1 ghati = 24 minutes, 1 pala = 24 seconds = 24/60 minutes.
    """
    ghati, pala = spec
    return ghati * 24.0 + pala * (24.0 / 60.0)


# ---------------------------------------------------------------------------
# Aanandadi matching
# ---------------------------------------------------------------------------

def match_aanandadi(
    rules: list[dict],
    planet_nakshatras: dict[str, int],
    moon_segments: list[dict],
    day_window: tuple[float, float],
    planet_windows: dict[str, tuple[float, float]] | None = None,
) -> list[dict]:
    """Return one YogaMatch per planet-yoga pairing active on this day.

    Each of the 7 planets is always in exactly one nakshatra, so this
    always returns exactly 7 matches (one per planet).

    Slow planets (non-Moon) use planet_windows when provided, otherwise
    fall back to day_window (sunrise → next sunrise).
    Moon uses moon_segments for precise intra-day timing.
    """
    sunrise_jd, next_sunrise_jd = day_window
    moon_seg_by_nak: dict[int, list[dict]] = {}
    for s in moon_segments:
        moon_seg_by_nak.setdefault(s["index"], []).append(s)

    matches: list[dict] = []
    for rule in rules:
        for planet in _PLANETS:
            expected_nak = rule["planet_map"][planet]
            if planet_nakshatras.get(planet) != expected_nak:
                continue

            if planet == "Moon":
                segs = moon_seg_by_nak.get(expected_nak, [])
                if not segs:
                    continue
                start_jd = segs[0]["start_jd"]
                end_jd = segs[-1]["end_jd"]
            elif planet_windows and planet in planet_windows:
                start_jd, end_jd = planet_windows[planet]
            else:
                start_jd = sunrise_jd
                end_jd = next_sunrise_jd

            matches.append(_build_aanandadi_match(rule, planet, expected_nak, start_jd, end_jd))

    return matches


def _build_aanandadi_match(
    rule: dict,
    planet: str,
    nak_index: int,
    start_jd: float,
    end_jd: float,
) -> dict:
    varjya_spec = rule["varjya"]
    if varjya_spec is None:
        v_minutes = None
        v_start_jd = None
        v_end_jd = None
    elif varjya_spec == "full_day":
        v_minutes = "full_day"
        v_start_jd = None
        v_end_jd = None
    else:
        v_minutes = varjya_minutes(varjya_spec)
        v_start_jd = start_jd
        v_end_jd = start_jd + v_minutes / 1440.0

    return {
        "name": rule["name"],
        "nature": rule["nature"],
        "severity": rule["severity"],
        "fal": rule["fal"],
        "meaning": rule["meaning"],
        "severe": rule["severe"],
        "triggering_planet": planet,
        "trigger_nakshatra_index": nak_index,
        "start_jd": start_jd,
        "end_jd": end_jd,
        "varjya_minutes": v_minutes,
        "varjya_start_jd": v_start_jd,
        "varjya_end_jd": v_end_jd,
    }


# ---------------------------------------------------------------------------
# Dainika matching
# ---------------------------------------------------------------------------

def match_dainika(
    rules: list[dict],
    vara: int,
    tithi_segments: list[dict],
    nakshatra_segments: list[dict],
) -> list[dict]:
    """Return all active Dainika yoga matches for the given day.

    For tithi rules: one match per matching tithi segment.
    For nakshatra rules: one match per matching nakshatra segment.
    For tithi_and_nakshatra rules: one match per non-empty intersection.
    """
    matches: list[dict] = []

    for rule in rules:
        vara_map: dict = rule["vara_map"]
        if vara not in vara_map:
            continue

        trigger = rule["trigger"]

        if trigger == "tithi_and_nakshatra":
            tithi_vals: list[int] = rule.get("tithi_values", [])
            nak_vals: list[int] = rule.get("nakshatra_values", [])
            for t_seg in tithi_segments:
                if t_seg["index"] not in tithi_vals:
                    continue
                for n_seg in nakshatra_segments:
                    if n_seg["index"] not in nak_vals:
                        continue
                    result = overlap(t_seg, n_seg)
                    if result is None:
                        continue
                    start_jd, end_jd = result
                    matches.append({
                        **_dainika_base(rule, "tithi_and_nakshatra",
                                        f"Vara {vara}, Tithi {t_seg['index']}, Nakshatra {n_seg['index']}"),
                        "start_jd": start_jd,
                        "end_jd": end_jd,
                    })
            continue

        if trigger == "tithi":
            allowed: list[int] = vara_map.get(vara, [])
            for seg in tithi_segments:
                if seg["index"] in allowed:
                    matches.append({
                        **_dainika_base(rule, "tithi", f"Vara {vara}, Tithi {seg['index']}"),
                        "start_jd": seg["start_jd"],
                        "end_jd": seg["end_jd"],
                    })
        else:  # nakshatra
            allowed = vara_map.get(vara, [])
            for seg in nakshatra_segments:
                if seg["index"] in allowed:
                    matches.append({
                        **_dainika_base(rule, "nakshatra", f"Vara {vara}, Nakshatra {seg['index']}"),
                        "start_jd": seg["start_jd"],
                        "end_jd": seg["end_jd"],
                    })

    return matches


def _dainika_base(rule: dict, trigger_kind: str, trigger_detail: str) -> dict:
    return {
        "name": rule["name"],
        "nature": rule["nature"],
        "severity": rule["severity"],
        "severe": rule.get("severe", False),
        "meaning": rule["meaning"],
        "trigger_kind": trigger_kind,
        "trigger_detail": trigger_detail,
    }


# ---------------------------------------------------------------------------
# Dainika override rules
# ---------------------------------------------------------------------------

def apply_dainika_overrides(matches: list[dict]) -> list[dict]:
    """Apply Sarvartha Siddhi / Dusht Tithi override rules.

    Rules (applied to a copy — originals are not mutated):
    - Sarvartha Siddhi present → Dusht Tithi entries get cancelled=True
    - Dusht Tithi active (not cancelled) + no Sarvartha Siddhi → Amrit Siddhi gets diminished=True
    """
    result = [dict(m) for m in matches]

    has_sarvartha = any(y["name"] == "Sarvartha Siddhi" for y in result)

    for yoga in result:
        if yoga["name"] == "Dusht Tithi" and has_sarvartha:
            yoga["cancelled"] = True

    has_active_dusht = any(
        y["name"] == "Dusht Tithi" and not y.get("cancelled", False)
        for y in result
    )

    if has_active_dusht and not has_sarvartha:
        for yoga in result:
            if yoga["name"] == "Amrit Siddhi":
                yoga["diminished"] = True

    return result


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

def compute_recommendation(matches: list[dict]) -> str:
    """Derive a recommendation string from a list of yoga matches.

    Cancelled matches are excluded. Priority order:
      mixed > avoid > caution > highly_auspicious > auspicious > neutral

    "mixed" is returned when a severe (highly_inauspicious) yoga coexists with a
    highly_auspicious yoga — real danger and real opportunity are both present.
    "avoid" is returned when a severe yoga has no highly_auspicious counterbalance.
    """
    effective = [m for m in matches if not m.get("cancelled", False)]
    if not effective:
        return "neutral"

    severe = [m for m in effective if m["severe"]]
    shubh = [m for m in effective if m["nature"] == "shubh"]
    ashubh = [m for m in effective if m["nature"] == "ashubh" and not m["severe"]]
    highly = [m for m in shubh if m["severity"] == "highly_auspicious"]

    if severe:
        return "mixed" if highly else "avoid"

    if ashubh:
        return "caution"

    return "highly_auspicious" if highly else "auspicious"
