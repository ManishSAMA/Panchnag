import json
import re

months = [
    'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
    'Ashwin', 'Kartika', 'Margashirsha', 'Pausha', 'Magha', 'Phalguna'
]

def get_previous_month(month_name):
    if month_name not in months:
        return month_name
    idx = months.index(month_name)
    prev_idx = (idx - 1) % 12
    return months[prev_idx]

with open('jain_festival_rules.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We'll parse the FESTIVAL_REGISTRY, mutate the dictionaries, and write back.
# Since it's a python file, we'll extract the dict, eval it, modify, and rewrite.

start_idx = text.find('FESTIVAL_REGISTRY = [')
prefix = text[:start_idx]
registry_text = text[start_idx + 20:]

# Safe eval
registry = eval(registry_text)

for fest in registry:
    if fest.get('paksha') == 'Krishna':
        fest['jain_month'] = get_previous_month(fest['jain_month'])

registry_str = 'FESTIVAL_REGISTRY = [\n'
for fest in registry:
    registry_str += '    {\n'
    for k, v in fest.items():
        if isinstance(v, str):
            # Escape quotes in strings
            v_escaped = v.replace('"', '\\"')
            registry_str += f'        "{k}": "{v_escaped}",\n'
        elif isinstance(v, list):
            registry_str += f'        "{k}": {json.dumps(v)},\n'
        else:
            registry_str += f'        "{k}": {v},\n'
    # Remove last comma
    registry_str = registry_str.rstrip(',\n') + '\n'
    registry_str += '    },\n'
# Remove last comma
registry_str = registry_str.rstrip(',\n') + '\n]\n'

with open('jain_festival_rules.py', 'w', encoding='utf-8') as f:
    f.write(prefix + registry_str)

print("Shifted Krishna Paksha months to Amanta system!")
