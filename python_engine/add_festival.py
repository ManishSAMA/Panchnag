import json

with open('jain_festival_rules.py', 'r', encoding='utf-8') as f:
    text = f.read()

fest = {
    "id": "shri_shantinath_ji_janma_tap_moksha",
    "name": "Shri Shantinath Ji - Janma, Tap, Moksha",
    "category": "kalyanak",
    "profiles": ["all"],
    "rule_type": "SingleTithi",
    "jain_month": "Jyeshtha",
    "paksha": "Krishna",
    "tithi": 14
}

new_entry = '    {\n'
new_entry += f'        "id": "{fest["id"]}",\n'
new_entry += f'        "name": "{fest["name"]}",\n'
new_entry += f'        "category": "{fest["category"]}",\n'
new_entry += f'        "profiles": {json.dumps(fest["profiles"])},\n'
new_entry += f'        "rule_type": "{fest["rule_type"]}",\n'
new_entry += f'        "jain_month": "{fest["jain_month"]}",\n'
new_entry += f'        "paksha": "{fest["paksha"]}",\n'
new_entry += f'        "tithi": {fest["tithi"]}\n'
new_entry += '    }'

# Find the end of the FESTIVAL_REGISTRY list and insert the new entry before the last closing bracket
last_bracket = text.rfind(']')
if text[last_bracket-1] == '\n':
    # Ensure there is a comma after the previous last entry
    # Actually, we can just insert it at the end of the list
    pass

# A simpler way: replace ']' with '    ,\n' + new_entry + '\n]'
text = text[:last_bracket] + ',\n' + new_entry + '\n]'

with open('jain_festival_rules.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added Shantinath Ji festival")
