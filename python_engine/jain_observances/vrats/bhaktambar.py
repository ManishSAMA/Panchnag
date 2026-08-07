import datetime
from typing import List, Tuple, Protocol, Dict, Optional, Set
from dataclasses import dataclass

class TithiProvider(Protocol):
    """
    Interface for providing astronomical Tithi data.
    """
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        """Return the exact datetime of sunrise for the given date and location."""
        ...
        
    def get_tithi_at_time(self, time: datetime.datetime, lat: float, lon: float) -> int:
        """
        Return the absolute Tithi index (1-30) active at the exact given datetime.
        1-15 = Shukla Paksha (1-15)
        16-30 = Krishna Paksha (1-15)
        """
        ...

@dataclass
class DayTithiInfo:
    date: datetime.date
    tithi_at_sunrise: int
    tithi_at_cutoff: int  # Tithi at Sunrise + 144 mins
    active_tithis: Set[int]  # Set of all tithis touching the morning window

@dataclass
class VratSchedule:
    start_date: str
    end_date: str
    total_fasting_days: int
    has_kshaya: bool
    has_vriddhi: bool
    daily_details: Optional[List[str]] = None


def calculate_bhaktambar_vrat(
    year: int,
    month: int,
    paksha: str,  # "SHUKLA" or "KRISHNA"
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[VratSchedule]:
    """
    Calculates Bhaktambar Vrat anchored by 8th (Ashtami) start and 14th (Chaturdashi) end,
    evaluating Tithi state between Sunrise and Sunrise + 144 minutes.
    """
    is_shukla = paksha.upper() == "SHUKLA"
    
    # Target Tithi indices for the Paksha
    # Shukla: Ashtami=8, ..., Chaturdashi=14
    # Krishna: Ashtami=23, ..., Chaturdashi=29
    ashtami_idx = 8 if is_shukla else 23
    chaturdashi_idx = 14 if is_shukla else 29
    
    # Scan window (~35 days around target month)
    search_start = datetime.date(year, month, 1) - datetime.timedelta(days=5)
    
    daily_records: Dict[datetime.date, DayTithiInfo] = {}

    # Step 1: Scan dates and capture Sunrise + 144 min window
    for day_offset in range(40):
        current_date = search_start + datetime.timedelta(days=day_offset)
        sunrise = provider.get_sunrise(current_date, lat, lon)
        cutoff_time = sunrise + datetime.timedelta(minutes=144)
        
        t_sunrise = provider.get_tithi_at_time(sunrise, lat, lon)
        t_cutoff = provider.get_tithi_at_time(cutoff_time, lat, lon)
        
        # Combine both Tithis into a set to detect overlap/touching
        active_set = {t_sunrise, t_cutoff}
        
        daily_records[current_date] = DayTithiInfo(
            date=current_date,
            tithi_at_sunrise=t_sunrise,
            tithi_at_cutoff=t_cutoff,
            active_tithis=active_set
        )

    # Step 2: Find Start Trigger (Day containing Ashtami / 8th)
    start_date: Optional[datetime.date] = None
    for d in sorted(daily_records.keys()):
        # Ensure we anchor in the right month scope
        if d.month == month or (d.month == (month % 12) + 1 and d.day <= 10):
            if ashtami_idx in daily_records[d].active_tithis:
                start_date = d
                break

    if not start_date:
        return None  # Could not anchor Ashtami trigger

    # Step 3: Find End Trigger (Day containing Chaturdashi / 14th)
    end_date: Optional[datetime.date] = None
    curr = start_date
    while curr <= start_date + datetime.timedelta(days=12):
        if curr in daily_records:
            rec = daily_records[curr]
            if chaturdashi_idx in rec.active_tithis:
                end_date = curr
                # If 14th continues onto the next solar day (Vriddhi), extend to include it
                next_day = curr + datetime.timedelta(days=1)
                if next_day in daily_records and chaturdashi_idx in daily_records[next_day].active_tithis:
                    end_date = next_day
                break
        curr += datetime.timedelta(days=1)

    if not end_date:
        return None

    # Step 4: Extract all fasting days between start_date and end_date
    fasting_days: List[DayTithiInfo] = []
    curr = start_date
    while curr <= end_date:
        fasting_days.append(daily_records[curr])
        curr += datetime.timedelta(days=1)

    total_days = len(fasting_days)

    # Step 5: Check Kshaya & Vriddhi flags
    # Standard Vrat span is usually 7-8 calendar days
    has_kshaya = total_days < 7
    has_vriddhi = total_days > 8

    # Formulate human-readable daily summary
    details = []
    for info in fasting_days:
        if info.tithi_at_sunrise == info.tithi_at_cutoff:
            t_str = f"Tithi {info.tithi_at_sunrise}"
        else:
            t_str = f"Overlap: Tithi {info.tithi_at_sunrise} & Tithi {info.tithi_at_cutoff} (Counted as 1 day)"
        details.append(f"{info.date.strftime('%Y-%m-%d')}: {t_str}")

    return VratSchedule(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        total_fasting_days=total_days,
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi,
        daily_details=details
    )


# ==========================================
# INTEGRATION HOOKS & MOCK IMPLEMENTATIONS
# ==========================================

from .provider import SwissEphTithiProvider
