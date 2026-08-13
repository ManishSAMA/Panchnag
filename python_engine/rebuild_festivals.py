import json
import re

raw_text = """
1. Shravan Month (July–August)
Shravan Krishna Paksha (Waning Moon Phase):

Badi Ekam (1st day): Veer Shasan Jayanti (The day Lord Mahavira delivered his first divine sermon).
Badi Dwitiya (2nd day): Shri Munisuvratnath Ji - Garbh Kalyanak (Conception event).
Badi Dashami (10th day): Shri Kunthunath Ji - Garbh Kalyanak (Conception event).

Shravan Shukla Paksha (Waxing Moon Phase):

Sudi Dwitiya (2nd day): Shri Sumatinath Ji - Garbh Kalyanak (Conception event).
Sudi Shasthi (6th day): Shri Neminath Ji - Janma & Tap Kalyanak (Birth and Penance/Renunciation).
Sudi Saptami (7th day): Shri Parshvanath Ji - Moksha Kalyanak (Liberation/Salvation).
Sudi Purnima (Full Moon): Shri Shreyansnath Ji - Moksha Kalyanak (Liberation/Salvation).

2. Bhadrapad Month (August–September)
Bhadrapad Krishna Paksha (Waning Moon Phase):

Badi Dwitiya (2nd day): Shri Vasupujya Ji - Kevalgyan Kalyanak (Attainment of Omniscience/Enlightenment).
Badi Saptami (7th day): Shri Shantinath Ji - Garbh Kalyanak (Conception event).

Bhadrapad Shukla Paksha (Waxing Moon Phase):

Sudi Shasthi (6th day): Shri Suparshvanath Ji - Garbh Kalyanak (Conception event).
Sudi Chaturdashi (14th day): Shri Vasupujya Ji - Moksha Kalyanak (Liberation/Salvation).

3. Ashwin / Kwar Month (September–October)
Ashwin Krishna Paksha (Waning Moon Phase):

Badi Dwitiya (2nd day): Shri Naminath Ji - Garbh Kalyanak (Conception event).

Ashwin Shukla Paksha (Waxing Moon Phase):

Sudi Ekam (1st day): Shri Neminath Ji - Kevalgyan Kalyanak (Attainment of Omniscience/Enlightenment).
Sudi Ashtami (8th day): Shri Pushpadant Ji - Moksha Kalyanak (Liberation/Salvation).
Sudi Ashtami (8th day): Shri Sheetalnath Ji - Moksha Kalyanak (Liberation/Salvation).

4. Kartik Month (October–November)
Kartik Krishna Paksha (Waning Moon Phase):

Badi Ekam (1st day): Shri Anantnath Ji - Garbh Kalyanak (Conception event).
Badi Chaturthi (4th day): Shri Sambhavnath Ji - Kevalgyan Kalyanak (Attainment of Omniscience/Enlightenment).
Badi Amavasya (New Moon): Shri Mahavir Swami Ji - Moksha Kalyanak (The Nirvana/Liberation of Lord Mahavira, celebrated as Jain Diwali).

1. Kartik Shukla Paksha (Waxing Moon Phase)
Sudi Ekam (1st day): Veer Nirvana Prapti (Attainment of Liberation by Lord Mahavira)
Sudi Ekam (1st day): Shri Gautam Swami Gyan (Attainment of Omniscience by Gautam Swami)
Sudi Dwitiya (2nd day): Shri Pushpadant Ji - Kevalgyan (Enlightenment)
Sudi Shasthi (6th day): Shri Neminath Ji - Garbh (Conception)
Sudi Dwadashi (12th day): Shri Arahnath Ji - Kevalgyan (Enlightenment)
Sudi Trayodashi (13th day): Shri Padmaprabhu Ji - Janma, Tap (Birth and Penance)
Sudi Purnima (Full Moon): Shri Sambhavnath Ji - Janma (Birth)

2. Margashirsha (Agahan) Krishna Paksha (Waning Moon Phase)
Badi Dashami (10th day): Shri Mahavir Swami Ji - Tap (Penance)

3. Margashirsha (Agahan) Shukla Paksha (Waxing Moon Phase)
Sudi Ekam (1st day): Shri Pushpadant Ji - Janma, Tap (Birth and Penance)
Sudi Ekadashi (11th day): Shri Mallinath Ji - Janma, Tap (Birth and Penance)
Sudi Ekadashi (11th day): Shri Neminath Ji - Kevalgyan (Enlightenment)
Sudi Chaturdashi (14th day): Shri Arahnath Ji - Janma, Tap (Birth and Penance)
Sudi Purnima (Full Moon): Shri Sambhavnath Ji - Tap (Penance)

4. Paush Krishna Paksha (Waning Moon Phase)
Badi Dwitiya (2nd day): Shri Mallinath Ji - Kevalgyan (Enlightenment)
Badi Ekadashi (11th day): Shri Chandraprabhu Ji - Janma, Tap (Birth and Penance)
Badi Ekadashi (11th day): Shri Parshvanath Ji - Janma, Tap (Birth and Penance)
Badi Chaturdashi (14th day): Shri Sheetalnath Ji - Kevalgyan (Enlightenment)

5. Paush Shukla Paksha (Waxing Moon Phase)
Sudi Chaturthi (4th day): Shri Ajitnath Ji - Kevalgyan (Enlightenment)
Sudi Dashami (10th day): Shri Shantinath Ji - Kevalgyan (Enlightenment)
Sudi Chaturdashi (14th day): Shri Abhinandannath Ji - Kevalgyan (Enlightenment)
Sudi Purnima (Full Moon): Shri Dharmanath Ji - Kevalgyan (Enlightenment)

6. Magh Krishna Paksha (Waning Moon Phase)
Badi Shasthi (6th day): Shri Padmaprabhu Ji - Garbh (Conception)
Badi Dwadashi (12th day): Shri Sheetalnath Ji - Janma, Tap (Birth and Penance)
Badi Chaturdashi (14th day): Shri Adinath Ji - Moksha (Liberation)
Badi Amavas (New Moon): Shri Shreyansnath Ji - Kevalgyan (Enlightenment)

7. Magh Shukla Paksha (Waxing Moon Phase)
Sudi Chaturthi (4th day): Shri Vimalnath Ji - Janma, Tap (Birth and Penance)
Sudi Shasthi (6th day): Shri Vimalnath Ji - Kevalgyan (Enlightenment)
Sudi Dashami (10th day): Shri Ajitnath Ji - Janma, Tap (Birth and Penance)
Sudi Dwadashi (12th day): Shri Abhinandannath Ji - Janma, Tap (Birth and Penance)
Sudi Trayodashi (13th day): Shri Dharmanath Ji - Janma, Tap (Birth and Penance)

8. Phalgun Krishna Paksha (Waning Moon Phase)
Badi Chaturthi (4th day): Shri Padmaprabhu Ji - Moksha (Liberation)
Badi Shasthi (6th day): Shri Suparshvanath Ji - Kevalgyan (Enlightenment)
Badi Saptami (7th day): Shri Chandraprabhu Ji - Kevalgyan (Enlightenment)
Badi Saptami (7th day): Shri Suparshvanath Ji - Moksha (Liberation)
Badi Navami (9th day): Shri Pushpadant Ji - Garbh (Conception)
Badi Ekadashi (11th day): Shri Adinath Ji - Kevalgyan (Enlightenment)
Badi Ekadashi (11th day): Shri Shreyansnath Ji - Janma, Tap (Birth and Penance)
Badi Dwadashi (12th day): Shri Munisuvratnath Ji - Moksha (Liberation)
Badi Chaturdashi (14th day): Shri Vasupujya Ji - Janma, Tap (Birth and Penance)

9. Phalgun Shukla Paksha (Waxing Moon Phase)
Sudi Tritiya (3rd day): Shri Arahnath Ji - Garbh (Conception)
Sudi Panchami (5th day): Shri Mallinath Ji - Moksha (Liberation)
Sudi Saptami (7th day): Shri Chandraprabhu Ji - Moksha (Liberation)
Sudi Ashtami (8th day): Shri Sambhavnath Ji - Garbh (Conception)

10. Chaitra Krishna Paksha (Waning Moon Phase)
Badi Chaturthi (4th day): Shri Anantnath Ji - Moksha (Liberation)
Badi Chaturthi (4th day): Shri Parshvanath Ji - Kevalgyan (Enlightenment)
Badi Panchami (5th day): Shri Chandraprabhu Ji - Garbh (Conception)
Badi Ashtami (8th day): Shri Sheetalnath Ji - Garbh (Conception)
Badi Navami (9th day): Shri Adinath Ji - Janma, Tap (Birth and Penance)
Badi Amavas (New Moon): Shri Anantnath Ji - Kevalgyan (Enlightenment)

1. Chaitra Shukla Paksha (Waxing Moon Phase)
Sudi Ekam (1st day): Shri Mallinath Ji - Garbh (Conception)
Sudi Tritiya (3rd day): Shri Kunthunath Ji - Kevalgyan (Enlightenment)
Sudi Panchami (5th day): Shri Ajitnath Ji - Moksha (Liberation)
Sudi Shasthi (6th day): Shri Sambhavnath Ji - Moksha (Liberation)
Sudi Ekadashi (11th day): Shri Sumatinath Ji - Janma, Tap, Kevalgyan, Moksha (Birth, Penance, Enlightenment, and Liberation)
Sudi Ekadashi (11th day): Shri Arahnath Ji - Moksha (Liberation)
Sudi Trayodashi (13th day): Shri Mahavir Swami Ji - Janma (Birth / Mahavir Jayanti)
Sudi Purnima (Full Moon): Shri Padmaprabhu Ji - Kevalgyan (Enlightenment)

2. Vaishakh Krishna Paksha (Waning Moon Phase)
Badi Dwitiya (2nd day): Shri Parshvanath Ji - Garbh (Conception)
Badi Navami (9th day): Shri Munisuvratnath Ji - Kevalgyan (Enlightenment)
Badi Dasami (10th day): Shri Munisuvratnath Ji - Janma, Tap (Birth and Penance)
Badi Chaturdashi (14th day): Shri Naminath Ji - Moksha (Liberation)

3. Vaishakh Shukla Paksha (Waxing Moon Phase)
Sudi Ekam (1st day): Shri Kunthunath Ji - Janma, Tap, Moksha (Birth, Penance, and Liberation)
Sudi Shasthi (6th day): Shri Abhinandannath Ji - Garbh, Moksha (Conception and Liberation)
Sudi Ashtami (8th day): Shri Dharmanath Ji - Garbh (Conception)
Sudi Dashami (10th day): Shri Mahavir Swami Ji - Kevalgyan (Enlightenment)

4. Jyeshtha Krishna Paksha (Waning Moon Phase)
Badi Ashtami (8th day): Shri Shreyansnath Ji - Garbh (Conception)
Badi Dashami (10th day): Shri Vimalnath Ji - Garbh (Conception)
Badi Dwadashi (12th day): Shri Anantnath Ji - Janma, Tap (Birth and Penance)
Badi Chaturdashi (14th day): Shri Sheetalnath Ji - Janma, Tap, Moksha (Birth, Penance, and Liberation)
Badi Amavas (New Moon): Shri Ajitnath Ji - Garbh (Conception)

5. Jyeshtha Shukla Paksha (Waxing Moon Phase)
Sudi Chaturthi (4th day): Shri Dharmanath Ji - Moksha (Liberation)
Sudi Dwadashi (12th day): Shri Suparshvanath Ji - Janma, Tap (Birth and Penance)

6. Ashadh Krishna Paksha (Waning Moon Phase)
Badi Dwitiya (2nd day): Shri Munisuvratnath Ji - Garbh (Conception)
Badi Shasthi (6th day): Shri Vasupujya Ji - Garbh (Conception)
Badi Shasthi (6th day): Shri Vimalnath Ji - Moksha (Liberation)
Badi Dashami (10th day): Shri Naminath Ji - Janma, Tap (Birth and Penance)

7. Ashadh Shukla Paksha (Waxing Moon Phase)
Sudi Shasthi (6th day): Shri Mahavir Swami Ji - Garbh (Conception)
Sudi Ashtami (8th day): Shri Neminath Ji - Moksha (Liberation)
"""

