import calendar
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from astronomy import get_planetary_longitude
from panchang import get_tithi, get_hindu_month, calculate_jain_tithi_from_sunrise, generate_daily_panchang
from panchang_service import resolve_location, _calculate_daily_events
from jain_festival_rules import FESTIVAL_REGISTRY, RuleFactory

def generate_jain_festivals(
    year: int,
    lat: float,
    lon: float,
    ayanamsa: str = "Lahiri",
    profile: str = "shwetambar_murtipujak_tapagachchha"
) -> dict:
    """Generate all Jain festivals for a given year and location, filtered by profile."""
    location = resolve_location(lat=lat, lon=lon)
    tz_name = location.timezone
    
    # 1. Generate daily Panchang snapshots for the entire year
    snapshots = []
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    curr = start_date
    while curr <= end_date:
        try:
            events = _calculate_daily_events(curr, location)
            daily_panchang = generate_daily_panchang(events.sunrise_jd, ayanamsa, local_date=curr)
            tithi_idx = daily_panchang["Tithi_Index"]
            hindu_month, _, is_adhika = get_hindu_month(events.sunrise_jd, ayanamsa)
            jain_tithi_data = calculate_jain_tithi_from_sunrise(events.sunrise_jd, ayanamsa)
            
            # Clean month name (e.g. strip Adhika for standard matching)
            base_month = hindu_month.removeprefix("Adhika ")
            
            snapshots.append({
                "date": curr,
                "sunrise_jd": events.sunrise_jd,
                "tithi": tithi_idx,
                "jain_tithi": jain_tithi_data["Jain_Tithi_Index"],
                "jain_tithi_name": jain_tithi_data["Jain_Tithi_Name"],
                "hindu_month": base_month,
                "is_adhika": is_adhika,
                "paksha": "Shukla" if tithi_idx <= 15 else "Krishna",
                "tithi_in_paksha": tithi_idx if tithi_idx <= 15 else tithi_idx - 15,
            })
        except Exception:
            # Fallback if astro fails
            pass
        curr += timedelta(days=1)

    festivals = []
    context = {}

    # 2. Process rules
    rules = [RuleFactory.create(conf) for conf in FESTIVAL_REGISTRY]
    
    independent_rules = [r for r in rules if r.config.get("rule_type") != "Relative"]
    relative_rules = [r for r in rules if r.config.get("rule_type") == "Relative"]

    for rule in independent_rules:
        if not rule.matches_profile(profile):
            continue
        occurrences = rule.resolve(snapshots, profile, context)
        context[rule.id] = occurrences
        festivals.extend(occurrences)

    for rule in relative_rules:
        if not rule.matches_profile(profile):
            continue
        occurrences = rule.resolve(snapshots, profile, context)
        context[rule.id] = occurrences
        festivals.extend(occurrences)

    # Sort occurrences by start date
    festivals.sort(key=lambda x: x["start_date"])

    # 3. Calculate upcoming section
    ref_date = date.today()
    if ref_date.year != year:
        ref_date = date(year, 1, 1)
        
    upcoming_limit = ref_date + timedelta(days=30)
    upcoming = [
        f for f in festivals
        if ref_date.isoformat() <= f["start_date"] <= upcoming_limit.isoformat()
    ]

    return {
        "year": year,
        "location": {
            "name": location.name,
            "lat": location.lat,
            "lon": location.lon,
            "timezone": tz_name
        },
        "profile": profile,
        "upcoming": upcoming,
        "festivals": festivals
    }
