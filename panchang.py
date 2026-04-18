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
from datetime import date, timedelta
from astronomy import get_planetary_longitude, get_sunrise, local_time_to_jd

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

# Hindu/Jain lunar month names (Sanskrit/formal and common colloquial forms).
# Index 0–11 corresponds to Sun Rashi index 0–11 (Mesha→Chaitra … Meena→Phalguna).
HINDU_MONTH_NAMES: list[str] = [
    "Chaitra", "Vaishakha", "Jyeshtha",  "Ashadha",
    "Shravana", "Bhadrapada", "Ashwin",  "Kartika",
    "Agrahayana", "Pausha",  "Magha",    "Phalguna",
]

HINDU_MONTH_COMMON_NAMES: dict[str, str] = {
    "Chaitra":    "Chaitra",
    "Vaishakha":  "Vaishakh",
    "Jyeshtha":   "Jeth",
    "Ashadha":    "Ashadh",
    "Shravana":   "Shravan",
    "Bhadrapada": "Bhadarvo",
    "Ashwin":     "Aaso",
    "Kartika":    "Kartak",
    "Agrahayana": "Maagsar",
    "Pausha":     "Posh",
    "Magha":      "Maha",
    "Phalguna":   "Faagan",
}


def get_hindu_month_from_sun_lon(sun_lon: float) -> tuple[str, str]:
    """Return (Sanskrit_name, common_name) for the Hindu lunar month.

    Derived from the Sun's sidereal longitude: the Sun Rashi index (0–11)
    maps directly to the lunar month index (Mesha→Chaitra, …, Meena→Phalguna).
    """
    idx = int(sun_lon / 30.0) % 12
    sanskrit = HINDU_MONTH_NAMES[idx]
    return sanskrit, HINDU_MONTH_COMMON_NAMES[sanskrit]


def _moon_sun_elongation(jd: float, ayanamsa: str = 'Lahiri') -> float:
    moon = get_planetary_longitude(jd, 'Moon', ayanamsa)
    sun = get_planetary_longitude(jd, 'Sun', ayanamsa)
    return (moon - sun) % 360.0


def find_new_moon_before(jd: float, ayanamsa: str = 'Lahiri') -> float:
    """Return JD of the most recent Amavasya (new moon) strictly before jd."""
    e = _moon_sun_elongation(jd, ayanamsa)
    centre = jd - e / 13.2
    lo = centre - 3.0
    prev_e = _moon_sun_elongation(lo, ayanamsa)
    for i in range(14):
        curr = lo + (i + 1) * 0.5
        curr_e = _moon_sun_elongation(curr, ayanamsa)
        if prev_e > 270.0 and curr_e < 90.0:
            a, b = lo + i * 0.5, curr
            for _ in range(50):
                mid = (a + b) / 2
                if _moon_sun_elongation(mid, ayanamsa) > 180.0:
                    a = mid
                else:
                    b = mid
            return b
        prev_e = curr_e
    raise ValueError(f"No new moon found before JD {jd}")


def find_new_moon_after(jd: float, ayanamsa: str = 'Lahiri') -> float:
    """Return JD of the next Amavasya (new moon) strictly after jd."""
    e = _moon_sun_elongation(jd, ayanamsa)
    centre = jd + (360.0 - e) / 13.2
    lo = centre - 3.0
    prev_e = _moon_sun_elongation(lo, ayanamsa)
    for i in range(14):
        curr = lo + (i + 1) * 0.5
        curr_e = _moon_sun_elongation(curr, ayanamsa)
        if prev_e > 270.0 and curr_e < 90.0:
            a, b = lo + i * 0.5, curr
            for _ in range(50):
                mid = (a + b) / 2
                if _moon_sun_elongation(mid, ayanamsa) > 180.0:
                    a = mid
                else:
                    b = mid
            if b > jd:
                return b
        prev_e = curr_e
    raise ValueError(f"No new moon found after JD {jd}")


