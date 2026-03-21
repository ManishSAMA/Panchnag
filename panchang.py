"""
panchang.py — Vedic Panchang element calculations.

Computes the five Panchang elements (Pancha Anga):
  1. Tithi   — Lunar day (30 per lunar month)
  2. Nakshatra — Lunar mansion (27 total)
  3. Yoga    — Luni-solar combination (27 total)
  4. Karana  — Half-Tithi (60 per lunar month, 11 types in cycle)
  5. Vara    — Weekday (7 days)

All formulas follow classical Vedic astronomy.
"""

import math
from astronomy import get_planetary_longitude

# ---------------------------------------------------------------------------
# Reference Name Lists
# ---------------------------------------------------------------------------

TITHI_NAMES: list[str] = [
    # Shukla Paksha (Waxing / Bright fortnight)
    "Shukla Pratipada",  "Shukla Dwitiya",    "Shukla Tritiya",
    "Shukla Chaturthi",  "Shukla Panchami",   "Shukla Shashthi",
    "Shukla Saptami",    "Shukla Ashtami",    "Shukla Navami",
    "Shukla Dashami",    "Shukla Ekadashi",   "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi","Purnima",
    # Krishna Paksha (Waning / Dark fortnight)
    "Krishna Pratipada", "Krishna Dwitiya",   "Krishna Tritiya",
    "Krishna Chaturthi", "Krishna Panchami",  "Krishna Shashthi",
    "Krishna Saptami",   "Krishna Ashtami",   "Krishna Navami",
    "Krishna Dashami",   "Krishna Ekadashi",  "Krishna Dwadashi",
    "Krishna Trayodashi","Krishna Chaturdashi","Amavasya",
]

NAKSHATRA_NAMES: list[str] = [
    "Ashwini",          "Bharani",          "Krittika",
    "Rohini",           "Mrigashirsha",     "Ardra",
    "Punarvasu",        "Pushya",           "Ashlesha",
    "Magha",            "Purva Phalguni",   "Uttara Phalguni",
    "Hasta",            "Chitra",           "Swati",
    "Vishakha",         "Anuradha",         "Jyeshtha",
    "Mula",             "Purva Ashadha",    "Uttara Ashadha",
    "Shravana",         "Dhanishta",        "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada","Revati",
]

YOGA_NAMES: list[str] = [
    "Vishkumbha", "Priti",     "Ayushman",  "Saubhagya", "Shobhana",
    "Atiganda",   "Sukarma",   "Dhriti",    "Shula",     "Ganda",
    "Vriddhi",    "Dhruva",    "Vyaghata",  "Harshana",  "Vajra",
    "Siddhi",     "Vyatipata", "Variyana",  "Parigha",   "Shiva",
    "Siddha",     "Sadhya",    "Shubha",    "Shukla",    "Brahma",
    "Indra",      "Vaidhriti",
]

# Vara: 0 = Sunday (Ravivara)
VARA_NAMES: list[str] = [
    "Ravivara (Sunday)",    "Somavara (Monday)",
    "Mangalavara (Tuesday)","Budhavara (Wednesday)",
    "Guruvara (Thursday)",  "Shukravara (Friday)",
    "Shanivara (Saturday)",
]

# ---------------------------------------------------------------------------
# Karana Names & Cycle Logic
# ---------------------------------------------------------------------------
# There are 11 Karana types.
# The 60 Karanas of a lunar month are assigned as follows:
#   - Karana index 0  → Kimstughna (fixed, occurs only once)
#   - Karana index 1–56 → cycle through 7 movable Karanas repeated 8 times
#   - Karana index 57 → Shakuni  (fixed)
#   - Karana index 58 → Chatushpada (fixed)
#   - Karana index 59 → Naga      (fixed)

MOVABLE_KARANAS: list[str] = [
    "Bava", "Balava", "Kaulava", "Taitila",
    "Garaja", "Vanija", "Vishti (Bhadra)",
]

