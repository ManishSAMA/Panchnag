import datetime
with open('jain_observances/festival_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = -1
for i, line in enumerate(lines):
    if 'festivals.sort(key=lambda x: x["start_date"])' in line:
        insert_idx = i
        break

injection = '''
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

'''

if insert_idx != -1:
    lines.insert(insert_idx, injection)
    with open('jain_observances/festival_service.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Injected Bhaktambar logic.")
else:
    print("Could not find insertion point!")
