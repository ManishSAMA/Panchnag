"""
dainika_muhurta_service.py — Panchang Yoga (Muhurta) detection.

Detects which of the 31 traditional Vara/Tithi/Nakshatra yogas are active
on a given day and produces a final muhurta recommendation.

Vara:      0=Sunday … 6=Saturday
Tithi:     1–30
Nakshatra: 1–27 (28=Abhijit where applicable)
"""

from __future__ import annotations

from datetime import date as date_type

# ---------------------------------------------------------------------------
# Rule table — 31 yogas
# ---------------------------------------------------------------------------
# Each rule dict contains:
#   name         – canonical yoga name
#   nature       – "shubh" | "ashubh"
#   trigger      – "tithi" | "nakshatra"
#   severity     – "highly_auspicious" | "auspicious" | "inauspicious" | "highly_inauspicious"
#   meaning      – short English meaning
#   vara_map     – {vara_index: [tithi_values]} or {vara_index: [nakshatra_values]}
#   severe       – True when this yoga alone forces "avoid" recommendation

YOGA_RULES: list[dict] = [
    # ── SECTION 1: TITHI-BASED ────────────────────────────────────────────
    {
        "name": "Siddhi Yoga Tithi",
        "nature": "shubh",
        "trigger": "tithi",
        "severity": "auspicious",
        "meaning": "Accomplishment — work started here reaches completion successfully.",
        "vara_map": {
            2: [3, 8, 13],   # Tuesday
            3: [2, 7, 12],   # Wednesday
            4: [5, 10, 15],  # Thursday
            5: [1, 6, 11],   # Friday
            6: [4, 9, 14],   # Saturday
        },
    },
    {
        "name": "Dagdha Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Burnt — work started here gets destroyed. Avoid new beginnings.",
        "vara_map": {
            0: [12],   # Sunday
            1: [11],   # Monday
            2: [5],    # Tuesday
            3: [3],    # Wednesday
            4: [6],    # Thursday
            5: [8],    # Friday
            6: [9],    # Saturday
        },
    },
    {
        "name": "Hutashan Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Consumed by fire — efforts get destroyed. Harmful for auspicious starts.",
        "vara_map": {
            0: [12],   # Sunday
            1: [6],    # Monday
            2: [7],    # Tuesday
            3: [8],    # Wednesday
            4: [9],    # Thursday
            5: [10],   # Friday
            6: [11],   # Saturday
        },
    },
    {
        "name": "Vishakhya Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Poison — undertakings here tend to have harmful or toxic results.",
        "vara_map": {
            0: [4],    # Sunday
            1: [6],    # Monday
            2: [7],    # Tuesday
            3: [2],    # Wednesday
            4: [8],    # Thursday
            5: [9],    # Friday
            6: [7],    # Saturday
        },
    },
    {
        "name": "Adham Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Lowest/inferior — work here gives degraded or base results.",
        "vara_map": {
            0: [7, 12],     # Sunday
            1: [11],        # Monday
            2: [10],        # Tuesday
            3: [1, 9],      # Wednesday
            4: [8],         # Thursday
            5: [7],         # Friday
            6: [6],         # Saturday
        },
    },
    {
        "name": "Mrityu Yoga Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Death — one of the most inauspicious yogas. Strongly avoid all auspicious muhurtas.",
        "vara_map": {
            0: [1, 6, 11],  # Sunday
            1: [2, 7, 12],  # Monday
            2: [1, 6, 11],  # Tuesday
            3: [3, 8, 13],  # Wednesday
            4: [4, 9, 14],  # Thursday
            5: [2, 7, 12],  # Friday
            6: [5, 10, 15], # Saturday
        },
    },
    {
        "name": "Krakach Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Saw — cuts through benefits. Efforts will be cut short or disrupted.",
        "vara_map": {
            0: [12],   # Sunday
            1: [11],   # Monday
            2: [10],   # Tuesday
            3: [9],    # Wednesday
            4: [8],    # Thursday
            5: [7],    # Friday
            6: [6],    # Saturday
        },
    },
    {
        "name": "Dusht Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Wicked/corrupt — gives corrupted results. Cancelled by Sarvartha Siddhi.",
        "vara_map": {
            0: [1, 3, 7],             # Sunday
            1: list(range(2, 12)),    # Monday: 2–11
            2: [3, 9, 12],            # Tuesday
            3: [7, 9, 11],            # Wednesday
            # Thursday: Pushya nakshatra mentioned — no tithi trigger
            6: list(range(11, 14)),   # Saturday: 11–13
        },
    },
    # ── SECTION 2: NAKSHATRA-BASED (Vara + Nakshatra) ─────────────────────
    {
        "name": "Varjit Tithi Nakshatra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Forbidden nakshatra+vara — strictly avoid for auspicious muhurtas.",
        "vara_map": {
            0: [13],   # Sunday: Hasta
            1: [5],    # Monday: Mrigashira
            2: [1],    # Tuesday: Ashvini
            3: [24],   # Wednesday: Shatabhisha
            4: [8],    # Thursday: Pushya
            5: [27],   # Friday: Revati
            6: [4],    # Saturday: Rohini
        },
    },
    {
        "name": "Utpat Nakshatra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Calamity — creates turbulence and unexpected trouble.",
        "vara_map": {
            0: [16],   # Sunday: Vishakha
            1: [11],   # Monday: Purva Phalguni
            2: [23],   # Tuesday: Dhanishtha
            3: [27],   # Wednesday: Revati
            4: [4],    # Thursday: Rohini
            5: [8],    # Friday: Pushya
            6: [12],   # Saturday: Uttara Phalguni
        },
    },
    {
        "name": "Mrityu Yoga Nakshatra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Death yoga via Nakshatra — extremely inauspicious. No muhurta should be given.",
        "vara_map": {
            0: [17],   # Sunday: Anuradha
            1: [21],   # Monday: Uttara Ashadha
            2: [24],   # Tuesday: Shatabhisha
            3: [1],    # Wednesday: Ashvini
            4: [5],    # Thursday: Mrigashira
            5: [9],    # Friday: Ashlesha
            6: [13],   # Saturday: Hasta
        },
    },
    # ── SECTION 3: NAMED NAKSHATRA+VARA YOGAS ─────────────────────────────
    {
        "name": "Kaan Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "One-eyed — incomplete results. Especially bad for legal, contractual, medical muhurtas.",
        "vara_map": {
            0: [18],   # Sunday: Jyeshtha
            1: [28],   # Monday: Abhijit
            2: [25],   # Tuesday: Purva Bhadrapada
            3: [2],    # Wednesday: Bharani
            4: [6],    # Thursday: Ardra
            5: [10],   # Friday: Magha
            6: [14],   # Saturday: Chitra
        },
    },
    {
        "name": "Dagdha Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Burnt — all good effects are burnt away. Work does not bear fruit.",
        "vara_map": {
            0: [2],    # Sunday: Bharani
            1: [14],   # Monday: Chitra
            2: [21],   # Tuesday: Uttara Ashadha
            3: [23],   # Wednesday: Dhanishtha
            4: [12],   # Thursday: Uttara Phalguni
            5: [18],   # Friday: Jyeshtha
            6: [27],   # Saturday: Revati
        },
    },
    {
        "name": "Yam Ghant",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Bell of Yama — highly inauspicious. Signals proximity to harmful outcomes.",
        "vara_map": {
            0: [10],   # Sunday: Magha
            1: [16],   # Monday: Vishakha
            2: [6],    # Tuesday: Ardra
            3: [19],   # Wednesday: Mula
            4: [3],    # Thursday: Kritika
            5: [4],    # Friday: Rohini
            6: [13],   # Saturday: Hasta
        },
    },
    {
        "name": "Musal Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Pestle — crushes efforts. Especially bad for business starts and partnerships.",
        "vara_map": {
            0: [28],   # Sunday: Abhijit
            1: [25],   # Monday: Purva Bhadrapada
            2: [2],    # Tuesday: Bharani
            3: [6],    # Wednesday: Ardra
            4: [10],   # Thursday: Magha
            5: [14],   # Friday: Chitra
            6: [18],   # Saturday: Jyeshtha
        },
    },
    {
        "name": "Kaal Dand",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Staff of time — punishes actions started in it. Bad for government and legal matters.",
        "vara_map": {
            0: [2],    # Sunday: Bharani
            1: [6],    # Monday: Ardra
            2: [10],   # Tuesday: Magha
            3: [14],   # Wednesday: Chitra
            4: [18],   # Thursday: Jyeshtha
            5: [28],   # Friday: Abhijit
            6: [25],   # Saturday: Purva Bhadrapada
        },
    },
    {
        "name": "Vajra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Thunderbolt — strikes suddenly. Harmful for marriage, travel, new partnerships.",
        "vara_map": {
            0: [9],    # Sunday: Ashlesha
            1: [13],   # Monday: Hasta
            2: [17],   # Tuesday: Anuradha
            3: [21],   # Wednesday: Uttara Ashadha
            4: [24],   # Thursday: Shatabhisha
            5: [1],    # Friday: Ashvini
            6: [5],    # Saturday: Mrigashira
        },
    },
    {
        "name": "Rakshas Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Demon — one of the most feared yogas. All auspicious muhurtas forbidden.",
        "vara_map": {
            0: [24],   # Sunday: Shatabhisha
            1: [1],    # Monday: Ashvini
            2: [5],    # Tuesday: Mrigashira
            3: [9],    # Wednesday: Ashlesha
            4: [13],   # Thursday: Hasta
            5: [17],   # Friday: Anuradha
            6: [12],   # Saturday: Uttara Phalguni (Uttara Ashadha per source, mapped to 21 alt)
        },
    },
    {
        "name": "Dhwanksh",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Crow — brings bad news, separation, dark outcomes. Avoid family and social events.",
        "vara_map": {
            0: [6],    # Sunday: Ardra
            1: [10],   # Monday: Magha
            2: [14],   # Tuesday: Chitra
            3: [18],   # Wednesday: Jyeshtha
            4: [28],   # Thursday: Abhijit
            5: [25],   # Friday: Purva Bhadrapada
            6: [2],    # Saturday: Bharani
        },
    },
    {
        "name": "Dhumra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Smoke — clouds clarity. Results unclear or obscured. Avoid contracts and negotiations.",
        "vara_map": {
            0: [3],    # Sunday: Kritika
            1: [7],    # Monday: Punarvasu
            2: [11],   # Tuesday: Purva Phalguni
            3: [15],   # Wednesday: Swati
            4: [19],   # Thursday: Mula
            5: [22],   # Friday: Shravana
            6: [26],   # Saturday: Uttara Bhadrapada
        },
    },
    {
        "name": "Gad",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Disease — brings illness or heavy obstacles. Avoided for health and medical muhurtas.",
        "vara_map": {
            0: [22],   # Sunday: Shravana
            1: [26],   # Monday: Uttara Bhadrapada
            2: [3],    # Tuesday: Kritika
            3: [7],    # Wednesday: Punarvasu
            4: [11],   # Thursday: Purva Phalguni
            5: [15],   # Friday: Swati
            6: [19],   # Saturday: Mula
        },
    },
    {
        "name": "Anand",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Joy/bliss — brings happiness. Good for celebrations and social gatherings.",
        "vara_map": {
            0: [1],    # Sunday: Ashvini
            1: [5],    # Monday: Mrigashira
            2: [9],    # Tuesday: Ashlesha
            3: [13],   # Wednesday: Hasta
            4: [17],   # Thursday: Anuradha
            5: [21],   # Friday: Uttara Ashadha
            6: [24],   # Saturday: Shatabhisha
        },
    },
    {
        "name": "Shrivatsa",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Divine mark of Vishnu — brings prosperity and divine grace. Good for financial muhurtas.",
        "vara_map": {
            0: [8],    # Sunday: Pushya
            1: [12],   # Monday: Uttara Phalguni
            2: [16],   # Tuesday: Vishakha
            3: [20],   # Wednesday: Purva Ashadha
            4: [23],   # Thursday: Dhanishtha
            5: [27],   # Friday: Revati
            6: [4],    # Saturday: Rohini
        },
    },
    {
        "name": "Saumya",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Gentle/benevolent — calmness and pleasant outcomes. Good for relationships and healing.",
        "vara_map": {
            0: [5],    # Sunday: Mrigashira
            1: [9],    # Monday: Ashlesha
            2: [13],   # Tuesday: Hasta
            3: [17],   # Wednesday: Anuradha
            4: [21],   # Thursday: Uttara Ashadha
            5: [24],   # Friday: Shatabhisha
            6: [1],    # Saturday: Ashvini
        },
    },
    {
        "name": "Chatra",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Royal canopy — protection and prestige. Good for authority and leadership muhurtas.",
        "vara_map": {
            0: [11],   # Sunday: Purva Phalguni
            1: [15],   # Monday: Swati
            2: [19],   # Tuesday: Mula
            3: [22],   # Wednesday: Shravana
            4: [26],   # Thursday: Uttara Bhadrapada
            5: [3],    # Friday: Kritika
            6: [7],    # Saturday: Punarvasu
        },
    },
    {
        "name": "Shubh",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Auspicious/good — blesses any work started in it with good results.",
        "vara_map": {
            0: [20],   # Sunday: Purva Ashadha
            1: [23],   # Monday: Dhanishtha
            2: [27],   # Tuesday: Revati
            3: [4],    # Wednesday: Rohini
            4: [8],    # Thursday: Pushya
            5: [12],   # Friday: Uttara Phalguni
            6: [16],   # Saturday: Vishakha
        },
    },
    {
        "name": "Amrit",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Nectar — excellent, long-lasting, fruitful results. Highly recommended for muhurtas.",
        "vara_map": {
            0: [21],   # Sunday: Uttara Ashadha
            1: [24],   # Monday: Shatabhisha
            2: [1],    # Tuesday: Ashvini
            3: [5],    # Wednesday: Mrigashira
            4: [9],    # Thursday: Ashlesha
            5: [13],   # Friday: Hasta
            6: [17],   # Saturday: Anuradha
        },
    },
    {
        "name": "Mitra",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Friend — friendly, cooperative energy. Excellent for partnerships and marriages.",
        "vara_map": {
            0: [12],   # Sunday: Uttara Phalguni
            1: [16],   # Monday: Vishakha
            2: [11],   # Tuesday: Purva Phalguni
            3: [23],   # Wednesday: Dhanishtha
            4: [27],   # Thursday: Revati
            5: [4],    # Friday: Rohini
            6: [8],    # Saturday: Pushya
        },
    },
    {
        "name": "Siddha Yoga",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Accomplished — work reaches its intended goal. Great for precision tasks.",
        "vara_map": {
            0: [19],   # Sunday: Mula
            1: [22],   # Monday: Shravana
            2: [26],   # Tuesday: Uttara Bhadrapada
            3: [3],    # Wednesday: Kritika
            4: [7],    # Thursday: Punarvasu
            5: [11],   # Friday: Purva Phalguni
            6: [15],   # Saturday: Swati
        },
    },
    {
        "name": "Amrit Siddhi",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Nectar of accomplishment — highest auspicious yoga. Work is blessed with completion and longevity.",
        "vara_map": {
            0: [13],   # Sunday: Hasta
            1: [22],   # Monday: Shravana
            2: [1],    # Tuesday: Ashvini
            3: [17],   # Wednesday: Anuradha
            4: [8],    # Thursday: Pushya
            5: [27],   # Friday: Revati
            6: [4],    # Saturday: Rohini
        },
    },
    {
        "name": "Sarvartha Siddhi",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Accomplishment of all purposes — extremely powerful. Fulfils any objective.",
        "vara_map": {
            0: [13, 19, 8, 1],   # Sunday: Hasta, Mula, Pushya, Ashvini
            1: [22, 4, 5],       # Monday: Shravana, Rohini, Mrigashira
            2: [1, 8, 26, 17],   # Tuesday: Ashvini, Pushya, Uttara Bhadrapada, Anuradha
            3: [4, 17, 13],      # Wednesday: Rohini, Anuradha, Hasta
            4: [27, 17, 1, 7],   # Thursday: Revati, Anuradha, Ashvini, Punarvasu
            5: [27, 17, 1, 7, 22],  # Friday: Revati, Anuradha, Ashvini, Punarvasu, Shravana
            6: [4, 22, 15],      # Saturday: Rohini, Shravana, Swati
        },
    },
]

