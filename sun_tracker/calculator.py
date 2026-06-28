import os
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from skyfield.api import load
import swisseph as swe

from sun_tracker.cities import CITIES

# Resolve ephemeris data directory for JPL planetary data files
import sys as _sys
try:
    _EPHE_BASE = _sys._MEIPASS
except AttributeError:
    _EPHE_BASE = os.path.dirname(os.path.abspath(__file__))
_EPHE_DIR = os.path.join(_EPHE_BASE, 'ephe')
swe.set_ephe_path(_EPHE_DIR)

# Calibrated Lahiri Ayanamsa (Indian Astronomical Ephemeris reference).
# SIDM_USER with t0 = J2000.0 (JD 2451545.0) and ayan_t0 = 23.857102694767°
# produces 24° 13' 13.10" at Jan 1, 2026 00:00 IST, matching IAE values.
_LAHIRI_T0 = 2451545.0
_LAHIRI_AYAN_T0 = 23.857102694767

def _set_lahiri_mode() -> None:
    """Set Swiss Ephemeris to use calibrated Lahiri ayanamsa."""
    swe.set_sid_mode(swe.SIDM_USER, _LAHIRI_T0, _LAHIRI_AYAN_T0)

RASHI_NAMES = [
    "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"
]

def get_ayanamsa_dm(jd: float) -> str:
    """Calculate Lahiri Ayanamsa at Julian Date `jd` and return formatted as D° MM' SS.SS"."""
    _set_lahiri_mode()
    val = swe.get_ayanamsa_ut(jd)
    d = int(val)
    m_dec = (val - d) * 60.0
    m = int(m_dec)
    s = (m_dec - m) * 60.0
    return f"{d}° {m:02d}' {s:05.2f}\""

def jd_to_datetime_utc(jd: float) -> datetime:
    """Convert Julian Date to a timezone-aware UTC datetime."""
    y, m, d, h = swe.revjul(jd)
    h_int = int(h)
    m_dec = (h - h_int) * 60.0
    m_int = int(m_dec)
    s_dec = (m_dec - m_int) * 60.0
    s_int = int(round(s_dec))
    # Handle possible rounding overflows (e.g. s_int = 60)
    dt = datetime(y, m, d, h_int, m_int, 0, tzinfo=timezone.utc)
    return dt + timedelta(seconds=s_int)

def find_crossing_time_sidereal(t1_jd: float, t2_jd: float, target_arcminute: int) -> float:
    """Find the precise JD where the Sun's Lahiri sidereal longitude crosses target_arcminute / 60."""
    target_lon = target_arcminute / 60.0
    low = t1_jd
    high = t2_jd
    _set_lahiri_mode()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    
    for _ in range(12):
        mid = (low + high) / 2.0
        res, _ = swe.calc_ut(mid, swe.SUN, flags)
        lon_mid = res[0] % 360.0
        
        diff = (lon_mid - target_lon + 180.0) % 360.0 - 180.0
        if diff < 0.0:
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0

