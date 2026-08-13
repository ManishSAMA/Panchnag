import datetime
with open('jain_observances/festival_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = -1
for i, line in enumerate(lines):
    if 'festivals.sort(key=lambda x: x["start_date"])' in line:
        insert_idx = i
        break

injection = '''
    # Add Rohini Nakshatra Parv Vrat
    from .vrats.rohini import evaluate_rohini_vrat, SwissEphPanchangProvider
    import datetime
    
    provider = SwissEphPanchangProvider(ayanamsa=ayanamsa_name)
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
                "status": "confirmed"
            })
    except Exception as e:
        print(f"Error calculating Rohini Vrat: {e}")

'''

if insert_idx != -1:
    lines.insert(insert_idx, injection)
    with open('jain_observances/festival_service.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Injected Rohini logic.")
else:
    print("Could not find insertion point!")
