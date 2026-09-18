import datetime
from typing import List, Tuple, Protocol, Dict, Optional, Any
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


@dataclass(frozen=True)
class VratSchedule:
    start_date: str
    end_date: str
    total_fasting_days: int
    has_kshaya: bool
    has_vriddhi: bool


def calculate_bhaktambar_vrat(
    year: int,
    month: int,
    paksha: str,
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[VratSchedule]:
    """
    Calculates the Bhaktambar Vrat (Ashtami to Chaturdashi) for a specific month and paksha,
    enforcing Jain Day +144 minute boundaries, Kshaya (min 7 days) and Vriddhi rules.
    Accepts case-insensitive paksha strings ('SHUKLA', 'shukla', 'Krishna', etc.).
    """
    norm_paksha = paksha.strip().upper() if isinstance(paksha, str) else ""
    if norm_paksha not in ["SHUKLA", "KRISHNA"]:
        raise ValueError(f"Invalid paksha '{paksha}'. Must be 'SHUKLA' or 'KRISHNA'.")

    # Define search window from 1st of month to 10th of next month
    start_date = datetime.date(year, month, 1)
    next_month_year = year + (month // 12)
    next_month = (month % 12) + 1
    end_date = datetime.date(next_month_year, next_month, 10)

    # Target Tithis based on Paksha
    # Shukla Paksha = 1 to 15. Target: 8 to 14
    # Krishna Paksha = 16 to 30. Target: 23 to 29 (which is Krishna 8 to Krishna 14)
    if norm_paksha == "SHUKLA":
        target_tithi_range = range(8, 15)
        saptami_idx = 7
    else:
        target_tithi_range = range(23, 30)
        saptami_idx = 22

    # Step 1: Calculate Calendar Days for Target Tithis
    date_to_tithi: Dict[datetime.date, int] = {}
    curr = start_date
    while curr <= end_date:
        sunrise = provider.get_sunrise(curr, lat, lon)
        jain_cutoff = sunrise + datetime.timedelta(minutes=144)
        tithi_idx = provider.get_tithi_at_time(jain_cutoff, lat, lon)
        date_to_tithi[curr] = tithi_idx
        curr += datetime.timedelta(days=1)

    # Extract cluster dates for the target paksha
    cluster_dates: List[datetime.date] = []
    for d in sorted(date_to_tithi.keys()):
        t = date_to_tithi[d]
        if t in target_tithi_range or t == saptami_idx:
            if not cluster_dates or (d - cluster_dates[-1]).days == 1:
                cluster_dates.append(d)
            elif (d - cluster_dates[-1]).days > 1 and len(cluster_dates) >= 5:
                break
            else:
                cluster_dates = [d]

    if not cluster_dates:
        return None

    # Step 2: Determine start and end days
    ashtami_dates = [d for d in cluster_dates if date_to_tithi[d] == target_tithi_range[0]]
    if not ashtami_dates:
        saptami_dates = [d for d in cluster_dates if date_to_tithi[d] == saptami_idx]
        start_day = saptami_dates[0] if saptami_dates else cluster_dates[0]
    else:
        start_day = ashtami_dates[0]

    chaturdashi_dates = [d for d in cluster_dates if date_to_tithi[d] == target_tithi_range[-1]]
    if not chaturdashi_dates:
        target_dates = [d for d in cluster_dates if date_to_tithi[d] in target_tithi_range]
        end_day = max(target_dates) if target_dates else cluster_dates[-1]
    else:
        end_day = chaturdashi_dates[-1]

    total_days = (end_day - start_day).days + 1

    # Step 3: Apply Kshaya Rule (Min 7 Days Guarantee)
    has_kshaya = False
    if total_days < 7:
        has_kshaya = True
        saptami_dates = [d for d in cluster_dates if date_to_tithi[d] == saptami_idx]
        if saptami_dates:
            start_day = saptami_dates[0]
        else:
            start_day = end_day - datetime.timedelta(days=6)

        total_days = (end_day - start_day).days + 1
        if total_days < 7:
            start_day = end_day - datetime.timedelta(days=6)
            total_days = 7

    # Step 4: Vriddhi Rule Detection
    has_vriddhi = total_days > 7

    return VratSchedule(
        start_date=start_day.strftime("%Y-%m-%d"),
        end_date=end_day.strftime("%Y-%m-%d"),
        total_fasting_days=total_days,
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi
    )


# ==========================================
# INTEGRATION HOOKS & MOCK IMPLEMENTATIONS
# ==========================================

from .provider import SwissEphTithiProvider