# ---------------------------------------------------------------------------
# Yoga detection
# ---------------------------------------------------------------------------

_SEVERE_NAMES = frozenset(
    r["name"] for r in YOGA_RULES if r.get("severe", False)
)

_HIGHLY_AUSPICIOUS_NAMES = frozenset(
    r["name"] for r in YOGA_RULES if r["severity"] == "highly_auspicious"
)


def detect_yogas(*, vara: int, tithi: int, nakshatra: int) -> dict:
    """Return all active yogas for the given (vara, tithi, nakshatra) triple.

    Args:
        vara:      Weekday index 0=Sunday … 6=Saturday.
        tithi:     Lunar day 1–30.
        nakshatra: Lunar mansion 1–27 (28=Abhijit).

    Returns:
        {
            "yogas": [...],         # list of active yoga dicts
            "recommendation": str,  # highly_auspicious | auspicious | caution | avoid | neutral
        }
    """
    active: list[dict] = []

    for rule in YOGA_RULES:
        vara_map: dict = rule["vara_map"]
        values = vara_map.get(vara, [])
        if not values:
            continue

        check_value = tithi if rule["trigger"] == "tithi" else nakshatra
        if check_value not in values:
            continue

        entry = {
            "name": rule["name"],
            "nature": rule["nature"],
            "trigger_kind": rule["trigger"],
            "trigger_detail": f"Vara {vara}, {'Tithi' if rule['trigger'] == 'tithi' else 'Nakshatra'} {check_value}",
            "severity": rule["severity"],
            "meaning": rule["meaning"],
        }
        active.append(entry)

    # ── Override rules ────────────────────────────────────────────────────
    has_sarvartha = any(y["name"] == "Sarvartha Siddhi" for y in active)
    has_amrit_siddhi = any(y["name"] == "Amrit Siddhi" for y in active)

    for yoga in active:
        if yoga["name"] == "Dusht Tithi" and has_sarvartha:
            yoga["cancelled"] = True
        elif yoga["name"] == "Amrit Siddhi" and _has_active_dusht(active) and not has_sarvartha:
            yoga["diminished"] = True

    # ── Recommendation ────────────────────────────────────────────────────
    recommendation = _compute_recommendation(active)

    return {"yogas": active, "recommendation": recommendation}


