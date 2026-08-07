import datetime
from typing import List, Tuple, Protocol, Dict, Optional
from dataclasses import dataclass

class TithiProvider(Protocol):
    """Interface for providing astronomical Tithi data."""
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
        
    def get_tithi_at_time(self, time: datetime.datetime, lat: float, lon: float) -> int:
        ...

    def get_hindu_month_name(self, date: datetime.date, lat: float, lon: float) -> str:
        ...

@dataclass
class AshtahnikaSchedule:
    month: str
    start_date: str
    end_date: str
    total_days: int
    has_kshaya: bool
    has_vriddhi: bool


def calculate_ashtahnika_vrat(
    year: int,
    month: int,
    month_name: str, # "KARTIKA", "PHALGUNA", or "ASHADHA"
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[AshtahnikaSchedule]:
    """
    Calculates the Ashtahnika Mahaparv for a specific month (Shukla 8 to 15),
    enforcing Jain Day +84 minute boundaries, Kshaya (min 8 days) and Vriddhi rules.
    """
    
    # We scan a 40-day window around the 1st of the month to capture Shukla Paksha
    start_date = datetime.date(year, month, 1)
    next_month_year = year + (month // 12)
    next_month = (month % 12) + 1
    end_date = datetime.date(next_month_year, next_month, 15)
    
    # Target Tithis:
    # 7: Saptami (Kshaya Start)
    # 8: Ashtami (Standard Start)
    # ...
    # 15: Poornima (Standard End)
    
    target_tithi_range = range(8, 16)
    saptami_idx = 7

    # Step 1: Calculate Calendar Days for Target Tithis
    date_to_tithi: Dict[datetime.date, int] = {}
    
    curr = start_date
    while curr <= end_date:
        if hasattr(provider, 'is_adhik_month') and provider.is_adhik_month(curr, lat, lon):
            curr += datetime.timedelta(days=1)
            continue
        sunrise = provider.get_sunrise(curr, lat, lon)
        jain_cutoff = sunrise + datetime.timedelta(minutes=84)
        tithi_idx = provider.get_tithi_at_time(jain_cutoff, lat, lon)
        date_to_tithi[curr] = tithi_idx
        curr += datetime.timedelta(days=1)
        
    # Group dates that form the continuous cluster of the target Paksha
    cluster_dates = []
    for d in sorted(date_to_tithi.keys()):
        t = date_to_tithi[d]
        if t in target_tithi_range or t == saptami_idx:
            if hasattr(provider, 'get_hindu_month_name') and provider.get_hindu_month_name(d, lat, lon).upper() != month_name.upper():
                continue
            if not cluster_dates or (d - cluster_dates[-1]).days == 1:
                cluster_dates.append(d)
            elif (d - cluster_dates[-1]).days > 1 and len(cluster_dates) >= 6:
                break
            else:
                cluster_dates = [d]

    if not cluster_dates:
        return None

    # Step 2: Calculate Base Span
    ashtami_dates = [d for d in cluster_dates if date_to_tithi[d] == target_tithi_range[0]]
    if not ashtami_dates:
        # Ashtami skipped (Kshaya) -> Shift to Saptami
        saptami_dates = [d for d in cluster_dates if date_to_tithi[d] == saptami_idx]
        start_day = saptami_dates[0] if saptami_dates else cluster_dates[0]
    else:
        start_day = ashtami_dates[0]

    poornima_dates = [d for d in cluster_dates if date_to_tithi[d] == target_tithi_range[-1]]
    if not poornima_dates:
        end_day = max([d for d in cluster_dates if date_to_tithi[d] in target_tithi_range])
    else:
        end_day = poornima_dates[-1]  # Vriddhi Rule: Second 15th if it repeats

    total_days = (end_day - start_day).days + 1

    # Step 3: Apply Kshaya Rule (Min 8 Days Guarantee)
    has_kshaya = False
    if total_days < 8:
        has_kshaya = True
        
        # Shift fast start back to Saptami
        saptami_dates = [d for d in cluster_dates if date_to_tithi[d] == saptami_idx]
        if saptami_dates:
            start_day = saptami_dates[0]
        else:
            start_day = end_day - datetime.timedelta(days=7)
            
        total_days = (end_day - start_day).days + 1
        
        # Double Kshaya Guarantee
        if total_days < 8:
            start_day = end_day - datetime.timedelta(days=7)
            total_days = 8

    # Step 4: Apply Vriddhi Rule Detection
    has_vriddhi = total_days > 8


    return AshtahnikaSchedule(
        month=month_name,
        start_date=start_day.strftime("%Y-%m-%d"),
        end_date=end_day.strftime("%Y-%m-%d"),
        total_days=total_days,
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi
    )

from .provider import SwissEphTithiProvider

