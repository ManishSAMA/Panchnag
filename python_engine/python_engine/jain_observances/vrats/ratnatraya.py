import datetime
from typing import List, Dict, Optional, Protocol, Set, Tuple
from dataclasses import dataclass

class TithiProvider(Protocol):
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
        
    def get_tithi_at_time(self, time: datetime.datetime, lat: float, lon: float) -> int:
        """
        Returns absolute Tithi index (1-30).
        13 = Shukla Trayodashi, 14 = Shukla Chaturdashi, 15 = Shukla Poornima
        """
        ...

    def get_hindu_month_name(self, date: datetime.date, lat: float, lon: float) -> str:
        ...

@dataclass
class RatnatrayaSchedule:
    month: str
    dharana_date: str
    fast_start_date: str
    fast_end_date: str
    parana_date: str
    total_fasting_days: int
    has_kshaya: bool
    has_vriddhi: bool

def calculate_ratnatraya_vrat(
    year: int,
    month: int,
    month_name: str,  # "BHADRAPADA", "MAGHA", or "CHAITRA"
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[RatnatrayaSchedule]:
    """
    Calculates the Ratnatraya Vrat (Shukla 13 to 15) using active Tithis touching 
    the morning window (Sunrise to Sunrise + 144m).
    
    Guarantees min 3 fasting days (shifting fast start to Dwadashi on Kshaya),
    adjusts Dharana accordingly, and calculates Parana.
    """
    TARGET_START_TITHI = 13  # Shukla Trayodashi
    TARGET_END_TITHI = 15    # Shukla Poornima
    
    # Scan a wide 45-day window around the 1st of the month
    search_start = datetime.date(year, month, 1) - datetime.timedelta(days=7)
    daily_active: Dict[datetime.date, Set[int]] = {}
    
    for day_offset in range(45):
        current_date = search_start + datetime.timedelta(days=day_offset)
        sunrise_time = provider.get_sunrise(current_date, lat, lon)
        cutoff_time = sunrise_time + datetime.timedelta(minutes=144)
        
        t_cutoff = provider.get_tithi_at_time(cutoff_time, lat, lon)
        
        # Capture strictly the Tithi at the morning window cutoff (skip if Adhik Maas)
        if hasattr(provider, 'is_adhik_month') and provider.is_adhik_month(current_date, lat, lon):
            continue
        daily_active[current_date] = {t_cutoff}

    # Locate primary Trayodashi (13) in target month
    baseline_start_date = None
    for d in sorted(daily_active.keys()):
        d_month_name = provider.get_hindu_month_name(d, lat, lon)
        if d_month_name.upper() == month_name.upper() and TARGET_START_TITHI in daily_active[d]:
            baseline_start_date = d
            break

    # Fallback if Trayodashi suffered complete Kshaya -> Anchor at Dwadashi (12)
    if not baseline_start_date:
        for d in sorted(daily_active.keys()):
            d_month_name = provider.get_hindu_month_name(d, lat, lon)
            if d_month_name.upper() == month_name.upper() and 12 in daily_active[d]:
                baseline_start_date = d
                break

    if not baseline_start_date:
        return None

    # Helper function to scan schedule continuously from an anchor date
    def scan_window(anchor_date: datetime.date, start_tithi_target: int) -> List[Tuple[datetime.date, int]]:
        schedule = []
        curr = anchor_date
        curr_tithi = start_tithi_target
        
        while curr_tithi <= TARGET_END_TITHI:
            active_set = daily_active.get(curr, set())
            
            matched = None
            for t_val in range(curr_tithi, TARGET_END_TITHI + 1):
                if t_val in active_set:
                    matched = t_val
                    break
            
            if matched is not None:
                schedule.append((curr, matched))
                
                # Check for Vriddhi on consecutive day
                next_day = curr + datetime.timedelta(days=1)
                if matched in daily_active.get(next_day, set()):
                    schedule.append((next_day, matched))
                    curr = next_day  # Advance to skip repeating date twice in outer loop
                
                curr_tithi = matched + 1
            
            curr += datetime.timedelta(days=1)
            
            if curr > anchor_date + datetime.timedelta(days=10):
                break  # Circuit breaker
                
        return schedule

    # 1. First Pass: Natural baseline span
    baseline_schedule = scan_window(baseline_start_date, TARGET_START_TITHI)
    
    # 2. Check for Kshaya (fewer than 3 unique Tithis between 13 and 15)
    distinct_target_tithis = len({t for _, t in baseline_schedule if TARGET_START_TITHI <= t <= TARGET_END_TITHI})
    has_kshaya = distinct_target_tithis < 3 or len(baseline_schedule) < 3
    
    shift_days = max(0, 3 - len(baseline_schedule))
    
    # 3. Final Pass with early shifted start date if needed
    final_start_date = baseline_start_date - datetime.timedelta(days=shift_days)
    final_start_tithi = TARGET_START_TITHI - shift_days
    
    final_schedule = scan_window(final_start_date, final_start_tithi)
    
    # 4. Determine Fasting Dates & Vriddhi
    fast_start_date = final_schedule[0][0]
    fast_end_date = final_schedule[-1][0]
    total_fasting_days = len(final_schedule)
    
    observed_tithis = [t for _, t in final_schedule]
    has_vriddhi = len(observed_tithis) > len(set(observed_tithis))

    # 5. Determine Dharana Date (Day before Fasting Begins)
    dharana_date = fast_start_date - datetime.timedelta(days=1)

    # 6. Determine Parana Date (Day after Fasting Ends)
    parana_date = fast_end_date + datetime.timedelta(days=1)

    return RatnatrayaSchedule(
        month=month_name,
        dharana_date=dharana_date.strftime("%Y-%m-%d"),
        fast_start_date=fast_start_date.strftime("%Y-%m-%d"),
        fast_end_date=fast_end_date.strftime("%Y-%m-%d"),
        parana_date=parana_date.strftime("%Y-%m-%d"),
        total_fasting_days=total_fasting_days,
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi
    )

from .provider import SwissEphTithiProvider
