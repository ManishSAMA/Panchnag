"""
astronomy.py — Core Swiss Ephemeris wrapper for the Panchang Generator.

Provides:
  - Julian Date conversion
  - Ayanamsa retrieval (Lahiri, Raman, Krishnamurti)
  - Nirayana (sidereal) planet longitudes with DMS formatting
  - Sunrise / Sunset / Moonrise / Moonset calculation
  - Julian Day → local time string conversion
"""

import swisseph as swe
import math

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
# Point to ephemeris files if available; empty string → built-in Moshier
swe.set_ephe_path('')

# ---------------------------------------------------------------------------
# Constants & Mappings
# ---------------------------------------------------------------------------
AYANAMSA_SYSTEMS: dict[str, int] = {
    'Lahiri':       swe.SIDM_LAHIRI,
    'Raman':        swe.SIDM_RAMAN,
    'Krishnamurti': swe.SIDM_KRISHNAMURTI,
}

PLANETS: dict[str, int] = {
    'Sun':     swe.SUN,
    'Moon':    swe.MOON,
    'Mars':    swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus':   swe.VENUS,
    'Saturn':  swe.SATURN,
    'Rahu':    swe.TRUE_NODE,   # True Lunar North Node (more accurate)
    # Ketu is computed as Rahu + 180°
}

# ---------------------------------------------------------------------------
# Julian Date helpers
# ---------------------------------------------------------------------------

def get_julian_date(year: int, month: int, day: int, hour_utc: float) -> float:
    """Return the Julian Day Number for a given UTC datetime.

    Args:
        year, month, day: Calendar date.
        hour_utc: Time in UTC as a decimal fraction (e.g., 5.5 = 05:30 UTC).
    """
    return swe.julday(year, month, day, hour_utc)


def local_time_to_jd(year: int, month: int, day: int,
                     local_hour: float, tz_offset: float = 5.5) -> float:
    """Convert a local time to Julian Day (UTC-based).

    Args:
        local_hour:  Local clock time as a decimal (e.g., 5.5 = 05:30).
        tz_offset:   Hours east of UTC (default 5.5 = IST).
    """
    hour_utc = local_hour - tz_offset
    # Handle crossing into the previous or next UTC day
    delta_days = 0
    if hour_utc < 0:
        hour_utc += 24.0
        delta_days = -1
    elif hour_utc >= 24.0:
        hour_utc -= 24.0
        delta_days = 1
    jd = swe.julday(year, month, day, hour_utc)
    return jd + delta_days


# ---------------------------------------------------------------------------
# Ayanamsa
# ---------------------------------------------------------------------------

def get_ayanamsa(julian_date: float, ayanamsa_name: str = 'Lahiri') -> float:
    """Return the ayanamsa value in decimal degrees for the given JD."""
    sid_mode = AYANAMSA_SYSTEMS.get(ayanamsa_name, swe.SIDM_LAHIRI)
    swe.set_sid_mode(sid_mode, 0, 0)
    return swe.get_ayanamsa_ut(julian_date)


# ---------------------------------------------------------------------------
# Planetary Positions
# ---------------------------------------------------------------------------

def _set_sidereal_mode(ayanamsa_name: str) -> None:
    """Internal helper: set sidereal mode before a calculation."""
    sid_mode = AYANAMSA_SYSTEMS.get(ayanamsa_name, swe.SIDM_LAHIRI)
    swe.set_sid_mode(sid_mode, 0, 0)


def get_planetary_longitude(julian_date: float,
                             planet_name: str,
                             ayanamsa_name: str = 'Lahiri') -> float:
    """Return the Nirayana (sidereal) longitude of a planet in decimal degrees.

    Uses geocentric apparent positions with high-precision Swiss Ephemeris mode.

    Args:
        julian_date:   Julian Day Number (UT).
        planet_name:   One of 'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
                       'Venus', 'Saturn', 'Rahu', 'Ketu'.
        ayanamsa_name: Ayanamsa system to use.

    Returns:
        Longitude in decimal degrees [0, 360).
    """
    if planet_name == 'Ketu':
        rahu_lon = get_planetary_longitude(julian_date, 'Rahu', ayanamsa_name)
        return (rahu_lon + 180.0) % 360.0

    planet_id = PLANETS[planet_name]
    _set_sidereal_mode(ayanamsa_name)

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    res, _err = swe.calc_ut(julian_date, planet_id, flags)
    return res[0] % 360.0


def get_all_planet_positions(julian_date: float,
                              ayanamsa_name: str = 'Lahiri') -> dict[str, float]:
    """Return sidereal longitudes for all 9 Vedic grahas.

    Returns:
        Dict mapping planet name → decimal degrees.
    """
    _set_sidereal_mode(ayanamsa_name)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    result: dict[str, float] = {}
    for name, pid in PLANETS.items():
        res, _err = swe.calc_ut(julian_date, pid, flags)
        result[name] = res[0] % 360.0

    # Ketu = Rahu + 180°
    result['Ketu'] = (result['Rahu'] + 180.0) % 360.0
    return result


# ---------------------------------------------------------------------------
# DMS formatting
# ---------------------------------------------------------------------------

