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
            
            # Fast Jain tithi index
            reference_jd = sunrise_jd + (2.4 / 24.0)
            sun_lon_j = get_planetary_longitude(reference_jd, 'Sun', ayanamsa)
            moon_lon_j = get_planetary_longitude(reference_jd, 'Moon', ayanamsa)
            jain_tithi_idx = get_tithi(sun_lon_j, moon_lon_j)
            
            hindu_month, _, is_adhika = get_hindu_month(sunrise_jd, ayanamsa)

            
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
                "paksha": "Shukla" if jain_tithi_idx <= 15 else "Krishna",
                "tithi_in_paksha": jain_tithi_idx if jain_tithi_idx <= 15 else jain_tithi_idx - 15,
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

    # Filter occurrences to strictly match the requested year
    festivals = [f for f in festivals if f["start_date"].startswith(str(year))]

    # Sort occurrences by start date

    # Add Rohini Nakshatra Parv Vrat
    from .vrats.rohini import evaluate_rohini_vrat, SwissEphPanchangProvider
    import datetime
    
    provider = SwissEphPanchangProvider(ayanamsa=ayanamsa)
    start_date_obj = datetime.date(year, 1, 1)
    end_date_obj = datetime.date(year, 12, 31)
    
    try:
        rohini_dates = evaluate_rohini_vrat(start_date_obj, end_date_obj, lat, lon, provider)
        for r_date in rohini_dates:
            d_str = r_date.strftime("%Y-%m-%d")
            festivals.append({
                "occurrence_id": "rohini_vrat",
                "name": "Rohini Nakshatra Parv Vrat",
                "category": "parva",
                "start_date": d_str,
                "end_date": d_str,
                "status": "confirmed",
                "jain_month": "Nakshatra:",
                "paksha": "Rohini",
                "tithi": " "
            })
    except Exception as e:
        print(f"Error calculating Rohini Vrat: {e}")


    # Add Bhaktambar Vrat (Every month, both Pakshas)
    from .vrats.bhaktambar import calculate_bhaktambar_vrat, SwissEphTithiProvider
    
    tithi_provider = SwissEphTithiProvider(ayanamsa=ayanamsa)
    
    for m in range(1, 13):
        for p in ["SHUKLA", "KRISHNA"]:
            try:
                vrat = calculate_bhaktambar_vrat(year, m, p, lat, lon, tithi_provider)
                if vrat:
                    festivals.append({
                        "occurrence_id": f"bhaktambar_vrat_{year}_{m}_{p.lower()}",
                        "name": f"{p.capitalize()} Bhaktambar Vrat",
                        "category": "parva",
                        "start_date": vrat.start_date,
                        "end_date": vrat.end_date,
                        "status": "confirmed",
                        "duration_days": vrat.total_fasting_days,
                        "has_kshaya": vrat.has_kshaya,
                        "has_vriddhi": vrat.has_vriddhi
                    })
            except Exception as e:
                print(f"Error calculating Bhaktambar Vrat for {year}-{m} {p}: {e}")


    # Add Daslakshan, Ratnatraya, Ashtahnika, Shodashkaran, Ravivara, Karma Nirjara
    from .vrats.daslakshan import calculate_daslakshan_vrat, SwissEphTithiProvider as SETP_Das
    from .vrats.ratnatraya import calculate_ratnatraya_vrat, SwissEphTithiProvider as SETP_Rat
    from .vrats.ashtahnika import calculate_ashtahnika_vrat, SwissEphTithiProvider as SETP_Ash
    from .vrats.shodashkaran import calculate_shodashkaran_vrat, SwissEphTithiProvider as SETP_Sho
    from .vrats.ravivara import calculate_ravivara_vrat, SwissEphTithiProvider as SETP_Rav
    from .vrats.karma_nirjara import calculate_karma_nirjara_vrat, SwissEphTithiProvider as SETP_KN
    
    # Map months to their approx python int representations (simplified for loop injection)
    # Bhadrapada = 8/9, Magha = 1/2, Chaitra = 3/4, Ashadha = 6/7, Kartika = 10/11, Phalguna = 2/3, Ashvina = 9/10, Vaishakha = 4/5, Shravana = 7/8
    # Actually, the python loops scan the solar months. The functions find the correct month regardless of the exact integer as long as the search window hits it.
    
    # 1. Daslakshan
    
    def get_greg_month(h_name, paksha, target_tithi=1):
        base_name = h_name.split("_")[0].upper()
        for s in snapshots:
            if s["hindu_month"].upper() == base_name and s["paksha"].upper() == paksha.upper() and not s["is_adhika"]:
                if s["tithi_in_paksha"] == target_tithi:
                    return s["date"].month
        # Fallback to first day of paksha
        for s in snapshots:
            if s["hindu_month"].upper() == base_name and s["paksha"].upper() == paksha.upper() and not s["is_adhika"]:
                return s["date"].month
        return {"ASHADHA": 6, "KARTIKA": 10, "PHALGUNA": 2, "BHADRAPADA": 8, "MAGHA": 1, "CHAITRA": 3, "ASHVINA": 10, "SHRAVANA": 7}.get(base_name, 1)

    for _, p_name in [(8, "BHADRAPADA"), (1, "MAGHA"), (3, "CHAITRA")]:
        try:
            p_month = get_greg_month(p_name, "Shukla", 5)
            vrat = calculate_daslakshan_vrat(year, p_month, p_name, lat, lon, SETP_Das(ayanamsa))
            if vrat and hasattr(vrat, 'daily_schedule'):
                festivals.append({
                    "occurrence_id": f"daslakshan_{p_name}_{year}",
                    "name": f"Daslakshan Parv",
                    "category": "mahaparv",
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                    "meaning": "10-day observation of supreme virtues.",
                    "observance": "Fasting, introspection, discourses.",
                    "daily_schedule": [{"date": d.date, "virtue": d.virtue} for d in vrat.daily_schedule]
                })
        except Exception as e:
            pass
    # 2. Ratnatraya
    for _, p_name in [(8, "BHADRAPADA"), (1, "MAGHA"), (3, "CHAITRA")]:
        try:
            p_month = get_greg_month(p_name, "Shukla", 13)
            vrat = calculate_ratnatraya_vrat(year, p_month, p_name, lat, lon, SETP_Rat(ayanamsa))
            if vrat:
                festivals.append({
                    "occurrence_id": f"ratnatraya_{p_name}_{year}",
                    "name": f"Ratnatraya Vrat ({p_name})",
                    "category": "parva",
                    "start_date": vrat.fast_start_date,
                    "end_date": vrat.fast_end_date,
                    "status": "confirmed",
                })
        except Exception as e:
            pass
            
    # 3. Ashtahnika
    for _, p_name in [(10, "KARTIKA"), (2, "PHALGUNA"), (6, "ASHADHA")]:
        try:
            p_month = get_greg_month(p_name, "Shukla", 8)
            print(f'DEBUG: Ashtahnika p_name={p_name}, p_month={p_month}')
            vrat = calculate_ashtahnika_vrat(year, p_month, p_name, lat, lon, SETP_Ash(ayanamsa))
            if vrat:
                festivals.append({
                    "occurrence_id": f"ashtahnika_{p_name}_{year}",
                    "name": f"Ashtahnika Mahaparv ({p_name})",
                    "category": "mahaparv",
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                })
        except Exception as e:
            print(f"Exception in Ashtahnika {p_name}: {e}")

    # 4. Shodashkaran
    shodashkaran_amanta_starts = {
        "BHADRAPADA_ASHVINA": "ASHADHA",
        "MAGHA_PHALGUNA": "PAUSHA",
        "CHAITRA_VAISHAKHA": "PHALGUNA"
    }
    for _, p_name in [(8, "BHADRAPADA_ASHVINA"), (1, "MAGHA_PHALGUNA"), (3, "CHAITRA_VAISHAKHA")]:
        try:
            amanta_start = shodashkaran_amanta_starts[p_name]
            p_month = get_greg_month(amanta_start, "Krishna", 1)
            vrat = calculate_shodashkaran_vrat(year, p_month, p_name, lat, lon, SETP_Sho(ayanamsa))
            if vrat:
                festivals.append({
                    "occurrence_id": f"shodashkaran_{p_name}_{year}",
                    "name": f"Shodashkaran Vrat ({p_name})",
                    "category": "parva",
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                })
        except Exception as e:
            pass

    # 5. Ravivara
    try:
        vrat = calculate_ravivara_vrat(year, lat, lon, SETP_Rav(ayanamsa))
        if vrat:
            festivals.append({
                "occurrence_id": f"ravivara_{year}",
                "name": f"Ravivara Vrat",
                "category": "parva",
                "start_date": vrat.start_date,
                "end_date": vrat.end_date,
                "status": "confirmed",
            })
    except Exception as e:
        pass
        
    # 6. Karma Nirjara
    for _, p_name in [(9, "ASHVINA"), (3, "CHAITRA"), (6, "ASHADHA"), (7, "SHRAVANA"), (8, "BHADRAPADA")]:
        try:
            p_month = get_greg_month(p_name, "Shukla")
            vrat = calculate_karma_nirjara_vrat(year, p_month, p_name, lat, lon, SETP_KN(ayanamsa))
            if vrat:
                if vrat.vrat_dates: # Vriddhi
                    start = vrat.vrat_dates[0]
                    end = vrat.vrat_dates[-1]
                else:
                    start = vrat.vrat_date
                    end = vrat.vrat_date
                festivals.append({
                    "occurrence_id": f"karma_nirjara_{p_name}_{year}",
                    "name": f"Karma Nirjara Vrat ({p_name})",
                    "category": "parva",
                    "start_date": start,
                    "end_date": end,
                    "status": "confirmed",
                })
        except Exception as e:
            pass

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
