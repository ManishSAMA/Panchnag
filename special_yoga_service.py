"""
special_yoga_service.py — Yogas with no Vara restriction.

Three yogas that fire based solely on Moon nakshatra or longitude,
or on Tithi+Nakshatra conjunction regardless of weekday:

  Gandmool Nakshatra — Moon in any of 6 Rashi-junction nakshatras
  Panchak            — Moon longitude in [300°, 360°) (last 5 nakshatras)
  Jwalamukhi         — Specific Tithi + Nakshatra pairs, any Vara
"""

from __future__ import annotations

from datetime import date as date_type

# ---------------------------------------------------------------------------
# Gandmool Nakshatra
# ---------------------------------------------------------------------------

# Nakshatras at Rashi junctions (Gand = knot, Mool = root):
#   Ashvini (1), Ashlesha (9), Magha (10), Jyeshtha (18), Mula (19), Revati (27)
_GANDMOOL_NAKSHATRAS: frozenset[int] = frozenset({1, 9, 10, 18, 19, 27})

_GANDMOOL_NAMES: dict[int, str] = {
    1:  "Ashvini",
    9:  "Ashlesha",
    10: "Magha",
    18: "Jyeshtha",
    19: "Mula",
    27: "Revati",
}

# ---------------------------------------------------------------------------
# Jwalamukhi Yoga
# ---------------------------------------------------------------------------

# (Tithi, Nakshatra) pairs — any Vara
_JWALAMUKHI_PAIRS: frozenset[tuple[int, int]] = frozenset({
    (1,  19),   # Pratipada + Mula
    (5,  2),    # Panchami + Bharani
    (9,  4),    # Navami + Rohini
    (9,  3),    # Navami + Kritika
    (10, 9),    # Dashami + Ashlesha
})


# ---------------------------------------------------------------------------
# Main detection function
# ---------------------------------------------------------------------------