def find_sankrantis_in_range(
    start_jd: float, end_jd: float, ayanamsa: str = 'Lahiri'
) -> list[int]:
    """Return zodiac sign indices (0–11) of all Sankrantis in (start_jd, end_jd].

    A Sankranti occurs when the Sun crosses a 30° boundary into a new sign.
    """
    results: list[int] = []
    step = 0.5
    t = start_jd
    prev_sign = int(get_planetary_longitude(t, 'Sun', ayanamsa) / 30.0) % 12
    t += step
    while t <= end_jd + step:
        curr_sign = int(get_planetary_longitude(t, 'Sun', ayanamsa) / 30.0) % 12
        if curr_sign != prev_sign:
            a, b = t - step, t
            for _ in range(50):
                mid = (a + b) / 2
                if int(get_planetary_longitude(mid, 'Sun', ayanamsa) / 30.0) % 12 == prev_sign:
                    a = mid
                else:
                    b = mid
            if start_jd < b <= end_jd:
                results.append(curr_sign)
            prev_sign = curr_sign
        t += step
    return results


def get_hindu_month(jd: float, ayanamsa: str = 'Lahiri') -> tuple[str, str, bool]:
    """Return (sanskrit_name, common_name, is_adhika) for the lunar month containing jd.

    Amanta rule: the month is named after the Sankranti (Sun sign ingress) that
    falls within the lunar month (prev Amavasya → next Amavasya).
    Zero Sankrantis in a month → Adhika (leap) masa, named after the next month's Sankranti.
    """
    prev_nm = find_new_moon_before(jd, ayanamsa)
    next_nm = find_new_moon_after(prev_nm + 1.0, ayanamsa)
    sankrantis = find_sankrantis_in_range(prev_nm, next_nm, ayanamsa)

    if sankrantis:
        name = HINDU_MONTH_NAMES[sankrantis[0]]
        return name, HINDU_MONTH_COMMON_NAMES[name], False

    next_next_nm = find_new_moon_after(next_nm + 1.0, ayanamsa)
    next_sankrantis = find_sankrantis_in_range(next_nm, next_next_nm, ayanamsa)
    if next_sankrantis:
        base = HINDU_MONTH_NAMES[next_sankrantis[0]]
        return f"Adhika {base}", f"Adhika {HINDU_MONTH_COMMON_NAMES[base]}", True

    sun_lon = get_planetary_longitude(jd, 'Sun', ayanamsa)
    base = HINDU_MONTH_NAMES[int(sun_lon / 30.0) % 12]
    return f"Adhika {base}", f"Adhika {HINDU_MONTH_COMMON_NAMES[base]}", True

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
JAIN_TITHI_OFFSET_DAYS = 144.0 / 1440.0


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


def get_vara_from_date(local_date: date) -> int:
    """Return the weekday index for a local civil date.

    Python's weekday() uses Monday=0..Sunday=6, while Vara uses
    Sunday=0..Saturday=6.
    """
    return int((local_date.weekday() + 1) % 7)


def get_tithi_at_jd(jd: float, ayanamsa_name: str) -> int:
    sun_lon = get_planetary_longitude(jd, 'Sun', ayanamsa_name)
    moon_lon = get_planetary_longitude(jd, 'Moon', ayanamsa_name)
    return get_tithi(sun_lon, moon_lon)


def get_karana_index_at_jd(jd: float, ayanamsa_name: str) -> int:
    sun_lon = get_planetary_longitude(jd, 'Sun', ayanamsa_name)
    moon_lon = get_planetary_longitude(jd, 'Moon', ayanamsa_name)
    idx, _ = get_karana(sun_lon, moon_lon)
    return idx


def get_nakshatra_at_jd(jd: float, ayanamsa_name: str) -> int:
    moon_lon = get_planetary_longitude(jd, 'Moon', ayanamsa_name)
    return get_nakshatra(moon_lon)


def get_yoga_at_jd(jd: float, ayanamsa_name: str) -> int:
    sun_lon = get_planetary_longitude(jd, 'Sun', ayanamsa_name)
    moon_lon = get_planetary_longitude(jd, 'Moon', ayanamsa_name)
    return get_yoga(sun_lon, moon_lon)


