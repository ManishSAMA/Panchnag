import calendar
from functools import lru_cache
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from astronomy import get_planetary_longitude, get_sunrise, local_date_anchor_jd
from panchang import get_tithi, get_hindu_month, calculate_jain_tithi_from_sunrise
from panchang_service import resolve_location
from .registry import FESTIVAL_REGISTRY
from .festival_rules import RuleFactory

@lru_cache(maxsize=32)
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
    
    # 1. Generate daily Panchang snapshots for a 14-month window (Dec 1 of previous year to Jan 31 of next year)
    snapshots = []
    start_date = date(year - 1, 12, 1)
    end_date = date(year + 1, 1, 31)
    curr = start_date
    while curr <= end_date:
        try:
            day_start_jd = local_date_anchor_jd(curr, tz_name, hour=0)
            sunrise_jd = get_sunrise(day_start_jd, lat, lon)
            sun_lon = get_planetary_longitude(sunrise_jd, 'Sun', ayanamsa)
            moon_lon = get_planetary_longitude(sunrise_jd, 'Moon', ayanamsa)
            tithi_idx = get_tithi(sun_lon, moon_lon)
            
            # Fast Jain tithi index and month
            reference_jd = sunrise_jd + (2.4 / 24.0)
            sun_lon_j = get_planetary_longitude(reference_jd, 'Sun', ayanamsa)
            moon_lon_j = get_planetary_longitude(reference_jd, 'Moon', ayanamsa)
            jain_tithi_idx = get_tithi(sun_lon_j, moon_lon_j)
            
            hindu_month, _, is_adhika = get_hindu_month(reference_jd, ayanamsa)

            
            # Clean month name (e.g. strip Adhika for standard matching)
            base_month = hindu_month.removeprefix("Adhika ")
            
            snapshots.append({
                "date": curr,
                "sunrise_jd": sunrise_jd,
                "tithi": tithi_idx,
                "jain_tithi": jain_tithi_idx,
                "jain_tithi_name": "", # Unused by logic engine
                "hindu_month": base_month,
                "is_adhika": is_adhika,
                "paksha": "Shukla" if tithi_idx <= 15 else "Krishna",
                "tithi_in_paksha": tithi_idx if tithi_idx <= 15 else tithi_idx - 15,
                "jain_paksha": "Shukla" if jain_tithi_idx <= 15 else "Krishna",
                "jain_tithi_in_paksha": jain_tithi_idx if jain_tithi_idx <= 15 else jain_tithi_idx - 15,
            })
        except Exception:
            # Fallback if astro fails
            pass
        curr += timedelta(days=1)

    festivals = []
    context = {"lat": lat, "lon": lon, "ayanamsa": ayanamsa, "year": year}

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

    # Filter occurrences to strictly match the requested year
    festivals = [f for f in festivals if f["start_date"].startswith(str(year))]

    # Post-process: ensure all occurrences have valid jain_month, paksha, tithi, and metadata
    date_to_snap = {s["date"].isoformat(): s for s in snapshots}
    TITHI_LABEL_MAP = {
        1: "Ekam (1)", 2: "Dwitiya (2)", 3: "Tritiya (3)", 4: "Chaturthi (4)", 5: "Panchami (5)",
        6: "Shasthi (6)", 7: "Saptami (7)", 8: "Ashtami (8)", 9: "Navami (9)", 10: "Dashami (10)",
        11: "Ekadashi (11)", 12: "Dwadashi (12)", 13: "Trayodashi (13)", 14: "Chaturdashi (14)",
        15: "Purnima (15)"
    }

    for f in festivals:
        f["id"] = f.get("id", f.get("occurrence_id", f.get("name", "")))
        f.setdefault("name_hindi", f.get("name_hindi", f["name"]))
        f.setdefault("meaning", f.get("meaning", f["name"]))
        f.setdefault("observance", f.get("observance", "Vrat observance and prayer"))
        f.setdefault("sources", f.get("sources", []))
        
        # Normalize jain_month, paksha, and format tithi if possible
        if f.get("jain_month") != "Nakshatra:":
            snap = date_to_snap.get(f["start_date"])
            if snap:
                prefix = ""
                if snap["is_adhika"]:
                    prefix = "Adhika "
                elif any(s["hindu_month"] == snap["hindu_month"] and s["is_adhika"] and s["date"].year == snap["date"].year for s in snapshots):
                    prefix = "Nija "
                
                # Apply Purnimanta Shift: If Krishna paksha, month is actually +1
                base_month = snap["hindu_month"]
                if snap["paksha"] == "Krishna":
                    m_names = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwin", "Kartika", "Agrahayana", "Pausha", "Magha", "Phalguna"]
                    if base_month in m_names:
                        idx = m_names.index(base_month)
                        base_month = m_names[(idx + 1) % 12]
                
                f["jain_month"] = prefix + base_month
                f["paksha"] = snap["paksha"]
                
                # Format Tithi
                t_val = f.get("tithi")
                t_num = snap["tithi_in_paksha"]
                if isinstance(t_val, int) or not t_val:
                    # Use the snap's tithi if not provided, or format the integer provided
                    use_num = t_val if isinstance(t_val, int) else t_num
                    t_name = TITHI_LABEL_MAP.get(use_num, f"Tithi {use_num}")
                    if snap["paksha"] == "Krishna" and use_num == 15:
                        t_name = "Amavasya (15)"
                    f["tithi"] = t_name
            else:
                if not f.get("jain_month"): f["jain_month"] = "—"
                if not f.get("paksha"): f["paksha"] = ""
                if not f.get("tithi"): f["tithi"] = "—"

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

    panchang_tithi_map = {}
    for s in snapshots:
        t_num = s["tithi_in_paksha"]
        t_name = TITHI_LABEL_MAP.get(t_num, f"Tithi {t_num}")
        if s["paksha"] == "Krishna" and t_num == 15:
            t_name = "Amavasya (15)"
        
        prefix = ""
        if s["is_adhika"]:
            prefix = "Adhika "
        elif any(x["hindu_month"] == s["hindu_month"] and x["is_adhika"] and x["date"].year == s["date"].year for x in snapshots):
            prefix = "Nija "
            
        base_month = s["hindu_month"]
        if s["paksha"] == "Krishna":
            m_names = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwin", "Kartika", "Agrahayana", "Pausha", "Magha", "Phalguna"]
            if base_month in m_names:
                idx = m_names.index(base_month)
                base_month = m_names[(idx + 1) % 12]
                
        panchang_tithi_map[s["date"].isoformat()] = f"{prefix}{base_month} {s['paksha']} {t_name}"

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
        "festivals": festivals,
        "panchang_tithi_map": panchang_tithi_map
    }
