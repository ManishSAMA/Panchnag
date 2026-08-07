import datetime
from typing import List, Tuple, Protocol, Optional
from dataclasses import dataclass
import swisseph as swe

@dataclass
class NakshatraSpan:
    nakshatra_id: int
    name: str
    start_time: datetime.datetime  # UTC
    end_time: datetime.datetime    # UTC

class PanchangProvider(Protocol):
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
    def get_nakshatra_at_time(self, dt: datetime.datetime) -> int:
        ...

def evaluate_rohini_vrat(
    start_date: datetime.date,
    end_date: datetime.date,
    lat: float,
    lon: float,
    provider: PanchangProvider
) -> List[datetime.date]:
    """
    Evaluates Rohini Vrat dates between start_date and end_date.
    A day is flagged if Rohini Nakshatra (ID = 4) is active at the morning cutoff (Sunrise + 144 mins).
    Handles Tithi/Nakshatra Vriddhi (both days marked if Rohini is active at cutoff on both days)
    and Kshaya (assign to day before if Rohini is skipped at cutoff).
    """
    vrat_dates = []
    ROHINI_ID = 4
    
    def get_nak_at_cutoff(d: datetime.date) -> int:
        try:
            sunrise = provider.get_sunrise(d, lat, lon)
            cutoff = sunrise + datetime.timedelta(minutes=144)
            return provider.get_nakshatra_at_time(cutoff)
        except:
            return 0

    curr_date = start_date
    while curr_date <= end_date:
        nak_today = get_nak_at_cutoff(curr_date)
        
        if nak_today == ROHINI_ID:
            vrat_dates.append(curr_date)
            # Check if it lasts 2 days (Vriddhi)
            next_date = curr_date + datetime.timedelta(days=1)
            nak_next = get_nak_at_cutoff(next_date)
            if nak_next == ROHINI_ID:
                vrat_dates.append(next_date)
                curr_date = next_date + datetime.timedelta(days=24)
            else:
                curr_date = curr_date + datetime.timedelta(days=24)
        else:
            # Check if Rohini is skipped (Kshaya)
            next_date = curr_date + datetime.timedelta(days=1)
            nak_next = get_nak_at_cutoff(next_date)
            
            # Today has Krittika (3) at cutoff, and tomorrow has Mrigashirsha (5) at cutoff,
            # meaning Rohini (4) was completely skipped at cutoff!
            is_skipped = (nak_today == 3 and nak_next == 5)
            
            if is_skipped:
                # Assign to one day before (which is curr_date / today)
                vrat_dates.append(curr_date)
                curr_date += datetime.timedelta(days=24)
            else:
                curr_date += datetime.timedelta(days=1)
                
    return sorted(vrat_dates)


# ==========================================
# INTEGRATION HOOKS & MOCK IMPLEMENTATIONS
# ==========================================

from astronomy import get_sunrise, local_time_to_jd
from panchang import get_nakshatra_at_jd, NAKSHATRA_NAMES

def jd_to_utc_dt(jd: float) -> datetime.datetime:
    y, m, d, h_utc = swe.revjul(jd, swe.GREG_CAL)
    return datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=h_utc)

def dt_to_jd(dt: datetime.datetime) -> float:
    # Convert naive dt representing UTC to JD
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour)

class SwissEphPanchangProvider:
    def __init__(self, ayanamsa: str = "Lahiri"):
        self.ayanamsa = ayanamsa
        
    def get_sunrise(self, date_obj: datetime.date, lat: float, lon: float) -> datetime.datetime:
        from location_service import get_timezone_name
        from astronomy import local_date_anchor_jd, get_sunrise
        tz_name = get_timezone_name(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon)
        return jd_to_utc_dt(sunrise_jd).replace(tzinfo=None)
        
    def get_nakshatra_at_time(self, dt: datetime.datetime) -> int:
        jd = dt_to_jd(dt)
        return get_nakshatra_at_jd(jd, self.ayanamsa)

class JSONApiPanchangProvider:
    def __init__(self, api_url: str):
        self.api_url = api_url
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        raise NotImplementedError("Implement API call")
    def get_nakshatra_at_time(self, dt: datetime.datetime) -> int:
        raise NotImplementedError("Implement API call")