def decimal_to_dms(decimal_degrees: float) -> tuple[int, int, float]:
    """Convert decimal degrees → (degrees, minutes, seconds)."""
    d = int(decimal_degrees)
    m_dec = (decimal_degrees - d) * 60.0
    m = int(m_dec)
    s = (m_dec - m) * 60.0
    return d, m, s


def format_dms(decimal_degrees: float) -> str:
    """Return a human-readable DMS string, e.g. '123° 45′ 06.78″'."""
    d, m, s = decimal_to_dms(decimal_degrees)
    return f"{d:3d}° {m:02d}' {s:05.2f}\""


def get_rashi_name(decimal_degrees: float) -> str:
    """Return the Rashi (zodiac sign) name for a given sidereal longitude."""
    RASHI_NAMES = [
        "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
        "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)",
        "Tula (Libra)", "Vrishchika (Scorpio)", "Dhanu (Sagittarius)",
        "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
    ]
    idx = int(decimal_degrees / 30.0) % 12
    return RASHI_NAMES[idx]


# ---------------------------------------------------------------------------
# Rise / Set calculations
# ---------------------------------------------------------------------------

def _rise_set(julian_date: float, body: int,
              lat: float, lon: float,
              is_rise: bool) -> float:
    """Internal: compute rise or set JD for a celestial body.

    Args:
        julian_date: JD used as search start.
        body:        Swiss Ephemeris body constant.
        lat, lon:    Geographic coordinates (degrees, positive north/east).
        is_rise:     True → rise time; False → set time.

    Returns:
        Julian Day of the event, or 0.0 on failure.
    """
    geopos = (lon, lat, 0.0)       # (longitude, latitude, altitude_m)

    # Start from 00:00 UTC of the given calendar day
    # swe.julday gives JD at 12:00 UTC (noon), subtract 0.5 to get midnight
    y, m, d, _ = swe.revjul(julian_date, swe.GREG_CAL)
    jd_start = swe.julday(y, m, d, 0.0)   # 00:00 UTC of that date

    rsmi = swe.CALC_RISE if is_rise else swe.CALC_SET
    rsmi |= swe.BIT_DISC_CENTER

    try:
        # pyswisseph 2.10.x signature:
        # rise_trans(tjdut, body, rsmi, geopos, atpress=0, attemp=0, flags=FLG_SWIEPH)
        # Note: no star_name argument in this version
        ret, tret = swe.rise_trans(
            jd_start,
            body,
            rsmi,
            geopos,
            1013.25,
            15.0,
        )
        if ret == 0 and tret[0] > 0:
            return tret[0]
    except Exception:
        pass

    # Fallback without disc-center correction
    try:
        rsmi2 = swe.CALC_RISE if is_rise else swe.CALC_SET
        ret, tret = swe.rise_trans(jd_start, body, rsmi2, geopos, 1013.25, 15.0)
        if ret == 0 and tret[0] > 0:
            return tret[0]
    except Exception:
        pass

    return 0.0


def get_sunrise(julian_date: float, lat: float, lon: float) -> float:
    """Return Julian Day of sunrise for the given date and location."""
    return _rise_set(julian_date, swe.SUN, lat, lon, is_rise=True)


def get_sunset(julian_date: float, lat: float, lon: float) -> float:
    """Return Julian Day of sunset for the given date and location."""
    return _rise_set(julian_date, swe.SUN, lat, lon, is_rise=False)


def get_moonrise(julian_date: float, lat: float, lon: float) -> float:
    """Return Julian Day of moonrise for the given date and location."""
    return _rise_set(julian_date, swe.MOON, lat, lon, is_rise=True)


def get_moonset(julian_date: float, lat: float, lon: float) -> float:
    """Return Julian Day of moonset for the given date and location."""
    return _rise_set(julian_date, swe.MOON, lat, lon, is_rise=False)


# ---------------------------------------------------------------------------
# Time Conversion
# ---------------------------------------------------------------------------

def jd_to_local_time_string(jd: float, tz_offset: float = 5.5) -> str:
    """Convert a Julian Day to a local time string HH:MM:SS.

    Args:
        jd:         Julian Day Number.
        tz_offset:  Hours east of UTC (default 5.5 = IST UTC+5:30).

    Returns:
        Local time string like '07:18:34', or '--:--:--' on failure.
    """
    if jd == 0.0:
        return '--:--:--'
    try:
        _y, _m, _d, h_utc = swe.revjul(jd, swe.GREG_CAL)
        h_local = h_utc + tz_offset
        # Handle overflow across midnight
        h_local = h_local % 24.0
        hh = int(h_local)
        mm_float = (h_local - hh) * 60.0
        mm = int(mm_float)
        ss = int((mm_float - mm) * 60.0)
        return f"{hh:02d}:{mm:02d}:{ss:02d}"
    except Exception:
        return '--:--:--'


# Backward-compatible alias used by old callers
def jd_to_ist_string(jd: float) -> str:
    """Convert a Julian Day to IST (UTC+5:30) time string."""
    return jd_to_local_time_string(jd, tz_offset=5.5)
