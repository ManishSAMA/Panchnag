"""Which observances take the second day of a tithi vriddhi (वृद्धौ कार्या तथोत्तरा).

User decision, 2026-10-20 (plans/vrat-vriddhi-second-day.md): vrats go on the
second of two days that share a Jain day-start tithi. Kalyanaks keep the
book-verified first day and parva tithis show on both days, so neither is a vrat
category here.
"""

from __future__ import annotations

VRAT_CATEGORIES = frozenset({"vrat", "monthly_vrat", "tap_vrat", "parva_vrat", "mahaparv_vrat"})

# Vrats that keep their own vriddhi rule: Karma Nirjara keeps the first day (user
# directive, 2026-08-30); the Ashtahnika markers follow the Ashtahnika span; the
# Ravi vrats are bound to Sunday; Kartika Shukla Panchami (Gyan + Labh Panchami)
# keeps its documented "Vriddhi -> 1st Panchami", matching the user's 2027
# reference panchang (decision 2026-10-21).
KEEPS_OWN_VRIDDHI_RULE = frozenset({
    "karma_nirjara_vrat", "kartika_nandishwar_ashtami",
    "kartika_purnima_ashtahnika_purna", "phalguna_purnima_ashtahnika_purna",
    "ravi_vrat", "ravivara", "kartika_shukla_panchami",
})


def takes_second_day_of_vriddhi(rule_id: str, category: str) -> bool:
    """Whether an observance follows वृद्धौ कार्या तथोत्तरा (the second day)."""
    return category in VRAT_CATEGORIES and rule_id not in KEEPS_OWN_VRIDDHI_RULE


def previous_tithi(index: int) -> int:
    """The tithi before `index` in the 1-30 cycle (Pratipada follows Amavasya)."""
    return (index - 2) % 30 + 1
