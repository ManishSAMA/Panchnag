# jain_festival_service.py - location-aware Shwetambar Jain festival occurrence generation.

import calendar
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from astronomy import get_planetary_longitude
from panchang import get_tithi, get_hindu_month, calculate_jain_tithi_from_sunrise
from panchang_service import resolve_location, _calculate_daily_events
from jain_festival_rules import FESTIVAL_REGISTRY

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
            sun_lon = get_planetary_longitude(events.sunrise_jd, 'Sun', ayanamsa)
            moon_lon = get_planetary_longitude(events.sunrise_jd, 'Moon', ayanamsa)
            tithi_idx = get_tithi(sun_lon, moon_lon)
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

    # Helper to clean up profile matches
    def matches_profile(rule_profiles):
        return profile in rule_profiles or "all" in rule_profiles

    # 2. Resolve multi-day and special events first
    # A. Samvatsari
    samvatsari_date = None
    samvatsari_rule = None
    if profile == "shwetambar_murtipujak_tapagachchha":
        target_tithi = 4  # Chaturthi
        samvatsari_id = "samvatsari_tapagachchha"
    else:
        target_tithi = 5  # Panchami
        samvatsari_id = "samvatsari_sthanakvasi" if profile == "shwetambar_sthanakvasi" else "samvatsari_terapanthi"

    # Find matching Bhadrapada Shukla snapshots
    bhadrapada_matches = [
        s for s in snapshots
        if s["hindu_month"] == "Bhadrapada" and not s["is_adhika"] and s["paksha"] == "Shukla"
    ]
    
    samvatsari_candidates = [s for s in bhadrapada_matches if s["tithi_in_paksha"] == target_tithi]
    
    if samvatsari_candidates:
        if len(samvatsari_candidates) > 1:
            # Vriddhi: Tapagachchha uses second_day, others use first_day
            if profile == "shwetambar_murtipujak_tapagachchha":
                samvatsari_date = samvatsari_candidates[1]["date"]
            else:
                samvatsari_date = samvatsari_candidates[0]["date"]
        else:
            samvatsari_date = samvatsari_candidates[0]["date"]
    else:
        # Kshaya: Find first day whose Tithi is strictly > target_tithi
        next_days = [s for s in bhadrapada_matches if s["tithi_in_paksha"] > target_tithi]
        if next_days:
            samvatsari_date = next_days[0]["date"]

    # Append Samvatsari if found
    if samvatsari_date:
        rule = next(r for r in FESTIVAL_REGISTRY if r["id"] == samvatsari_id)
        samvatsari_occurrence = {
            "id": rule["id"],
            "occurrence_id": f"{rule['id']}:{samvatsari_date.isoformat()}",
            "name": rule["name"],
            "name_gujarati": rule["name_gujarati"],
            "category": rule["category"],
            "start_date": samvatsari_date.isoformat(),
            "end_date": samvatsari_date.isoformat(),
            "jain_month": "Bhadrapada",
            "paksha": "Shukla",
            "tithi": target_tithi,
            "profile": profile,
            "status": "confirmed",
            "meaning": rule["meaning"],
            "observance": rule["observance"],
            "sources": rule["sources"]
        }
        festivals.append(samvatsari_occurrence)
        
        # B. Paryushan Start (exactly 7 days before Samvatsari)
        paryushan_start = samvatsari_date - timedelta(days=7)
        if profile == "shwetambar_murtipujak_tapagachchha":
            paryushan_rule_id = "paryushan_start_tapagachchha"
        else:
            paryushan_rule_id = f"paryushan_start_{profile.removeprefix('shwetambar_')}"
        paryushan_rule = next(r for r in FESTIVAL_REGISTRY if r["id"] == paryushan_rule_id)
        
        festivals.append({
            "id": paryushan_rule["id"],
            "occurrence_id": f"{paryushan_rule['id']}:{paryushan_start.isoformat()}",
            "name": paryushan_rule["name"],
            "name_gujarati": paryushan_rule["name_gujarati"],
            "category": paryushan_rule["category"],
            "start_date": paryushan_start.isoformat(),
            "end_date": samvatsari_date.isoformat(),  # Spans to Samvatsari
            "jain_month": "Bhadrapada",
            "paksha": "Krishna",
            "tithi": 12 if profile == "shwetambar_murtipujak_tapagachchha" else 13,
            "profile": profile,
            "status": "confirmed",
            "meaning": paryushan_rule["meaning"],
            "observance": paryushan_rule["observance"],
            "sources": paryushan_rule["sources"]
        })

    # C. Ayambil Oli (Chaitra and Ashwin)
    for oli_id, target_month in [("ayambil_oli_chaitra", "Chaitra"), ("ayambil_oli_ashvin", "Ashwin")]:
        oli_matches = [
            s for s in snapshots
            if s["hindu_month"] == target_month and not s["is_adhika"] and s["paksha"] == "Shukla"
        ]
        
        # Find start of Shukla 7
        shukla_7_day = [s for s in oli_matches if s["tithi_in_paksha"] == 7]
        if shukla_7_day:
            start_oli_date = shukla_7_day[0]["date"]
        else:
            # Kshaya handling: find first available after Shukla 7
            next_avail = [s for s in oli_matches if s["tithi_in_paksha"] > 7]
            if next_avail:
                start_oli_date = next_avail[0]["date"]
            else:
                start_oli_date = None
                
        if start_oli_date:
            end_oli_date = start_oli_date + timedelta(days=8)  # exactly 9 consecutive days
            rule = next(r for r in FESTIVAL_REGISTRY if r["id"] == oli_id)
            festivals.append({
                "id": rule["id"],
                "occurrence_id": f"{rule['id']}:{start_oli_date.isoformat()}",
                "name": rule["name"],
                "name_gujarati": rule["name_gujarati"],
                "category": rule["category"],
                "start_date": start_oli_date.isoformat(),
                "end_date": end_oli_date.isoformat(),
                "jain_month": target_month,
                "paksha": "Shukla",
                "tithi": 7,
                "profile": profile,
                "status": "confirmed",
                "meaning": rule["meaning"],
                "observance": rule["observance"],
                "sources": rule["sources"]
            })

    # D. General Rule Matching (Single-day Kalyanaks, fasts, and Parva Tithis)
    for rule in FESTIVAL_REGISTRY:
        if not matches_profile(rule["profiles"]):
            continue
        # Skip special ones handled above
        if rule["id"] in [
            "samvatsari_tapagachchha", "samvatsari_sthanakvasi", "samvatsari_terapanthi",
            "paryushan_start_tapagachchha", "paryushan_start_sthanakvasi", "paryushan_start_terapanthi",
            "ayambil_oli_chaitra", "ayambil_oli_ashvin"
        ]:
            continue
            
        # Parse month, paksha, tithi rule
        target_month = rule["jain_month"]
        target_paksha = rule["paksha"]
        target_tithi = rule["tithi"]
        
        # We find matching snapshots
        matches = snapshots
        if target_month:
            matches = [s for s in matches if s["hindu_month"] == target_month and not s["is_adhika"]]
        if target_paksha:
            matches = [s for s in matches if s["paksha"] == target_paksha]
            
        # Group candidates by matching Udaya Tithi index within the paksha
        # Since Tithis repeat or skip, we do this carefully
        if isinstance(target_tithi, int):
            # We want to match this specific Tithi
            candidates = [s for s in matches if s["tithi_in_paksha"] == target_tithi]
            
            if candidates:
                # Handle Vriddhi (repeated Tithi)
                if len(candidates) > 1:
                    if rule["vriddhi_rule"] == "second_day":
                        resolved_day = candidates[1]["date"]
                    else:
                        resolved_day = candidates[0]["date"]
                else:
                    resolved_day = candidates[0]["date"]
                    
                festivals.append({
                    "id": rule["id"],
                    "occurrence_id": f"{rule['id']}:{resolved_day.isoformat()}",
                    "name": rule["name"],
                    "name_gujarati": rule["name_gujarati"],
                    "category": rule["category"],
                    "start_date": resolved_day.isoformat(),
                    "end_date": resolved_day.isoformat(),
                    "jain_month": target_month or "Every Month",
                    "paksha": target_paksha or "Both",
                    "tithi": target_tithi,
                    "profile": profile,
                    "status": "confirmed",
                    "meaning": rule["meaning"],
                    "observance": rule["observance"],
                    "sources": rule["sources"]
                })
            else:
                # Kshaya (skipped Tithi): find first day whose Tithi is strictly > target_tithi
                # (only for specific single-day festivals, not recurring monthly ones to avoid duplicate mappings)
                if target_month:
                    next_days = [s for s in matches if s["tithi_in_paksha"] > target_tithi]
                    if next_days:
                        resolved_day = next_days[0]["date"]
                        festivals.append({
                            "id": rule["id"],
                            "occurrence_id": f"{rule['id']}:{resolved_day.isoformat()}",
                            "name": rule["name"],
                            "name_gujarati": rule["name_gujarati"],
                            "category": rule["category"],
                            "start_date": resolved_day.isoformat(),
                            "end_date": resolved_day.isoformat(),
                            "jain_month": target_month,
                            "paksha": target_paksha,
                            "tithi": target_tithi,
                            "profile": profile,
                            "status": "confirmed",
                            "meaning": rule["meaning"],
                            "observance": rule["observance"],
                            "sources": rule["sources"]
                        })

    # Sort occurrences by start date
    festivals.sort(key=lambda x: x["start_date"])

    # 3. Calculate upcoming section (important observances in next 30 days)
    # Since we don't have current date passed in, we can dynamically check from today's date in local time,
    # or just return festivals in the next 30 days from May 31, 2026 as reference, or first 30 days from start_date.
    # Let's filter occurrences starting from a reference date (default: local current date or start of the year)
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