def _has_active_dusht(yogas: list[dict]) -> bool:
    return any(
        y["name"] == "Dusht Tithi" and not y.get("cancelled", False)
        for y in yogas
    )


def _compute_recommendation(yogas: list[dict]) -> str:
    effective = [y for y in yogas if not y.get("cancelled", False)]

    severe_active = [y for y in effective if y["name"] in _SEVERE_NAMES]
    if severe_active:
        return "avoid"

    ashubh = [y for y in effective if y["nature"] == "ashubh"]
    shubh = [y for y in effective if y["nature"] == "shubh"]

    if not effective:
        return "neutral"

    highly_auspicious = [y for y in shubh if y["severity"] == "highly_auspicious"]
    if highly_auspicious and not ashubh:
        return "highly_auspicious"

    if shubh and not ashubh:
        return "auspicious"

    if ashubh and not shubh:
        return "caution"

    # Mixed: shubh and ashubh both present
    return "caution"


def get_recommendation(yogas: list[dict]) -> str:
    """Public helper — compute recommendation from a list of yoga dicts."""
    return _compute_recommendation(yogas)


# ---------------------------------------------------------------------------
# Timed detection — walks Tithi/Nakshatra segments across the solar day
# ---------------------------------------------------------------------------

_SEGMENT_SAFETY_CAP = 10  # max number of tithi or nakshatra changes in one day


