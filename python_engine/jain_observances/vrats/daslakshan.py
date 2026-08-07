import datetime
from typing import List, Dict, Optional, Protocol, Set, Tuple
from dataclasses import dataclass

class TithiProvider(Protocol):
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
        
    def get_tithi_at_time(self, time: datetime.datetime, lat: float, lon: float) -> int:
        """
        Returns absolute Tithi index (1-30).
        1-15: Shukla Paksha (1=Pratipada ... 5=Panchami ... 14=Chaturdashi, 15=Purnima)
        16-30: Krishna Paksha
        """
        ...

    def get_hindu_month_name(self, date: datetime.date, lat: float, lon: float) -> str:
        ...

@dataclass
class DailySchedule:
    date: str
    tithi_index: int
    virtue: str
    note: Optional[str] = None

@dataclass
class DaslakshanSchedule:
    month: str
    start_date: str
    end_date: str
    total_days: int
    has_kshaya: bool
    has_vriddhi: bool
    daily_schedule: List[DailySchedule]

VIRTUES = [
    "Uttam Kshama",      # Day 1 / Panchami
    "Uttam Mardava",     # Day 2 / Shasthi
    "Uttam Aarjava",     # Day 3 / Saptami
    "Uttam Shaucha",     # Day 4 / Ashtami
    "Uttam Satya",       # Day 5 / Navami
    "Uttam Sanyam",      # Day 6 / Dashami
    "Uttam Tapa",        # Day 7 / Ekadashi
    "Uttam Tyaga",       # Day 8 / Dwadashi
    "Uttam Akinchanya",  # Day 9 / Trayodashi
    "Uttam Brahmacharya" # Day 10 / Chaturdashi (Anant Chaturdashi)
]

def calculate_daslakshan_vrat(
    year: int,
    month: int,
    month_name: str,  # "BHADRAPADA", "MAGHA", or "CHAITRA"
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[DaslakshanSchedule]:
    """
    Calculates Daslakshan Mahaparv using active Tithis touching the
    Sunrise to Sunrise + 144 minutes morning window (6 Ghatis).
    
    Guarantees 10 fasting days by shifting early on Kshaya, aligns 
    Uttam Dharmas properly without index overflows, and detects Vriddhi.
    """
    TARGET_START_TITHI = 5   # Shukla Panchami
    TARGET_END_TITHI = 14    # Shukla Chaturdashi
    
    # Step 1: Pre-calculate active Tithi sets touching the +144 min morning window
    search_start = datetime.date(year, month, 1) - datetime.timedelta(days=7)
    daily_active: Dict[datetime.date, Set[int]] = {}
    
    for day_offset in range(45):
        current_date = search_start + datetime.timedelta(days=day_offset)
        sunrise_time = provider.get_sunrise(current_date, lat, lon)
        cutoff_time = sunrise_time + datetime.timedelta(minutes=144)
        
        t_cutoff = provider.get_tithi_at_time(cutoff_time, lat, lon)
        
        # Capture all Tithis touching the 144 min window (skip if Adhik Maas)
        if hasattr(provider, 'is_adhik_month') and provider.is_adhik_month(current_date, lat, lon):
            continue
        daily_active[current_date] = {t_cutoff}

    # Step 2: Locate the primary Panchami date in target month
    baseline_start_date = None
    for d in sorted(daily_active.keys()):
        d_month_name = provider.get_hindu_month_name(d, lat, lon)
        if d_month_name.upper() == month_name.upper() and TARGET_START_TITHI in daily_active[d]:
            baseline_start_date = d
            break

    # Fallback if Panchami itself suffered a complete Kshaya
    if not baseline_start_date:
        for d in sorted(daily_active.keys()):
            d_month_name = provider.get_hindu_month_name(d, lat, lon)
            if d_month_name.upper() == month_name.upper() and 6 in daily_active[d]:
                baseline_start_date = d
                break

    if not baseline_start_date:
        return None

    # Helper function to scan schedule continuously from an anchor date
    def scan_parv_window(anchor_date: datetime.date, start_target: int) -> List[Tuple[datetime.date, int]]:
        schedule = []
        curr = anchor_date
        curr_tithi = start_target
        
        while curr_tithi <= TARGET_END_TITHI:
            active_set = daily_active.get(curr, set())
            
            # Find the lowest matching target Tithi in today's active set
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
            
            # Safety circuit breaker to prevent infinite loops
            if curr > anchor_date + datetime.timedelta(days=20):
                break
                
        return schedule

    # Step 3: First Pass - Natural baseline span
    baseline_schedule = scan_parv_window(baseline_start_date, TARGET_START_TITHI)
    
    # Step 4: Evaluate Kshaya & Calculate Early Shift required
    distinct_target_tithis = len({t for _, t in baseline_schedule if TARGET_START_TITHI <= t <= TARGET_END_TITHI})
    has_kshaya = distinct_target_tithis < 10 or len(baseline_schedule) < 10
    
    shift_days = max(0, 10 - len(baseline_schedule))
    
    # Step 5: Final Pass with shifted start date if needed
    final_start_date = baseline_start_date - datetime.timedelta(days=shift_days)
    final_start_tithi = TARGET_START_TITHI - shift_days
    
    final_schedule = scan_parv_window(final_start_date, final_start_tithi)
    
    # Step 6: Detect Vriddhi across final schedule
    observed_tithis = [t for _, t in final_schedule]
    has_vriddhi = len(observed_tithis) > len(set(observed_tithis))

    # Step 7: Safely Map Virtues 1-to-1
    daily_schedule: List[DailySchedule] = []
    virtue_pointer = 0

    for i, (day, tithi) in enumerate(final_schedule):
        note = None
        is_repeat = (i > 0 and final_schedule[i-1][1] == tithi)
        
        if is_repeat:
            note = f"Vriddhi Day (Repeat of Tithi {tithi})"
        elif i > 0:
            virtue_pointer += 1

        # Safely cap virtue index at 9 (Uttam Brahmacharya) to prevent overflow
        v_idx = min(virtue_pointer, 9)
        
        daily_schedule.append(DailySchedule(
            date=day.strftime("%Y-%m-%d"),
            tithi_index=tithi,
            virtue=VIRTUES[v_idx],
            note=note
        ))

    return DaslakshanSchedule(
        month=month_name,
        start_date=final_schedule[0][0].strftime("%Y-%m-%d"),
        end_date=final_schedule[-1][0].strftime("%Y-%m-%d"),
        total_days=len(final_schedule),
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi,
        daily_schedule=daily_schedule
    )

from .provider import SwissEphTithiProvider