def _find_exact_end_time(
    jd_start: float,
    get_index_func,
    current_index: int,
    ayanamsa_name: str,
    low_guess: float | None = None,
    high_guess: float | None = None,
    max_iter: int = 25,
) -> float:
    """Find the Julian Date when the given index (Tithi/Nakshatra) changes."""
    low = low_guess if low_guess is not None else jd_start
    high = high_guess if high_guess is not None else jd_start + (30.0 / 24.0)

    # Ensure low is still within the current element.
    if get_index_func(low, ayanamsa_name) != current_index:
        low = jd_start
        if get_index_func(low, ayanamsa_name) != current_index:
            raise ValueError("Starting JD is not within the current Panchang element.")

    # Ensure high is on the far side of the boundary before bisection.
    while get_index_func(high, ayanamsa_name) == current_index:
        high += 12.0 / 24.0
        if high - jd_start > 3.0:
            raise ValueError("Could not bracket Panchang element end time within 3 days.")
        
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        val = get_index_func(mid, ayanamsa_name)
        if val == current_index:
            low = mid
        else:
            high = mid
            
        # Early exit if window < 1 second (1/86400 days ≈ 0.0000115)
        if (high - low) < 0.00001:
            break
            
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


def calculate_tithi_details(
    julian_date: float,
    ayanamsa_name: str = 'Lahiri',
    sun_lon: float | None = None,
    moon_lon: float | None = None,
    key_prefix: str = 'Tithi',
) -> dict:
    """Compute the Tithi active at a specific JD and its end time."""
    if sun_lon is None:
        sun_lon = get_planetary_longitude(julian_date, 'Sun', ayanamsa_name)
    if moon_lon is None:
        moon_lon = get_planetary_longitude(julian_date, 'Moon', ayanamsa_name)

    tithi_idx = get_tithi(sun_lon, moon_lon)
    diff = (moon_lon - sun_lon) % 360.0
    tithi_left_deg = 12.0 - (diff % 12.0)
    tithi_low = julian_date + (tithi_left_deg / 15.0)
    tithi_high = julian_date + (tithi_left_deg / 10.0) + 0.05
    tithi_end_jd = _find_exact_end_time(
        julian_date,
        get_tithi_at_jd,
        tithi_idx,
        ayanamsa_name,
        tithi_low,
        tithi_high,
    )

    return {
        f'{key_prefix}_Index': tithi_idx,
        f'{key_prefix}_Name': TITHI_NAMES[tithi_idx - 1],
        f'{key_prefix}_End_JD': tithi_end_jd,
    }


def calculate_jain_tithi_from_sunrise(
    sunrise_jd: float,
    ayanamsa_name: str = 'Lahiri',
) -> dict:
    """Compute Jain Tithi from the Tithi active 2h24m after sunrise."""
    reference_jd = sunrise_jd + JAIN_TITHI_OFFSET_DAYS
    result = calculate_tithi_details(reference_jd, ayanamsa_name, key_prefix='Jain_Tithi')
    result['Jain_Tithi_Reference_JD'] = reference_jd
    return result


def calculate_yoga_details(
    julian_date: float,
    ayanamsa_name: str = 'Lahiri',
    sun_lon: float | None = None,
    moon_lon: float | None = None,
) -> dict:
    """Compute the Yoga active at a specific JD and its end time."""
    if sun_lon is None:
        sun_lon = get_planetary_longitude(julian_date, 'Sun', ayanamsa_name)
    if moon_lon is None:
        moon_lon = get_planetary_longitude(julian_date, 'Moon', ayanamsa_name)

    yoga_idx = get_yoga(sun_lon, moon_lon)
    yoga_length = 360.0 / 27.0
    total = (sun_lon + moon_lon) % 360.0
    yoga_left_deg = yoga_length - (total % yoga_length)
    yoga_low = julian_date + (yoga_left_deg / 30.0)
    yoga_high = julian_date + (yoga_left_deg / 20.0) + 0.05
    yoga_end_jd = _find_exact_end_time(
        julian_date,
        get_yoga_at_jd,
        yoga_idx,
        ayanamsa_name,
        yoga_low,
        yoga_high,
    )

    return {
        'Yoga_Index': yoga_idx,
        'Yoga_Name': YOGA_NAMES[yoga_idx - 1],
        'Yoga_End_JD': yoga_end_jd,
    }


