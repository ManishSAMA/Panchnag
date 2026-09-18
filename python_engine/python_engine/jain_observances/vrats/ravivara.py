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
        """Returns the Jain/Lunar month name at the given date."""
        ...

@dataclass
class DailySchedule:
    vrat_number: int
    date: str
    month: str

@dataclass
class RavivaraSchedule:
    vrat_name: str
    year: int
    total_sundays: int
    start_date: str
    end_date: str
    schedule: List[DailySchedule]


def calculate_ravivara_vrat(
    year: int,
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[RavivaraSchedule]:
    """
    Calculates the 9 annual dates for the Ravivara Vrat.
    Anchors to the LAST Sunday in Ashadha Shukla Paksha,
    evaluated using the strict +84 minute Jain Day cutoff.
    """
    
    # Step 1: Find Ashadha Shukla Paksha Boundaries
    # Ashadha typically falls between June (6) and July (7).
    # We scan a window from June 1 to August 15 to safely capture it.
    start_search = datetime.date(year, 6, 1)
    end_search = datetime.date(year, 8, 15)
    
    ashadha_shukla_sundays = []
    
    curr = start_search
    while curr <= end_search:
        sunrise = provider.get_sunrise(curr, lat, lon)
        jain_cutoff = sunrise + datetime.timedelta(minutes=84)
        
        # We only care about Sundays
        # In Python, Monday is 0 and Sunday is 6
        if curr.weekday() == 6:
            month_name = provider.get_hindu_month_name(jain_cutoff.date(), lat, lon)
            tithi_idx = provider.get_tithi_at_time(jain_cutoff, lat, lon)
            
            # Check if it's Ashadha (ignoring Adhik/Nija prefix for simplicity, 
            # or matching exactly depending on strictness. We use "ashadha" in substring)
            # Shukla Paksha corresponds to Tithis 1 through 15
            if month_name and "ashadha" in month_name.lower():
                if 1 <= tithi_idx <= 15:
                    ashadha_shukla_sundays.append(curr)
                    
        curr += datetime.timedelta(days=1)

    if not ashadha_shukla_sundays:
        return None

    # Step 2: Calculate Vrat_Sunday_1 (Start Date)
    # The cycle MUST start on the LAST Sunday in Ashadha Shukla Paksha
    start_date = ashadha_shukla_sundays[-1]
    
    # Step 3: Generate the 9 Annual Vrat Dates
    vrat_dates = []
    total_sundays = 9
    
    for i in range(total_sundays):
        current_sunday = start_date + datetime.timedelta(days=i * 7)
        
        # Calculate the governing month for this specific Sunday for schedule display
        sunrise = provider.get_sunrise(current_sunday, lat, lon)
        jain_cutoff = sunrise + datetime.timedelta(minutes=84)
        month_at_date = provider.get_hindu_month_name(jain_cutoff.date(), lat, lon)
        
        vrat_dates.append(DailySchedule(
            vrat_number=i + 1,
            date=current_sunday.strftime("%Y-%m-%d"),
            month=month_at_date or "Unknown"
        ))

    return RavivaraSchedule(
        vrat_name="Ravivara Vrat",
        year=year,
        total_sundays=total_sundays,
        start_date=vrat_dates[0].date,
        end_date=vrat_dates[-1].date,
        schedule=vrat_dates
    )


# ==========================================
# INTEGRATION HOOKS & MOCK IMPLEMENTATIONS
from .provider import SwissEphTithiProvider

