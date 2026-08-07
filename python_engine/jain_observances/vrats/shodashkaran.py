import datetime
from typing import List, Dict, Optional, Protocol, Set, Tuple
from dataclasses import dataclass

class TithiProvider(Protocol):
    """Interface for providing astronomical Tithi data."""
    def get_sunrise(self, date: datetime.date, lat: float, lon: float) -> datetime.datetime:
        ...
        
    def get_tithi_at_time(self, time: datetime.datetime, lat: float, lon: float) -> int:
        """
        Returns absolute Tithi index (1-30).
        1-15: Shukla Paksha (1=Pratipada ... 15=Purnima)
        16-30: Krishna Paksha (16=Krishna Pratipada ... 30=Amavasya)
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
class ShodashkaranSchedule:
    cycle_name: str
    start_date: str
    end_date: str
    total_days: int
    has_kshaya: bool
    has_vriddhi: bool
    daily_schedule: List[DailySchedule]

VIRTUES = [
    "Darshan Vishuddhi", "Vinaya Sampannata", "Sheel Vrateshu Anativyatikrama",
    "Abhikshna Jnanopayoga", "Samvega", "Shaktitas Tyaga",
    "Shaktitas Tapa", "Sadhu Samadhi", "Vaiyavritya Karana",
    "Arhant Bhakti", "Acharya Bhakti", "Bahushruta Bhakti",
    "Pravachana Bhakti", "Aavashyaka Aparihaani", "Marga Prabhavana",
    "Pravachana Vatsalya"
]

def calculate_shodashkaran_vrat(
    year: int,
    month: int,
    cycle_name: str, # e.g., "BHADRAPADA_ASHVINA"
    lat: float,
    lon: float,
    provider: TithiProvider
) -> Optional[ShodashkaranSchedule]:
    """
    Calculates the Shodashkaran / Meghmala Vrat (approx 30 Days),
    spanning from Krishna Pratipada of Month 1 to the day before Krishna Pratipada of Month 2.
    Uses active Tithis touching the morning window (Sunrise to Sunrise + 144m).
    """
    KRISHNA_PRATIPADA = 16
    
    # Map cycle name to Amanta month names for start and end verification
    purnimanta_to_amanta_start = {
        "BHADRAPADA_ASHVINA": "ASHADHA",
        "MAGHA_PHALGUNA": "PAUSHA",
        "CHAITRA_VAISHAKHA": "PHALGUNA"
    }
    purnimanta_to_amanta_end = {
        "BHADRAPADA_ASHVINA": "SHRAVANA",
        "MAGHA_PHALGUNA": "MAGHA",
        "CHAITRA_VAISHAKHA": "CHAITRA"
    }
    
    target_start_amanta = purnimanta_to_amanta_start[cycle_name]
    target_end_amanta = purnimanta_to_amanta_end[cycle_name]

    # We scan a 75-day window starting 7 days before the Gregorian month start
    start_date = datetime.date(year, month, 1) - datetime.timedelta(days=7)
    end_date = start_date + datetime.timedelta(days=75)
    
    daily_active: Dict[datetime.date, Set[int]] = {}
    sunrise_tithis: Dict[datetime.date, int] = {}
    
    curr = start_date
    while curr <= end_date:
        if hasattr(provider, 'is_adhik_month') and provider.is_adhik_month(curr, lat, lon):
            curr += datetime.timedelta(days=1)
            continue
        sunrise = provider.get_sunrise(curr, lat, lon)
        jain_cutoff = sunrise + datetime.timedelta(minutes=144)
        
        t_sunrise = provider.get_tithi_at_time(sunrise, lat, lon)
        t_cutoff = provider.get_tithi_at_time(jain_cutoff, lat, lon)
        
        daily_active[curr] = {t_sunrise, t_cutoff}
        sunrise_tithis[curr] = t_sunrise
        curr += datetime.timedelta(days=1)
        
    # Find the FIRST Krishna Pratipada (Tithi 16) in our search window that matches target start month
    start_day = None
    for d in sorted(daily_active.keys()):
        if KRISHNA_PRATIPADA in daily_active[d]:
            d_month = provider.get_hindu_month_name(d, lat, lon).upper()
            if d_month == target_start_amanta:
                start_day = d
                break

    if not start_day:
        return None

    # Collect ~31 fasting days until the NEXT Krishna Pratipada begins (and include it)
    vrat_days: List[datetime.date] = [start_day]
    curr = start_day + datetime.timedelta(days=1)
    
    while curr <= start_day + datetime.timedelta(days=33):
        if curr in daily_active:
            # Stop when we hit the next cycle's Krishna Pratipada in the target end month
            d_month = provider.get_hindu_month_name(curr, lat, lon).upper()
            if KRISHNA_PRATIPADA in daily_active[curr] and len(vrat_days) >= 28 and d_month == target_end_amanta:
                # Check for Vriddhi of the ending Pratipada on the consecutive day
                next_day = curr + datetime.timedelta(days=1)
                if next_day in daily_active and KRISHNA_PRATIPADA in daily_active[next_day]:
                    vrat_days.append(curr)
                    vrat_days.append(next_day)
                else:
                    vrat_days.append(curr)
                break
            vrat_days.append(curr)
        curr += datetime.timedelta(days=1)

    end_day = vrat_days[-1]
    total_days = len(vrat_days)

    has_kshaya = total_days < 30
    has_vriddhi = total_days > 30

    # Map 16 Virtues evenly across total_days
    daily_schedule: List[DailySchedule] = []
    
    for i, day_date in enumerate(vrat_days):
        virtue_idx = min(int((i / total_days) * 16), 15)
        virtue_name = VIRTUES[virtue_idx]
        
        t_sr = sunrise_tithis.get(day_date, 0)
        
        note = None
        if i > 0 and sunrise_tithis.get(vrat_days[i-1]) == t_sr:
            note = f"Vriddhi Day (Repeat of Tithi {t_sr})"

        daily_schedule.append(DailySchedule(
            date=day_date.strftime("%Y-%m-%d"),
            tithi_index=t_sr,
            virtue=virtue_name,
            note=note
        ))

    return ShodashkaranSchedule(
        cycle_name=cycle_name,
        start_date=start_day.strftime("%Y-%m-%d"),
        end_date=end_day.strftime("%Y-%m-%d"),
        total_days=total_days,
        has_kshaya=has_kshaya,
        has_vriddhi=has_vriddhi,
        daily_schedule=daily_schedule
    )

from .provider import SwissEphTithiProvider