def calculate_karana_details(
    julian_date: float,
    ayanamsa_name: str = 'Lahiri',
    sun_lon: float | None = None,
    moon_lon: float | None = None,
) -> dict:
    """Compute the Karana active at a specific JD and its start/end times.

    Uses the same bisection approach as calculate_tithi_details but for 6°
    intervals (half a Tithi).  Both start and end are returned as Julian Dates.
    """
    if sun_lon is None:
        sun_lon = get_planetary_longitude(julian_date, 'Sun', ayanamsa_name)
    if moon_lon is None:
        moon_lon = get_planetary_longitude(julian_date, 'Moon', ayanamsa_name)

    karana_idx, karana_name = get_karana(sun_lon, moon_lon)
    diff = (moon_lon - sun_lon) % 360.0

    # Degrees remaining until next 6° boundary → end time
    karana_left_deg = 6.0 - (diff % 6.0)
    karana_end_jd = _find_exact_end_time(
        julian_date,
        get_karana_index_at_jd,
        karana_idx,
        ayanamsa_name,
        low_guess=julian_date + (karana_left_deg / 15.0),
        high_guess=julian_date + (karana_left_deg / 10.0) + 0.05,
    )

    # Degrees already elapsed since last 6° boundary → start time
    karana_elapsed_deg = diff % 6.0
    prev_karana_idx = ((karana_idx - 2) % 60) + 1  # wrap within 1-based [1,60]
    karana_start_jd = _find_exact_end_time(
        julian_date - (karana_elapsed_deg / 10.0) - 0.05,
        get_karana_index_at_jd,
        prev_karana_idx,
        ayanamsa_name,
        low_guess=julian_date - (karana_elapsed_deg / 10.0) - 0.05,
        high_guess=julian_date,
    )

    return {
        'Karana_Index': karana_idx,
        'Karana_Name': karana_name,
        'Karana_Start_JD': karana_start_jd,
        'Karana_End_JD': karana_end_jd,
    }


# ---------------------------------------------------------------------------
# Aggregate Daily Panchang
# ---------------------------------------------------------------------------

def generate_daily_panchang(
    julian_date: float,
    ayanamsa_name: str = 'Lahiri',
    sun_lon: float | None = None,
    moon_lon: float | None = None,
    local_date: date | None = None,
) -> dict:
    """Compute all five Panchang elements for a given Julian Day.

    Typically called with the JD corresponding to 05:30 IST (00:00 UTC).

    Returns a dict with Tithi, Nakshatra, Yoga, Karana, and Vara data.
    """
    if sun_lon is None:
        sun_lon  = get_planetary_longitude(julian_date, 'Sun',  ayanamsa_name)
    if moon_lon is None:
        moon_lon = get_planetary_longitude(julian_date, 'Moon', ayanamsa_name)

    tithi_data = calculate_tithi_details(julian_date, ayanamsa_name, sun_lon=sun_lon, moon_lon=moon_lon)
    nak_idx    = get_nakshatra(moon_lon)
    nak_pada    = get_nakshatra_pada(moon_lon)
    karana_data = calculate_karana_details(julian_date, ayanamsa_name, sun_lon=sun_lon, moon_lon=moon_lon)
    vara_idx    = get_vara_from_date(local_date) if local_date is not None else get_vara(julian_date)
    yoga_data = calculate_yoga_details(julian_date, ayanamsa_name, sun_lon=sun_lon, moon_lon=moon_lon)

    # Compute tight bounds for Nakshatra
    nak_len = 360.0 / 27.0
    nak_left_deg = nak_len - (moon_lon % nak_len)
    nak_low = julian_date + (nak_left_deg / 16.0)
    nak_high = julian_date + (nak_left_deg / 11.0) + 0.05

    nak_end_jd = _find_exact_end_time(julian_date, get_nakshatra_at_jd, nak_idx, ayanamsa_name, nak_low, nak_high)

    return {
        **tithi_data,
        'Nakshatra_Index': nak_idx,
        'Nakshatra_Name':  NAKSHATRA_NAMES[nak_idx - 1],
        'Nakshatra_Pada':  nak_pada,
        'Nakshatra_End_JD':nak_end_jd,
        **yoga_data,
        **karana_data,
        'Vara_Index':      vara_idx,
        'Vara_Name':       VARA_NAMES[vara_idx],
    }


# ---------------------------------------------------------------------------
# Samvat (Traditional Year) Calculations
# ---------------------------------------------------------------------------

def get_vikram_samvat(gregorian_date: date, chaitra_shukla_1_date: date) -> int:
    """Return the Vikram Samvat year for a given Gregorian date.

    The VS new year starts on Chaitra Shukla Pratipada (the first day of the
    bright fortnight of Chaitra).  Dates on or after that day use year + 57;
    dates before it use year + 56.
    """
    if gregorian_date >= chaitra_shukla_1_date:
        return gregorian_date.year + 57
    return gregorian_date.year + 56