def detect_special_yogas_for_day(
    *,
    date_obj: date_type,
    sunrise_jd: float,
    next_sunrise_jd: float,
    tz_name: str,
    ayanamsa: str = "Lahiri",
) -> dict:
    """Return special yogas active during the solar day (sunrise to next sunrise).

    Returns:
        {
            "special_yogas": [
                {
                    "name": str,
                    "nature": str,        # "ashubh" for all three
                    "severity": str,
                    "meaning": str,
                    "start_time": str,    # HH:MM local
                    "end_time": str,
                    "start_local": str,   # ISO
                    "end_local": str,
                    "start_jd": float,
                    "end_jd": float,
                    "clipped_start": bool,  # window extends before today's sunrise
                    "clipped_end": bool,    # window extends past next sunrise
                    "trigger_detail": str,
                }, ...
            ]
        }
    """
    from astronomy import jd_to_zoned_datetime
    from dainika_muhurta_service import compute_day_segments
    from panchang import calculate_bhadra_kaal, calculate_panchak_kaal

    segs = compute_day_segments(sunrise_jd, next_sunrise_jd, ayanamsa, tz_name)
    results: list[dict] = []

    def _fmt(jd: float) -> tuple[str, str]:
        dt = jd_to_zoned_datetime(jd, tz_name)
        if dt is None:
            return "", ""
        return dt.strftime("%H:%M"), dt.isoformat(timespec="seconds")

    # ── 1. Gandmool Nakshatra ─────────────────────────────────────────────
    gandmool_segs = [s for s in segs["nakshatra_segments"] if s["index"] in _GANDMOOL_NAKSHATRAS]
    if gandmool_segs:
        # Merge consecutive Gandmool segments into contiguous windows
        windows: list[tuple[float, float, list[int]]] = []
        for seg in gandmool_segs:
            if windows and abs(seg["start_jd"] - windows[-1][1]) < 30.0 / 86400.0:
                windows[-1] = (windows[-1][0], seg["end_jd"], windows[-1][2] + [seg["index"]])
            else:
                windows.append((seg["start_jd"], seg["end_jd"], [seg["index"]]))

        for w_start, w_end, nak_indices in windows:
            st_time, st_local = _fmt(w_start)
            en_time, en_local = _fmt(w_end)
            naks = ", ".join(_GANDMOOL_NAMES[i] for i in nak_indices if i in _GANDMOOL_NAMES)
            results.append({
                "name": "Gandmool Nakshatra",
                "nature": "ashubh",
                "severity": "inauspicious",
                "meaning": "Junction nakshatra — inauspicious for births and new beginnings. Purification rites advised.",
                "start_time": st_time,
                "end_time": en_time,
                "start_local": st_local,
                "end_local": en_local,
                "start_jd": w_start,
                "end_jd": w_end,
                "clipped_start": w_start == sunrise_jd and gandmool_segs[0]["index"] in _GANDMOOL_NAKSHATRAS,
                "clipped_end": w_end == next_sunrise_jd,
                "trigger_detail": f"Moon in {naks}",
            })

    # ── 2. Panchak ────────────────────────────────────────────────────────
    panchak = calculate_panchak_kaal(sunrise_jd, next_sunrise_jd, ayanamsa)
    for pw in panchak.get("windows", []):
        w_start = pw["start_jd"]
        w_end   = pw["end_jd"]
        st_time, st_local = _fmt(w_start)
        en_time, en_local = _fmt(w_end)
        results.append({
            "name": "Panchak",
            "nature": "ashubh",
            "severity": "inauspicious",
            "meaning": "Last 5 nakshatras — avoid funeral rites, travel south, collecting wood, construction, and marriage.",
            "start_time": st_time,
            "end_time": en_time,
            "start_local": st_local,
            "end_local": en_local,
            "start_jd": w_start,
            "end_jd": w_end,
            "clipped_start": pw.get("clipped_start", False),
            "clipped_end": pw.get("clipped_end", False),
            "trigger_detail": f"Moon in {pw.get('nakshatra', 'Panchak zone')}",
        })

    # ── 3. Bhadra (Vishti Karana) ─────────────────────────────────────────
    for w in calculate_bhadra_kaal(sunrise_jd, next_sunrise_jd, ayanamsa):
        st_time, st_local = _fmt(w["start_jd"])
        en_time, en_local = _fmt(w["end_jd"])
        results.append({
            "name": "Bhadra (Vishti)",
            "nature": "ashubh",
            "severity": "inauspicious",
            "meaning": "Vishti Karana — inauspicious half-tithi period. Avoid all new undertakings, travel, and auspicious ceremonies.",
            "start_time": st_time,
            "end_time": en_time,
            "start_local": st_local,
            "end_local": en_local,
            "start_jd": w["start_jd"],
            "end_jd": w["end_jd"],
            "clipped_start": w.get("clipped_start", False),
            "clipped_end": w.get("clipped_end", False),
            "trigger_detail": f"Vishti Karana — Moon in {w.get('residence', '')} rashi (risk: {w.get('risk_level', '')})",
        })

    # ── 4. Jwalamukhi Yoga ────────────────────────────────────────────────
    for t_seg in segs["tithi_segments"]:
        for n_seg in segs["nakshatra_segments"]:
            if (t_seg["index"], n_seg["index"]) not in _JWALAMUKHI_PAIRS:
                continue
            seg_start = max(t_seg["start_jd"], n_seg["start_jd"])
            seg_end   = min(t_seg["end_jd"],   n_seg["end_jd"])
            if seg_end <= seg_start:
                continue
            st_time, st_local = _fmt(seg_start)
            en_time, en_local = _fmt(seg_end)
            results.append({
                "name": "Jwalamukhi",
                "nature": "ashubh",
                "severity": "inauspicious",
                "meaning": "Flame-mouth — combustive energy; avoid fire-related activities, surgery, and auspicious starts.",
                "start_time": st_time,
                "end_time": en_time,
                "start_local": st_local,
                "end_local": en_local,
                "start_jd": seg_start,
                "end_jd": seg_end,
                "clipped_start": False,
                "clipped_end": False,
                "trigger_detail": f"Tithi {t_seg['index']} + Nakshatra {n_seg['index']}",
            })

    return {"special_yogas": results}