FIXED_KARANAS_START: list[str] = ["Kimstughna"]   # index 0
FIXED_KARANAS_END: list[str]   = ["Shakuni", "Chatushpada", "Naga"]  # indices 57-59


def _get_karana_name_from_index(karana_index: int) -> str:
    """Map a Karana index (0–59) to its Karana name.

    The classical 60-Karana cycle:
      - Position 0        → Kimstughna (fixed)
      - Positions 1–56    → seven movable Karanas cycling repeatedly
      - Position 57       → Shakuni   (fixed)
      - Position 58       → Chatushpada (fixed)
      - Position 59       → Naga        (fixed)
    """
    k = karana_index % 60
    if k == 0:
        return FIXED_KARANAS_START[0]
    elif 1 <= k <= 56:
        return MOVABLE_KARANAS[(k - 1) % 7]
    elif k == 57:
        return FIXED_KARANAS_END[0]
    elif k == 58:
        return FIXED_KARANAS_END[1]
    else:  # k == 59
        return FIXED_KARANAS_END[2]


# ---------------------------------------------------------------------------
# Core Calculation Functions
# ---------------------------------------------------------------------------

def get_tithi(sun_lon: float, moon_lon: float) -> int:
    """Compute Tithi index (1–30).

    Tithi = floor( (Moon − Sun) / 12° ) + 1
    The first Tithi (Pratipada Shukla) begins when the angular difference
    is 0°, and each subsequent Tithi spans 12°.
    """
    diff = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(diff / 12.0)
    return tithi_idx + 1  # 1-indexed


def get_nakshatra(moon_lon: float) -> int:
    """Compute Nakshatra index (1–27).

    Nakshatra = floor( Moon_Longitude / (360°/27) ) + 1
    Each Nakshatra spans 13°20' = 13.3333°.
    """
    nakshatra_length = 360.0 / 27.0
    nakshatra_idx = int(moon_lon / nakshatra_length)
    return (nakshatra_idx % 27) + 1  # 1-indexed, guard against 360.0 edge


def get_nakshatra_pada(moon_lon: float) -> int:
    """Return the Pada (quarter) of the current Nakshatra (1–4)."""
    pada_length = (360.0 / 27.0) / 4.0
    pada_idx = int(moon_lon / pada_length)
    return (pada_idx % 4) + 1


def get_yoga(sun_lon: float, moon_lon: float) -> int:
    """Compute Yoga index (1–27).

    Yoga = floor( ((Sun + Moon) mod 360°) / (360°/27) ) + 1
    """
    total = (sun_lon + moon_lon) % 360.0
    yoga_length = 360.0 / 27.0
    yoga_idx = int(total / yoga_length)
    return (yoga_idx % 27) + 1  # 1-indexed


def get_karana(sun_lon: float, moon_lon: float) -> tuple[int, str]:
    """Compute Karana index (1–60) and name.

    Karana = half a Tithi = 6° of Moon-Sun difference.
    Each lunar month has exactly 60 Karanas.
    Returns (index_1_based, karana_name).
    """
    diff = (moon_lon - sun_lon) % 360.0
    karana_index_0 = int(diff / 6.0)   # 0-indexed [0, 59]
    name = _get_karana_name_from_index(karana_index_0)
    return karana_index_0 + 1, name   # 1-indexed


def get_vara(julian_date: float) -> int:
    """Compute Vara (weekday) index.

    JD 0.5 = Monday; adding 0.5 shifts to noon-to-noon epochs.
    Returns 0 = Sunday, …, 6 = Saturday.
    """
    jd_int = math.floor(julian_date + 0.5)
    # JD 2451545.0 (J2000.0) = Saturday = 6
    # Check: 2451545 % 7 → and Saturday should be 6 in our scheme (0=Sun)
    # (2451545 + 1) % 7 = 2451546 % 7 = 0 → Sun? Let's verify:
    # Jan 1 2000 was a Saturday. jd_int for Jan1 2000 noon = 2451545.
    # We want that to map to 6 (Saturday).
    return int((jd_int + 1) % 7)   # 0=Sun, 6=Sat


