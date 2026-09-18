import math
from datetime import datetime, timedelta, timezone
import swisseph as swe

# Ensure Swiss Ephemeris uses Moshier built-in ephemeris if no paths are set
swe.set_ephe_path('')

def get_sun_longitude_tropical(jd: float, topo_coords: tuple[float, float, float] | None = None) -> float:
    """Calculate the tropical longitude of the Sun at Julian Date `jd`.
    
    If `topo_coords` (longitude, latitude, altitude_meters) is provided,
    computes the topocentric position. Otherwise, computes the geocentric position.
    """
    if topo_coords is not None:
        lon, lat, alt = topo_coords
        swe.set_topo(lon, lat, alt)
        flags = swe.FLG_SWIEPH | swe.FLG_TOPOCTR
    else:
        flags = swe.FLG_SWIEPH
        
    res, _ = swe.calc_ut(jd, swe.SUN, flags)
    return res[0] % 360.0

def get_ayanamsa_dm(jd: float) -> str:
    """Calculate Lahiri Ayanamsa at Julian Date `jd` and return as a 'D° MM'' string."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    val = swe.get_ayanamsa_ut(jd)
    d = int(val)
    m = int(round((val - d) * 60.0))
    if m >= 60:
        d += 1
        m -= 60
    return f"{d}° {m:02d}'"

def find_crossing_time(t1: float, t2: float, target_arcminute: int, topo_coords: tuple[float, float, float] | None = None) -> float:
    """Find the precise Julian Date between t1 and t2 where the Sun's tropical
    longitude crosses target_arcminute / 60.0 degrees.
    """
    target_lon = target_arcminute / 60.0
    
    low = t1
    high = t2
    for _ in range(14):
        mid = (low + high) / 2.0
        lon_mid = get_sun_longitude_tropical(mid, topo_coords)
        # Difference from target_lon, handling 360 wrap-around
        diff = (lon_mid - target_lon + 180.0) % 360.0 - 180.0
        if diff < 0.0:
            low = mid
        else:
            high = mid
            
    return (low + high) / 2.0

def jd_to_datetime_utc(jd: float) -> datetime:
    """Convert Julian Date to a UTC datetime."""
    y, m, d, h_utc = swe.revjul(jd, swe.GREG_CAL)
    # Safely add hours as timedelta to avoid overflow errors in datetime constructor
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(hours=h_utc)

def datetime_to_jd(dt: datetime) -> float:
    """Convert a timezone-aware datetime to Julian Date (UTC)."""
    utc_dt = dt.astimezone(timezone.utc)
    hour_utc = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0 + utc_dt.microsecond / 3.6e9
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_utc)

def generate_transit_events(start_dt: datetime, end_dt: datetime, topo_coords: tuple[float, float, float] | None = None):
    """Generate all transit events where the Sun's tropical longitude crosses
    any integer arcminute boundary in the period [start_dt, end_dt].
    
    Yields dicts of:
        {
            'jd': float,
            'dt': datetime (UTC-aware),
            'degree': int,
            'minute': int
        }
    """
    # Ensure datetimes are timezone-aware
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
        
    jd_start = datetime_to_jd(start_dt)
    jd_end = datetime_to_jd(end_dt)
    
    # Step hour by hour (1/24.0 of a day)
    step = 1.0 / 24.0
    
    t_current = jd_start
    lon_curr = get_sun_longitude_tropical(t_current, topo_coords)
    a_curr = int(math.floor(lon_curr * 60.0))
    
    while t_current < jd_end:
        t_next = min(t_current + step, jd_end)
        lon_next = get_sun_longitude_tropical(t_next, topo_coords)
        a_next = int(math.floor(lon_next * 60.0))
        
        if a_next != a_curr:
            # Crossings occurred in this interval
            targets = []
            if a_next > a_curr:
                targets = list(range(a_curr + 1, a_next + 1))
            else:
                # Wrap-around from 359*60 + 59 to 0
                targets = list(range(a_curr + 1, 21600)) + list(range(0, a_next + 1))
                
            for target in targets:
                jd_cross = find_crossing_time(t_current, t_next, target, topo_coords)
                dt_cross = jd_to_datetime_utc(jd_cross)
                
                # Prevent yielding events slightly outside [jd_start, jd_end] due to precision limits
                if jd_start <= jd_cross <= jd_end:
                    yield {
                        'jd': jd_cross,
                        'dt': dt_cross,
                        'degree': target // 60,
                        'minute': target % 60,
                        'ayanamsa': get_ayanamsa_dm(jd_cross)
                    }
                    
        t_current = t_next
        lon_curr = lon_next
        a_curr = a_next
