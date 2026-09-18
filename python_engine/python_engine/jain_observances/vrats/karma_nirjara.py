import datetime
from typing import List, Tuple, Protocol, Dict, Optional, Union
from dataclasses import dataclass

class TithiProvider(Protocol):
    """Interface for providing astronomical Tithi data."""
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
        
    def get_tithi_at_time(self, time: datetime.datetime, lat: float, lon: float) -> int:
        ...

@dataclass
class KarmaNirjaraSchedule:
    vrat_name: str
    year: int
    month: str
    tithi: str
    has_kshaya: bool
    has_vriddhi: bool
    vrat_date: Optional[str] = None
    vrat_dates: Optional[List[str]] = None


def calculate_karma_nirjara_vrat(
    year: int,
    month: int,
    month_name: str,
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[KarmaNirjaraSchedule]:
    """
    Calculates the Karma Nirjara Vrat (Shukla Panchami),
    enforcing Jain Day +84 minute boundaries, Kshaya and Vriddhi rules.
    """
    
    start_date = datetime.date(year, month, 1)
    next_month_year = year + (month // 12)
    next_month = (month % 12) + 1
    end_date = datetime.date(next_month_year, next_month, 15)
    
    target_tithi = 5
    fallback_tithi = 4

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
        
    cluster_dates = []
    for d in sorted(date_to_tithi.keys()):
        t = date_to_tithi[d]
        if t in [target_tithi, fallback_tithi]:
            if not cluster_dates or (d - cluster_dates[-1]).days == 1:
                cluster_dates.append(d)
            elif (d - cluster_dates[-1]).days > 1 and len(cluster_dates) >= 2:
                break
            else:
                cluster_dates = [d]

    if not cluster_dates:
        return None

    panchami_dates = [d for d in cluster_dates if date_to_tithi[d] == target_tithi]
    
    has_kshaya = False
    has_vriddhi = False
    vrat_date = None
    vrat_dates = None
    
    if len(panchami_dates) == 1:
        # Standard Case
        vrat_date = panchami_dates[0].strftime("%Y-%m-%d")
    elif len(panchami_dates) == 0:
        # Kshaya Rule (Skipped Panchami)
        has_kshaya = True
        chaturthi_dates = [d for d in cluster_dates if date_to_tithi[d] == fallback_tithi]
        if chaturthi_dates:
            vrat_date = chaturthi_dates[-1].strftime("%Y-%m-%d")
        else:
            vrat_date = cluster_dates[0].strftime("%Y-%m-%d")
    elif len(panchami_dates) > 1:
        # Vriddhi Rule (Repeated Panchami)
        has_vriddhi = True
        vrat_dates = [d.strftime("%Y-%m-%d") for d in panchami_dates]

    return KarmaNirjaraSchedule(
        vrat_name="Karma Nirjara Vrat",
        year=year,
        month=month_name,
        vrat_date=vrat_date,
        vrat_dates=vrat_dates,
        tithi="Shukla Panchami",
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi
    )

from .provider import SwissEphTithiProvider

