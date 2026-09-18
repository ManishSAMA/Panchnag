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

_NAK_NAMES: tuple[str, ...] = (
    "Ashvini", "Bharani", "Kritika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
_TITHI_NAMES: tuple[str, ...] = (
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
)


def _nak_name(idx: int) -> str:
    return _NAK_NAMES[idx - 1] if 1 <= idx <= 27 else f"Nak {idx}"


def _tithi_name(idx: int) -> str:
    if 1 <= idx <= 15:
        return _TITHI_NAMES[idx - 1]
    if 16 <= idx <= 30:
        return "K. " + _TITHI_NAMES[idx - 16]
    return f"Tithi {idx}"


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
# Aanandadi matching — formula-based, Moon nakshatra + Vara only
# ---------------------------------------------------------------------------

def _to_28_nak(std_nak: int) -> int:
    """Convert standard nakshatra index (1–27, or 28=Abhijit) to 28-nak system.

    In the 28-nakshatra system Abhijit is inserted at position 22, shifting
    Shravana (22)→23, Dhanishtha (23)→24, …, Revati (27)→28.
    """
    if std_nak == 28:   # Abhijit
        return 22
    if std_nak <= 21:   # Ashvini … Uttara Ashadha — unchanged
        return std_nak
    return std_nak + 1  # Shravana(22)→23 … Revati(27)→28


def aanandadi_yoga_index(std_nak: int, vara: int) -> int:
    """Return the Aanandadi yoga index (1–28) for a Moon nakshatra on a given weekday.

    Formula: Y = (N_idx − (V_idx − 1) × 4) mod 28
    Where N_idx uses the 28-nakshatra system and V_idx = vara + 1.
    Result 0 maps to index 28 (Vriddhi).
    """
    n_idx = _to_28_nak(std_nak)
    v_idx = vara + 1
    y = (n_idx - (v_idx - 1) * 4) % 28
    return y if y != 0 else 28


def match_aanandadi(
    yogas: list[dict],
    vara: int,
    moon_segments: list[dict],
) -> list[dict]:
    """Return one Aanandadi yoga match per Moon nakshatra window during the day.

    When Moon transitions nakshatras mid-day each segment produces its own yoga.
    The yoga is determined exclusively by the weekday (vara) and Moon's nakshatra
    using the Aanandadi formula — no planetary positions involved.
    """
    matches: list[dict] = []
    for seg in moon_segments:
        y = aanandadi_yoga_index(seg["index"], vara)
        yoga_def = yogas[y - 1]
        start_jd = seg["start_jd"]
        end_jd = seg["end_jd"]

        varjya_spec = yoga_def["varjya"]
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

        matches.append({
            "name": yoga_def["name"],
            "nature": yoga_def["nature"],
            "severity": yoga_def["severity"],
            "fal": yoga_def["fal"],
            "meaning": yoga_def["meaning"],
            "severe": yoga_def["severe"],
            "yoga_index": y,
            "trigger_nakshatra_index": seg["index"],
            "start_jd": start_jd,
            "end_jd": end_jd,
            "varjya_minutes": v_minutes,
            "varjya_start_jd": v_start_jd,
            "varjya_end_jd": v_end_jd,
        })

    return matches


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
                                        f"{_tithi_name(t_seg['index'])} + {_nak_name(n_seg['index'])}"),
                        "start_jd": start_jd,
                        "end_jd": end_jd,
                    })
            continue

        if trigger == "tithi":
            allowed: list[int] = vara_map.get(vara, [])
            for seg in tithi_segments:
                if seg["index"] in allowed:
                    matches.append({
                        **_dainika_base(rule, "tithi", _tithi_name(seg["index"])),
                        "start_jd": seg["start_jd"],
                        "end_jd": seg["end_jd"],
                    })
        else:  # nakshatra
            allowed = vara_map.get(vara, [])
            for seg in nakshatra_segments:
                if seg["index"] in allowed:
                    matches.append({
                        **_dainika_base(rule, "nakshatra", _nak_name(seg["index"])),
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


def detect_yogas(*, vara: int, tithi: int, nakshatra: int) -> dict:
    """Helper for legacy tests to verify rules matching."""
    from yoga_rules import DAINIKA_RULES
    tithi_segs = [{"index": tithi, "start_jd": 0.0, "end_jd": 1.0}]
    nak_segs = [{"index": nakshatra, "start_jd": 0.0, "end_jd": 1.0}]
    matches = match_dainika(DAINIKA_RULES, vara, tithi_segs, nak_segs)
    overridden = apply_dainika_overrides(matches)
    recommendation = compute_recommendation(overridden)
    return {
        "yogas": overridden,
        "recommendation": recommendation,
    }
