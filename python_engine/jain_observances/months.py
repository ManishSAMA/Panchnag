"""Single source of truth for lunar-month names and the amanta -> purnimanta shift.

Imported by both `festival_service` (snapshot building, display) and `festival_rules`
(rule matching) so the two never disagree about month 8's name or the Ashwin spelling.
"""

PURNIMANTA_MONTHS = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwin", "Kartika", "Agrahayana", "Pausha", "Magha", "Phalguna",
]

_UPPER = [m.upper() for m in PURNIMANTA_MONTHS]

_ALIASES = {
    "ASHVINA": "ASHWIN", "ASO": "ASHWIN", "ASOJ": "ASHWIN",
    "MARGASHIRSHA": "AGRAHAYANA", "MARGASHIRSA": "AGRAHAYANA", "MAGSAR": "AGRAHAYANA",
    "MANSIR": "AGRAHAYANA", "MARGASHIRA": "AGRAHAYANA",
    "JYESTHA": "JYESHTHA", "JETH": "JYESHTHA",
    "VAISAKH": "VAISHAKHA", "BAISAKH": "VAISHAKHA",
    "KARTIK": "KARTIKA",
}


def canonical(name: str) -> str:
    """Upper-case canonical key for a month name, collapsing known spelling variants."""
    if not name:
        return ""
    u = name.upper()
    return _ALIASES.get(u, u)


def next_month(base_month: str) -> str:
    """Title-case month one position after `base_month` -- i.e. the purnimanta month
    name of that amanta month's Krishna paksha. Unknown names pass through unchanged."""
    u = canonical(base_month)
    if u in _UPPER:
        return PURNIMANTA_MONTHS[(_UPPER.index(u) + 1) % 12]
    return base_month