def compute_day_segments(
    sunrise_jd: float,
    next_sunrise_jd: float,
    ayanamsa: str = "Lahiri",
) -> dict:
    """Walk all Tithi and Nakshatra transitions between sunrise and next sunrise.

    Returns:
        {
          "tithi_segments":     [{"index": int, "start_jd": float, "end_jd": float}, ...],
          "nakshatra_segments": [{"index": int, "start_jd": float, "end_jd": float}, ...],
        }
    The first segment always starts at sunrise_jd and the last always ends at
    next_sunrise_jd; successive segments are contiguous.
    """
    from panchang import (
        _find_exact_end_time,
        get_tithi_at_jd,
        get_nakshatra_at_jd,
        calculate_tithi_details,
    )
    from astronomy import get_planetary_longitude

    # 30-second nudge — matches _collect_all_tithis_in_day in panchang_service.py
    # and is safely larger than _find_exact_end_time's bisection precision (~0.86 s)
    _NUDGE = 30.0 / 86400.0

    def _walk_segments(get_index_fn, start_jd: float, end_jd: float, trigger: str) -> list[dict]:
        segments: list[dict] = []
        cursor = start_jd
        prev_raw_end = start_jd  # tracks bisection boundary for display start

        for _ in range(_SEGMENT_SAFETY_CAP):
            idx = get_index_fn(cursor, ayanamsa)

            if trigger == "tithi":
                # calculate_tithi_details has proven tight low/high bounds (same as panchang)
                details = calculate_tithi_details(cursor, ayanamsa)
                raw_end = details["Tithi_End_JD"]
            else:
                # Tight bounds matching generate_daily_panchang in panchang.py
                moon_lon = get_planetary_longitude(cursor, "Moon", ayanamsa)
                nak_len = 360.0 / 27.0
                nak_left_deg = nak_len - (moon_lon % nak_len)
                nak_low = cursor + (nak_left_deg / 16.0)
                nak_high = cursor + (nak_left_deg / 11.0) + 0.05
                raw_end = _find_exact_end_time(
                    cursor, get_index_fn, idx, ayanamsa, nak_low, nak_high
                )

            seg_end = min(raw_end, end_jd)
            # Use prev_raw_end as start for exact contiguity in output
            seg_start = prev_raw_end
            segments.append({"index": idx, "start_jd": seg_start, "end_jd": seg_end})
            if seg_end >= end_jd:
                break
            prev_raw_end = raw_end   # next segment starts exactly where this one ended
            cursor = raw_end + _NUDGE   # nudge cursor past boundary for bisection

        if segments:
            segments[0]["start_jd"] = start_jd   # first segment starts exactly at sunrise
            segments[-1]["end_jd"] = end_jd       # last segment ends exactly at next sunrise
        return segments

    return {
        "tithi_segments": _walk_segments(
            get_tithi_at_jd, sunrise_jd, next_sunrise_jd, "tithi"
        ),
        "nakshatra_segments": _walk_segments(
            get_nakshatra_at_jd, sunrise_jd, next_sunrise_jd, "nakshatra"
        ),
    }