def run_calculation(year: int, city_name: str, progress_callback=None) -> list[dict]:
    """Calculate all Sun crossings for the given year and city using Skyfield."""
    # 1. Retrieve City Info
    city_info = CITIES[city_name]
    tz_name = city_info["tz"]
    tz = ZoneInfo(tz_name)
    
    # 2. Setup Year Range in Local Time
    start_dt_local = datetime(year, 1, 1, 0, 0, 0, tzinfo=tz)
    end_dt_local = datetime(year, 12, 31, 23, 59, 0, tzinfo=tz)
    
    # Total minutes to scan
    delta = end_dt_local - start_dt_local
    total_minutes = int(delta.total_seconds() / 60) + 1
    
    # 3. Initialize Skyfield
    if progress_callback:
        progress_callback("Loading Ephemeris...", 5)
        
    # Use built-in timescale data to run completely offline without downloading deltat/leap seconds files
    ts = load.timescale(builtin=True)
    
    # Resolve resource path for PyInstaller compatibility
    import sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    eph_path = os.path.join(base_path, 'de421.bsp')
    eph = load(eph_path)
    earth = eph['earth']
    sun = eph['sun']
    
    # 4. Generate Minutes Array and Timescale Array
    if progress_callback:
        progress_callback("Generating timescales...", 15)
        
    minutes = np.arange(total_minutes)
    start_utc = start_dt_local.astimezone(timezone.utc)
    
    # Skyfield handles overflows of minutes automatically
    t_array = ts.utc(
        start_utc.year,
        start_utc.month,
        start_utc.day,
        start_utc.hour,
        start_utc.minute + minutes
    )
    
    # 5. Compute Ecliptic Coordinates Vector (J2000)
    if progress_callback:
        progress_callback("Calculating Sun positions...", 30)
        
    astrometric = earth.at(t_array).observe(sun)
    apparent = astrometric.apparent()
    
    if progress_callback:
        progress_callback("Extracting J2000 longitudes...", 45)
        
    _, lon_j2000, _ = apparent.ecliptic_latlon()
    lons_j2000 = lon_j2000.degrees
    
    # Calculate daily samples to interpolate precession/nutation difference (J2000 to epoch of date)
    if progress_callback:
        progress_callback("Correcting for precession/nutation...", 52)
        
    day_indices = np.arange(0, total_minutes, 1440)
    if len(day_indices) == 0 or day_indices[-1] != total_minutes - 1:
        day_indices = np.append(day_indices, total_minutes - 1)
        
    t_days = t_array[day_indices]
    astrometric_days = earth.at(t_days).observe(sun).apparent()
    _, lon_days_date, _ = astrometric_days.ecliptic_latlon(epoch=t_days)
    _, lon_days_j2000, _ = astrometric_days.ecliptic_latlon()
    diffs_days = (lon_days_date.degrees - lon_days_j2000.degrees + 180) % 360 - 180
    
    # Interpolate to all minutes
    diffs_prec = np.interp(np.arange(total_minutes), day_indices, diffs_days)
    lons = (lons_j2000 + diffs_prec) % 360.0
    
    # Calculate Ayanamsa linear interpolation across the year for speed
    if progress_callback:
        progress_callback("Calculating Ayanamsa...", 60)
        
    jd_start = t_array[0].ut1
    jd_end = t_array[-1].ut1
    _set_lahiri_mode()
    ayan_start = swe.get_ayanamsa_ut(jd_start)
    ayan_end = swe.get_ayanamsa_ut(jd_end)
    ayanamsas = np.linspace(ayan_start, ayan_end, total_minutes)
    
    # Calculate Sidereal (Nirayana) Longitude
    sidereal_lons = (lons - ayanamsas) % 360.0
    
    # 6. Detect Arcminute Crossing Boundaries (on Sidereal Longitude)
    if progress_callback:
        progress_callback("Checking for crossings...", 80)
        
    arcminutes = np.floor(sidereal_lons * 60.0).astype(np.int32)
    diffs = np.diff(arcminutes)
    
    # Crossing occurs between idx and idx+1
    crossing_indices = np.where(diffs != 0)[0]
    
    # 7. Collect Rows
    if progress_callback:
        progress_callback("Constructing final dataset...", 90)
        
    rows = []
    total_crossings = len(crossing_indices)
    
    for idx_in_crossings, idx in enumerate(crossing_indices):
        crossing_idx = idx + 1
        t1_jd = t_array[idx].ut1
        t2_jd = t_array[crossing_idx].ut1
        
        # Target arcminute crossed into
        deg_float = sidereal_lons[crossing_idx]
        target_arcminute = int(math.floor(deg_float * 60.0))
        
        # Pinpoint exact crossing time using C-level Swiss Ephemeris bisection
        jd_cross = find_crossing_time_sidereal(t1_jd, t2_jd, target_arcminute)
        dt_utc = jd_to_datetime_utc(jd_cross)
        dt_local = dt_utc.astimezone(tz)
        
        # Degrees division
        deg = target_arcminute // 60
        rashi_idx = deg // 30
        ansha = deg % 30
        kala = target_arcminute % 60
        vikala = 0
        
        rashi_name = RASHI_NAMES[rashi_idx]
        
        # Ayanamsa at exact crossing moment
        ayan_str = get_ayanamsa_dm(jd_cross)
        
        rows.append({
            "Date": dt_local.strftime("%Y-%m-%d"),
            "Time": dt_local.strftime("%H:%M:%S"),  # HH:MM:SS format
            "Rashi": rashi_name,
            "Ansha": ansha,
            "Kala": kala,
            "Vikala": vikala,
            "Ayanamsa_DM": ayan_str
        })
        
    return rows
