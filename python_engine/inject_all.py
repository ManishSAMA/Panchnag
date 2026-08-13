import datetime
with open('jain_observances/festival_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = -1
for i, line in enumerate(lines):
    if 'festivals.sort(key=lambda x: x["start_date"])' in line:
        insert_idx = i
        break

injection = '''
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
    for p_month, p_name in [(8, "BHADRAPADA"), (1, "MAGHA"), (3, "CHAITRA")]:
        try:
            vrat = calculate_daslakshan_vrat(year, p_month, p_name, lat, lon, SETP_Das(ayanamsa))
            if vrat:
                festivals.append({
                    "occurrence_id": f"daslakshan_{p_name}_{year}",
                    "name": f"Daslakshan Mahaparv ({p_name})",
                    "category": "parva",
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                    "duration_days": vrat.total_days,
                })
        except Exception as e:
            pass

    # 2. Ratnatraya
    for p_month, p_name in [(8, "BHADRAPADA"), (1, "MAGHA"), (3, "CHAITRA")]:
        try:
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
    for p_month, p_name in [(10, "KARTIKA"), (2, "PHALGUNA"), (6, "ASHADHA")]:
        try:
            vrat = calculate_ashtahnika_vrat(year, p_month, p_name, lat, lon, SETP_Ash(ayanamsa))
            if vrat:
                festivals.append({
                    "occurrence_id": f"ashtahnika_{p_name}_{year}",
                    "name": f"Ashtahnika Mahaparv ({p_name})",
                    "category": "parva",
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                })
        except Exception as e:
            pass

    # 4. Shodashkaran
    for p_month, p_name in [(8, "BHADRAPADA_ASHVINA"), (1, "MAGHA_PHALGUNA"), (3, "CHAITRA_VAISHAKHA")]:
        try:
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
    for p_month, p_name in [(9, "ASHVINA"), (3, "CHAITRA"), (6, "ASHADHA"), (7, "SHRAVANA"), (8, "BHADRAPADA")]:
        try:
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

'''

if insert_idx != -1:
    lines.insert(insert_idx, injection)
    with open('jain_observances/festival_service.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Injected all vrats.")
else:
    print("Could not find insertion point!")