def detect_yogas_for_day(
    *,
    date_obj: date_type,
    sunrise_jd: float,
    next_sunrise_jd: float,
    tz_name: str,
    ayanamsa: str = "Lahiri",
) -> dict:
    """Detect all active yogas with precise start/end time windows.

    Each yoga entry includes ``start_time``, ``end_time`` (HH:MM local),
    ``start_local`` and ``end_local`` (ISO strings) so the UI and Excel export
    can show exactly when each yoga is active.

    Returns the same shape as ``detect_yogas`` plus per-yoga timing.
    """
    from panchang import get_vara_from_date, get_tithi_at_jd, get_nakshatra_at_jd
    from astronomy import jd_to_zoned_datetime

    segs = compute_day_segments(sunrise_jd, next_sunrise_jd, ayanamsa)
    vara = get_vara_from_date(date_obj)

    # Use the same functions as panchang generation — no double-ayanamsa correction
    sunrise_tithi = get_tithi_at_jd(sunrise_jd, ayanamsa)
    sunrise_nakshatra = get_nakshatra_at_jd(sunrise_jd, ayanamsa)

    def _fmt(jd: float) -> tuple[str, str]:
        dt = jd_to_zoned_datetime(jd, tz_name)
        if dt is None:
            return "", ""
        return dt.strftime("%H:%M"), dt.isoformat(timespec="seconds")

    # Build raw yoga entries from each segment
    raw: list[dict] = []

    for rule in YOGA_RULES:
        vara_values = rule["vara_map"].get(vara, [])
        if not vara_values:
            continue

        if rule["trigger"] == "tithi":
            for seg in segs["tithi_segments"]:
                if seg["index"] in vara_values:
                    st_time, st_local = _fmt(seg["start_jd"])
                    en_time, en_local = _fmt(seg["end_jd"])
                    raw.append({
                        "name": rule["name"],
                        "nature": rule["nature"],
                        "trigger_kind": "tithi",
                        "trigger_detail": f"Vara {vara}, Tithi {seg['index']}",
                        "severity": rule["severity"],
                        "meaning": rule["meaning"],
                        "start_time": st_time,
                        "end_time": en_time,
                        "start_local": st_local,
                        "end_local": en_local,
                    })
        else:  # nakshatra
            for seg in segs["nakshatra_segments"]:
                if seg["index"] in vara_values:
                    st_time, st_local = _fmt(seg["start_jd"])
                    en_time, en_local = _fmt(seg["end_jd"])
                    raw.append({
                        "name": rule["name"],
                        "nature": rule["nature"],
                        "trigger_kind": "nakshatra",
                        "trigger_detail": f"Vara {vara}, Nakshatra {seg['index']}",
                        "severity": rule["severity"],
                        "meaning": rule["meaning"],
                        "start_time": st_time,
                        "end_time": en_time,
                        "start_local": st_local,
                        "end_local": en_local,
                    })

    # Apply override rules (same logic as detect_yogas)
    has_sarvartha = any(y["name"] == "Sarvartha Siddhi" for y in raw)
    for yoga in raw:
        if yoga["name"] == "Dusht Tithi" and has_sarvartha:
            yoga["cancelled"] = True
        elif yoga["name"] == "Amrit Siddhi" and _has_active_dusht(raw) and not has_sarvartha:
            yoga["diminished"] = True

    recommendation = _compute_recommendation(raw)

    return {
        "vara": vara,
        "tithi": sunrise_tithi,
        "nakshatra": sunrise_nakshatra,
        "yogas": raw,
        "recommendation": recommendation,
    }
