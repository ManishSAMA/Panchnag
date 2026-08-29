import datetime
from typing import List, Tuple, Protocol
from dataclasses import dataclass
# pyrefly: ignore[missing-import]
import swisseph as swe

@dataclass
class NakshatraSpan:
    nakshatra_id: int
    name: str
    start_time: datetime.datetime
    end_time: datetime.datetime

class PanchangProvider(Protocol):
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
    def get_nakshatra_spans(self, start_time: datetime.datetime, end_time: datetime.datetime) -> List[NakshatraSpan]:
        ...

def get_jain_day_window(date: datetime.date, lat: float, lon: float, provider: PanchangProvider) -> Tuple[datetime.datetime, datetime.datetime]:
    sunrise_today = provider.get_sunrise(date, lat, lon)
    sunrise_tomorrow = provider.get_sunrise(date + datetime.timedelta(days=1), lat, lon)
    jain_start = sunrise_today + datetime.timedelta(minutes=144)
    jain_end = sunrise_tomorrow + datetime.timedelta(minutes=0)
    return jain_start, jain_end

def evaluate_rohini_vrat(start_date: datetime.date, end_date: datetime.date, lat: float, lon: float, provider: PanchangProvider) -> List[datetime.date]:
    """Rohini Nakshatra Parv Vrat is observed on the day Rohini nakshatra prevails
    at sunrise (udaya). Only when Rohini's whole span falls between two sunrises --
    touching neither -- does it fall back to the civil day that wholly contains it."""
    vrat_dates = []
    ROHINI_ID = 4
    curr_date = start_date
    while curr_date <= end_date:
        sunrise_today = provider.get_sunrise(curr_date, lat, lon)
        sunrise_tomorrow = provider.get_sunrise(curr_date + datetime.timedelta(days=1), lat, lon)
        spans = provider.get_nakshatra_spans(sunrise_today, sunrise_tomorrow)
        rohini_span = next((span for span in spans if span.nakshatra_id == ROHINI_ID), None)
        if rohini_span:
            prevails_at_sunrise = rohini_span.start_time <= sunrise_today <= rohini_span.end_time
            wholly_within_day = sunrise_today < rohini_span.start_time and rohini_span.end_time < sunrise_tomorrow
            if prevails_at_sunrise or wholly_within_day:
                if curr_date not in vrat_dates:
                    vrat_dates.append(curr_date)
                curr_date += datetime.timedelta(days=20)
                continue
        curr_date += datetime.timedelta(days=1)
    return sorted(vrat_dates)

# ==========================================
# INTEGRATION HOOKS & MOCK IMPLEMENTATIONS
# ==========================================

from astronomy import get_sunrise, local_time_to_jd
from panchang import get_nakshatra_at_jd, get_nakshatra_start_jd, _find_exact_end_time, NAKSHATRA_NAMES, get_planetary_longitude

def jd_to_utc_dt(jd: float) -> datetime.datetime:
    y, m, d, h_utc = swe.revjul(jd, swe.GREG_CAL)
    # create utc datetime
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
        from astronomy import local_date_anchor_jd, get_sunrise, jd_to_zoned_datetime
        tz_name = get_timezone_name(lat, lon)
        anchor_jd = local_date_anchor_jd(date_obj, tz_name)
        sunrise_jd = get_sunrise(anchor_jd, lat, lon)
        sunrise_dt = jd_to_zoned_datetime(sunrise_jd, tz_name)
        return sunrise_dt.replace(tzinfo=None)
        
    def get_nakshatra_spans(self, start_time: datetime.datetime, end_time: datetime.datetime) -> List[NakshatraSpan]:
        start_jd = dt_to_jd(start_time)
        end_jd = dt_to_jd(end_time)
        spans = []
        curr_jd = start_jd
        while curr_jd <= end_jd:
            nak_idx = get_nakshatra_at_jd(curr_jd, self.ayanamsa)
            moon_lon = get_planetary_longitude(curr_jd, 'Moon', self.ayanamsa)
            start_nak_jd = get_nakshatra_start_jd(curr_jd, nak_idx, moon_lon, self.ayanamsa)
            
            nak_len = 360.0 / 27.0
            nak_left_deg = nak_len - (moon_lon % nak_len)
            nak_low = curr_jd + (nak_left_deg / 16.0)
            nak_high = curr_jd + (nak_left_deg / 11.0) + 0.05
            end_nak_jd = _find_exact_end_time(curr_jd, get_nakshatra_at_jd, nak_idx, self.ayanamsa, nak_low, nak_high)
            
            start_dt = jd_to_utc_dt(start_nak_jd).replace(tzinfo=None)
            end_dt = jd_to_utc_dt(end_nak_jd).replace(tzinfo=None)
            
            spans.append(NakshatraSpan(
                nakshatra_id=nak_idx,
                name=NAKSHATRA_NAMES[nak_idx - 1],
                start_time=start_dt,
                end_time=end_dt
            ))
            curr_jd = end_nak_jd + 0.01
        return spans

class JSONApiPanchangProvider:
    def __init__(self, api_url: str):
        self.api_url = api_url
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        raise NotImplementedError("Implement API call")
    def get_nakshatra_spans(self, start_time: datetime.datetime, end_time: datetime.datetime) -> List[NakshatraSpan]:
        raise NotImplementedError("Implement API call")