def get_vira_nirvana_samvat(gregorian_date: date, diwali_date: date) -> int:
    """Return the Vira Nirvana Samvat year for a given Gregorian date.

    The VNS new year starts the day after Diwali (Kartik Krishna Amavasya).
    Dates strictly after Diwali use year + 527; dates on or before use year + 526.
    """
    if gregorian_date > diwali_date:
        return gregorian_date.year + 527
    return gregorian_date.year + 526


def _find_tithi_in_range(
    year: int,
    start_month: int,
    start_day: int,
    search_days: int,
    target_tithi: int,
    lat: float,
    lon: float,
    tz_offset: float,
    ayanamsa_name: str,
) -> date:
    """Scan a date range and return the first day whose sunrise Tithi matches.

    Uses the Udaya Tithi rule: Tithi evaluated at local sunrise determines the day.
    The search windows are chosen so that only one occurrence of the target
    Tithi exists in each window (no month-name filter is required).
    """
    for i in range(search_days):
        d = date(year, start_month, start_day) + timedelta(days=i)
        jd_start = local_time_to_jd(d.year, d.month, d.day, 0.0, tz_offset)
        jd_sr = get_sunrise(jd_start, lat, lon)
        sun_lon = get_planetary_longitude(jd_sr, 'Sun', ayanamsa_name)
        moon_lon = get_planetary_longitude(jd_sr, 'Moon', ayanamsa_name)
        if get_tithi(sun_lon, moon_lon) == target_tithi:
            return d
    raise ValueError(
        f"Could not find Tithi={target_tithi} in {year}-{start_month:02d}-{start_day:02d} "
        f"+ {search_days} days"
    )


def find_chaitra_shukla_1(
    year: int,
    lat: float,
    lon: float,
    tz_offset: float = 5.5,
    ayanamsa_name: str = 'Lahiri',
) -> date:
    """Return the Gregorian date of Chaitra Shukla Pratipada for the given year.

    In the amanta system, Chaitra Shukla Pratipada is defined as the civil day
    immediately after the Phalguna Amavasya — regardless of whether the Udaya
    Tithi at sunrise is 1 (Pratipada can be skipped when the New Moon falls
    very close to sunrise, as in 2026 where March 19 Amavasya jumps directly
    to Tithi=2 on March 20).

    The Phalguna Amavasya is the FIRST Tithi=30 in the March 1 – April 22
    window (52 days). In most years there is only one Amavasya in this range;
    in years with two (e.g. 2026: March 19 and April 17), the first one is
    always the Phalguna Amavasya.
    """
    phalguna_amavasya = _find_tithi_in_range(
        year, 3, 1, 52, 30, lat, lon, tz_offset, ayanamsa_name
    )
    return phalguna_amavasya + timedelta(days=1)


def find_diwali(
    year: int,
    lat: float,
    lon: float,
    tz_offset: float = 5.5,
    ayanamsa_name: str = 'Lahiri',
) -> date:
    """Return the Gregorian date of Diwali (Kartik Krishna Amavasya) for the given year.

    The Kartika Amavasya (Diwali) is identified as the first Amavasya (Tithi=30)
    in the October 10 – November 25 window where the Sun's sidereal longitude
    is ≥ 179°.  This threshold cleanly separates Diwali from the preceding
    Ashwin Amavasya (Mahalaya, max Sun ~178°) and avoids the subsequent
    Margashirsha Amavasya (min Sun ~213°).

    When there are two Amavasyas in the window (e.g. 2026: Ashwin Oct 10 at
    172.5°, Diwali Nov 9 at 202.4°), the Ashwin one is excluded by the
    sun-longitude filter and Diwali is returned as the first qualifying match.
    """
    for i in range(46):  # Oct 10 – Nov 24 inclusive
        d = date(year, 10, 10) + timedelta(days=i)
        jd_start = local_time_to_jd(d.year, d.month, d.day, 0.0, tz_offset)
        jd_sr = get_sunrise(jd_start, lat, lon)
        sun_lon = get_planetary_longitude(jd_sr, 'Sun', ayanamsa_name)
        moon_lon = get_planetary_longitude(jd_sr, 'Moon', ayanamsa_name)
        if get_tithi(sun_lon, moon_lon) == 30 and sun_lon >= 179.0:
            return d
    raise ValueError(f"Could not find Diwali (Kartika Amavasya) for year {year}")