month_map = {
    'Shravan': 'Shravana',
    'Bhadrapad': 'Bhadrapada',
    'Ashwin': 'Ashwin',
    'Kartik': 'Kartika',
    'Margashirsha': 'Margashirsha',
    'Paush': 'Pausha',
    'Magh': 'Magha',
    'Phalgun': 'Phalguna',
    'Chaitra': 'Chaitra',
    'Vaishakh': 'Vaishakha',
    'Jyeshtha': 'Jyeshtha',
    'Ashadh': 'Ashadha'
}

paksha_map = {
    'Badi': 'Krishna',
    'Sudi': 'Shukla'
}

tithi_map = {
    'Ekam': 1, 'Dwitiya': 2, 'Tritiya': 3, 'Chaturthi': 4, 'Panchami': 5,
    'Shasthi': 6, 'Saptami': 7, 'Ashtami': 8, 'Navami': 9, 'Dashami': 10,
    'Dasami': 10, 'Ekadashi': 11, 'Dwadashi': 12, 'Trayodashi': 13,
    'Chaturdashi': 14, 'Purnima': 15, 'Amavas': 15, 'Amavasya': 15
}

current_month = None
current_paksha = None
festivals = []

for line in raw_text.split('\n'):
    line = line.strip()
    if not line:
        continue
        
    for k, v in month_map.items():
        if re.search(r'\b' + k + r'\b', line, re.IGNORECASE) and 'Paksha' in line:
            current_month = v
            break
            
    if 'Month' in line:
        for k, v in month_map.items():
            if re.search(r'\b' + k + r'\b', line, re.IGNORECASE):
                current_month = v
                break
                
    paksha_match = re.search(r'(Krishna|Shukla)\s+Paksha', line, re.IGNORECASE)
    if paksha_match:
        current_paksha = paksha_match.group(1).capitalize()
        
    tithi_match = re.match(r'(Badi|Sudi)\s+([A-Za-z]+).*?:\s*(.*)', line, re.IGNORECASE)
    if tithi_match:
        paksha_prefix = tithi_match.group(1).capitalize()
        tithi_str = tithi_match.group(2).capitalize()
        name_raw = tithi_match.group(3).strip()
        
        name_clean = re.sub(r'\s*\(.*?\)$', '', name_raw).strip()
        
        paksha = paksha_map.get(paksha_prefix, current_paksha)
        tithi = tithi_map.get(tithi_str, 1)
        
        cat = 'kalyanak'
        if 'Diwali' in name_raw or 'Moksha' in name_raw:
            cat = 'festival' if 'Diwali' in name_raw else 'kalyanak'
            
        fest = {
            'id': re.sub(r'[^a-z0-9_]', '_', name_clean.lower()).strip('_'),
            'name': name_clean,
            'category': cat,
            'profiles': ['all'],
            'rule_type': 'SingleTithi',
            'jain_month': current_month,
            'paksha': paksha,
            'tithi': tithi
        }
        festivals.append(fest)

with open('jain_festival_rules.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('FESTIVAL_REGISTRY = [')
prefix = text[:start_idx]

registry_str = 'FESTIVAL_REGISTRY = [\n'
for fest in festivals:
    registry_str += '    {\n'
    registry_str += f'        "id": "{fest["id"]}",\n'
    registry_str += f'        "name": "{fest["name"]}",\n'
    registry_str += f'        "category": "{fest["category"]}",\n'
    registry_str += f'        "profiles": {json.dumps(fest["profiles"])},\n'
    registry_str += f'        "rule_type": "SingleTithi",\n'
    registry_str += f'        "jain_month": "{fest["jain_month"]}",\n'
    registry_str += f'        "paksha": "{fest["paksha"]}",\n'
    registry_str += f'        "tithi": {fest["tithi"]}\n'
    registry_str += '    },\n'
registry_str += ']\n'

with open('jain_festival_rules.py', 'w', encoding='utf-8') as f:
    f.write(prefix + registry_str)
    
print(f'Successfully wrote {len(festivals)} festivals.')