def get_tithi_at_jd(jd: float, ayanamsa_name: str) -> int:
    sun_lon = get_planetary_longitude(jd, 'Sun', ayanamsa_name)
    moon_lon = get_planetary_longitude(jd, 'Moon', ayanamsa_name)
    return get_tithi(sun_lon, moon_lon)


def get_nakshatra_at_jd(jd: float, ayanamsa_name: str) -> int:
    moon_lon = get_planetary_longitude(jd, 'Moon', ayanamsa_name)
    return get_nakshatra(moon_lon)


def _find_exact_end_time(jd_start: float, get_index_func, current_index: int, ayanamsa_name: str, step_hours: float = 30.0, max_iter: int = 20) -> float:
    """Find the Julian Date when the given index (Tithi/Nakshatra) changes."""
    jd_end = jd_start + (step_hours / 24.0)
    # Check if it actually changed by jd_end
    if get_index_func(jd_end, ayanamsa_name) == current_index:
        jd_end += 12.0 / 24.0  # Step further if not changed
    
    low = jd_start
    high = jd_end
    
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        val = get_index_func(mid, ayanamsa_name)
        if val == current_index:
            low = mid
        else:
            high = mid
            
    return high


def get_ishta_kaala(jd_event: float, jd_sunrise: float) -> tuple[int, int]:
    """Convert an event JD into Ishta Kaala (Ghati-Pala) elapsed since sunrise."""
    if jd_event < jd_sunrise:
        return 0, 0
    diff_days = jd_event - jd_sunrise
    total_ghatis = diff_days * 60.0
    g = int(total_ghatis)
    p = int((total_ghatis - g) * 60.0)
    return g, p


# ---------------------------------------------------------------------------
# Aggregate Daily Panchang
# ---------------------------------------------------------------------------

def generate_daily_panchang(julian_date: float,
                             ayanamsa_name: str = 'Lahiri') -> dict:
    """Compute all five Panchang elements for a given Julian Day.

    Typically called with the JD corresponding to 05:30 IST (00:00 UTC).

    Returns a dict with Tithi, Nakshatra, Yoga, Karana, and Vara data.
    """
    sun_lon  = get_planetary_longitude(julian_date, 'Sun',  ayanamsa_name)
    moon_lon = get_planetary_longitude(julian_date, 'Moon', ayanamsa_name)

    tithi_idx   = get_tithi(sun_lon, moon_lon)
    nak_idx     = get_nakshatra(moon_lon)
    nak_pada    = get_nakshatra_pada(moon_lon)
    yoga_idx    = get_yoga(sun_lon, moon_lon)
    kar_idx, kar_name = get_karana(sun_lon, moon_lon)
    vara_idx    = get_vara(julian_date)

    tithi_end_jd = _find_exact_end_time(julian_date, get_tithi_at_jd, tithi_idx, ayanamsa_name)
    nak_end_jd = _find_exact_end_time(julian_date, get_nakshatra_at_jd, nak_idx, ayanamsa_name)

    return {
        'Tithi_Index':     tithi_idx,
        'Tithi_Name':      TITHI_NAMES[tithi_idx - 1],
        'Tithi_End_JD':    tithi_end_jd,
        'Nakshatra_Index': nak_idx,
        'Nakshatra_Name':  NAKSHATRA_NAMES[nak_idx - 1],
        'Nakshatra_Pada':  nak_pada,
        'Nakshatra_End_JD':nak_end_jd,
        'Yoga_Index':      yoga_idx,
        'Yoga_Name':       YOGA_NAMES[yoga_idx - 1],
        'Karana_Index':    kar_idx,
        'Karana_Name':     kar_name,
        'Vara_Index':      vara_idx,
        'Vara_Name':       VARA_NAMES[vara_idx],
    }
