"""yoga_rules.py — Pure rule data for all yoga systems.

Three rule sets:
  AANANDADI_YOGAS  — 28 Vara+Moon yogas (ordered 1–28 for formula lookup)
  DAINIKA_RULES    — 42 vara-tithi/nakshatra based yogas
  SPECIAL_RULES    — 4 Moon-position based yogas (no vara dependency)

No logic, no imports beyond typing.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Aanandadi Yogas — 28 yogas determined exclusively by Vara (weekday) and
# the Moon's nakshatra using the formula:
#
#   Y = (N_idx − (V_idx − 1) × 4) mod 28   [add 28 if result ≤ 0]
#
# where:
#   N_idx  = Moon's nakshatra in the 28-nakshatra system (Abhijit at position 22)
#             Naks 1–21 keep their index; naks 22–27 shift to 23–28; Abhijit=28→22
#   V_idx  = weekday index: Sunday=1, Monday=2, ..., Saturday=7
#
# List index 0 = yoga Y=1 (Anand) … index 27 = yoga Y=28 (Vriddhi).
# varjya: None | "full_day" | (ghati, pala)
#   1 ghati = 24 min, 1 pala = 24 sec (0.4 min)
# ---------------------------------------------------------------------------

AANANDADI_YOGAS: list[dict] = [
    # Y=1
    {
        "name": "Anand",
        "nature": "shubh",
        "severe": False,
        "severity": "highly_auspicious",
        "fal": "Sarva Siddhi",
        "varjya": None,
        "meaning": "Joy and bliss — all undertakings succeed; highly auspicious for any new start.",
    },
    # Y=2
    {
        "name": "Kaal",
        "nature": "ashubh",
        "severe": True,
        "severity": "highly_inauspicious",
        "fal": "Haani",
        "varjya": "full_day",
        "meaning": "Time of doom — entire period is forbidden; avoid all auspicious and new undertakings.",
    },
    # Y=3
    {
        "name": "Dhumra",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Dukh",
        "varjya": (1, 0),
        "meaning": "Smoke and confusion — creates obstacles, delays, and unclear outcomes.",
    },
    # Y=4
    {
        "name": "Prajapati",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Laabh",
        "varjya": None,
        "meaning": "Lord of Beings — creative energy; auspicious for new beginnings and growth.",
    },
    # Y=5
    {
        "name": "Soumya",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Sukh",
        "varjya": None,
        "meaning": "Gentle and benevolent — peaceful energy; favourable for social and family activities.",
    },
    # Y=6
    {
        "name": "Dhwanksha",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Kshati",
        "varjya": (2, 0),
        "meaning": "Crow omen — inauspicious; avoid travel, new agreements, and auspicious ceremonies.",
    },
    # Y=7
    {
        "name": "Dhwaja",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Vijay",
        "varjya": None,
        "meaning": "Victory flag — success in endeavours; especially favourable for competitive activities.",
    },
    # Y=8
    {
        "name": "Shreevatsa",
        "nature": "shubh",
        "severe": False,
        "severity": "highly_auspicious",
        "fal": "Dhana Laabh",
        "varjya": None,
        "meaning": "Mark of Vishnu — wealth and prosperity; highly auspicious for financial transactions.",
    },
    # Y=9
    {
        "name": "Vajra",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Peeda",
        "varjya": (2, 0),
        "meaning": "Thunderbolt — sudden disruptions and sharp reversals; avoid risky ventures.",
    },
    # Y=10
    {
        "name": "Mudgar",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Kasht",
        "varjya": (2, 0),
        "meaning": "Hammer — forceful obstacles; projects require extra effort and face resistance.",
    },
    # Y=11
    {
        "name": "Chhatra",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Samman",
        "varjya": None,
        "meaning": "Royal umbrella — protection and prestige; auspicious for authority and leadership.",
    },
    # Y=12
    {
        "name": "Mitra",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Maitri",
        "varjya": None,
        "meaning": "Friendship — supportive social energy; excellent for alliances and partnerships.",
    },
    # Y=13
    {
        "name": "Manas",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Siddhi",
        "varjya": None,
        "meaning": "Mind — clarity and focus; favourable for intellectual and mental work.",
    },
    # Y=14
    {
        "name": "Padma",
        "nature": "shubh",
        "severe": False,
        "severity": "highly_auspicious",
        "fal": "Shree Laabh",
        "varjya": None,
        "meaning": "Lotus — beauty, wealth, and Lakshmi's grace; highly auspicious for prosperity.",
    },
    # Y=15
    {
        "name": "Lumbak",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Kshay",
        "varjya": (1, 36),
        "meaning": "Decay and suspension — delays and deterioration; avoid finalising contracts.",
    },
    # Y=16
    {
        "name": "Utpat",
        "nature": "ashubh",
        "severe": True,
        "severity": "highly_inauspicious",
        "fal": "Sarva Nashta",
        "varjya": "full_day",
        "meaning": "Calamity — entire period is forbidden; avoid all auspicious or important acts.",
    },
    # Y=17
    {
        "name": "Mrityu",
        "nature": "ashubh",
        "severe": True,
        "severity": "highly_inauspicious",
        "fal": "Maran",
        "varjya": "full_day",
        "meaning": "Death — entire period is forbidden; avoid all new undertakings without exception.",
    },
    # Y=18
    {
        "name": "Kaan",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Kaan Peeda",
        "varjya": (0, 48),
        "meaning": "Loss — deficits and troubles; avoid financial decisions and new commitments.",
    },
    # Y=19
    {
        "name": "Siddhi",
        "nature": "shubh",
        "severe": False,
        "severity": "highly_auspicious",
        "fal": "Siddhi",
        "varjya": None,
        "meaning": "Achievement — success guaranteed; highly favourable for completing important work.",
    },
    # Y=20
    {
        "name": "Shubha",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Shubh",
        "varjya": None,
        "meaning": "Auspicious — generally favourable energy; good for most activities.",
    },
    # Y=21
    {
        "name": "Amrut",
        "nature": "shubh",
        "severe": False,
        "severity": "highly_auspicious",
        "fal": "Amrut Phal",
        "varjya": None,
        "meaning": "Nectar — the finest Aanandadi yoga; actions taken here yield exceptional lasting results.",
    },
    # Y=22
    {
        "name": "Musal",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Kshati",
        "varjya": (0, 48),
        "meaning": "Pestle — grinding difficulties; hard work yields poor results; avoid major decisions.",
    },
    # Y=23
    {
        "name": "Gada",
        "nature": "ashubh",
        "severe": False,
        "severity": "inauspicious",
        "fal": "Rog",
        "varjya": (2, 48),
        "meaning": "Mace — health challenges and confrontations; avoid surgery and physical risks.",
    },
    # Y=24
    {
        "name": "Matanga",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Vriddhi",
        "varjya": None,
        "meaning": "Elephant — powerful and steady energy; auspicious for important decisions.",
    },
    # Y=25
    {
        "name": "Rakshasa",
        "nature": "ashubh",
        "severe": True,
        "severity": "highly_inauspicious",
        "fal": "Sarva Kasht",
        "varjya": "full_day",
        "meaning": "Demon — entire period is forbidden; avoid all auspicious acts without exception.",
    },
    # Y=26
    {
        "name": "Chara",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Safar Laabh",
        "varjya": None,
        "meaning": "Dynamic movement — favourable for travel, change, and transition activities.",
    },
    # Y=27
    {
        "name": "Sthira",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Sthirta",
        "varjya": None,
        "meaning": "Stability — excellent for laying foundations, construction, and long-term commitments.",
    },
    # Y=28
    {
        "name": "Vriddhi",
        "nature": "shubh",
        "severe": False,
        "severity": "auspicious",
        "fal": "Vriddhi",
        "varjya": None,
        "meaning": "Growth and increase — favourable for business expansion and accumulation.",
    },
]


# ---------------------------------------------------------------------------
# Dainika Rules — 42 yogas triggered by Vara (weekday) + Tithi/Nakshatra
#
# Vara: 0=Sunday … 6=Saturday
# Tithi: 1–30 (lunar day)
# Nakshatra: 1–27 (28=Abhijit)
#
# trigger: "tithi" | "nakshatra" | "tithi_and_nakshatra"
# vara_map: {vara_int: [tithi_or_nak_values]}
# ---------------------------------------------------------------------------

DAINIKA_RULES: list[dict] = [
    # ── SECTION 1: TITHI-BASED ────────────────────────────────────────────
    {
        "name": "Siddhi Yoga Tithi",
        "nature": "shubh",
        "trigger": "tithi",
        "severity": "auspicious",
        "meaning": "Accomplishment — work started here reaches completion successfully.",
        "vara_map": {
            2: [3, 8, 13],   # Tuesday
            3: [2, 7, 12],   # Wednesday
            4: [5, 10, 15],  # Thursday
            5: [1, 6, 11],   # Friday
            6: [4, 9, 14],   # Saturday
        },
    },
    {
        "name": "Dagdha Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Burnt — work started here gets destroyed. Avoid new beginnings.",
        "vara_map": {
            0: [12],   # Sunday
            1: [11],   # Monday
            2: [5],    # Tuesday
            3: [3],    # Wednesday
            4: [6],    # Thursday
            5: [8],    # Friday
            6: [9],    # Saturday
        },
    },
    {
        "name": "Hutashan Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Consumed by fire — efforts get destroyed. Harmful for auspicious starts.",
        "vara_map": {
            0: [12],   # Sunday
            1: [6],    # Monday
            2: [7],    # Tuesday
            3: [8],    # Wednesday
            4: [9],    # Thursday
            5: [10],   # Friday
            6: [11],   # Saturday
        },
    },
    {
        "name": "Vishakhya Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Poison — undertakings here tend to have harmful or toxic results.",
        "vara_map": {
            0: [4],    # Sunday
            1: [6],    # Monday
            2: [7],    # Tuesday
            3: [2],    # Wednesday
            4: [8],    # Thursday
            5: [9],    # Friday
            6: [7],    # Saturday
        },
    },
    {
        "name": "Adham Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Lowest/inferior — work here gives degraded or base results.",
        "vara_map": {
            0: [7, 12],   # Sunday
            1: [11],      # Monday
            2: [10],      # Tuesday
            3: [1, 9],    # Wednesday
            4: [8],       # Thursday
            5: [7],       # Friday
            6: [6],       # Saturday
        },
    },
    {
        "name": "Mrityu Yoga Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Death — one of the most inauspicious yogas. Strongly avoid all auspicious muhurtas.",
        "vara_map": {
            0: [1, 6, 11],   # Sunday
            1: [2, 7, 12],   # Monday
            2: [1, 6, 11],   # Tuesday
            3: [3, 8, 13],   # Wednesday
            4: [4, 9, 14],   # Thursday
            5: [2, 7, 12],   # Friday
            6: [5, 10, 15],  # Saturday
        },
    },
    {
        "name": "Krakach Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Saw — cuts through benefits. Efforts will be cut short or disrupted.",
        "vara_map": {
            0: [12],   # Sunday
            1: [11],   # Monday
            2: [10],   # Tuesday
            3: [9],    # Wednesday
            4: [8],    # Thursday
            5: [7],    # Friday
            6: [6],    # Saturday
        },
    },
    {
        "name": "Dusht Tithi",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Wicked/corrupt — gives corrupted results. Cancelled by Sarvartha Siddhi.",
        "vara_map": {
            0: [1, 3, 7],           # Sunday
            1: list(range(2, 12)),  # Monday: 2–11
            2: [3, 9, 12],          # Tuesday
            3: [7, 9, 11],          # Wednesday
            6: list(range(11, 14)), # Saturday: 11–13
        },
    },
    # ── SECTION 2: ASHUBH TITHIVAR (7 named Vara+Tithi combos) ──────────
    {
        "name": "Nal Banvas",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Exile of Nala — inauspicious combination associated with exile and hardship.",
        "vara_map": {2: [2]},   # Tuesday + Tithi 2
    },
    {
        "name": "Pandav Nash",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Destruction of Pandavas — inauspicious; avoid new undertakings.",
        "vara_map": {5: [3]},   # Friday + Tithi 3
    },
    {
        "name": "Vibhishan Maran",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Death of Vibhishana — inauspicious combination; avoid important events.",
        "vara_map": {0: [4]},   # Sunday + Tithi 4
    },
    {
        "name": "Sita Haran",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Abduction of Sita — inauspicious; avoid travel, marriage, and new ventures.",
        "vara_map": {3: [5]},   # Wednesday + Tithi 5
    },
    {
        "name": "Lanka Bhang",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Destruction of Lanka — inauspicious combination; avoid construction and agreements.",
        "vara_map": {6: [6]},   # Saturday + Tithi 6
    },
    {
        "name": "Pandav Jung",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "War of Pandavas — inauspicious; avoid legal matters and disputes.",
        "vara_map": {1: [7]},   # Monday + Tithi 7
    },
    {
        "name": "Bali Raja Chhal",
        "nature": "ashubh",
        "trigger": "tithi",
        "severity": "inauspicious",
        "meaning": "Deception of King Bali — inauspicious; avoid financial dealings and trusts.",
        "vara_map": {4: [8]},   # Thursday + Tithi 8
    },
    # ── SECTION 3: NAKSHATRA-BASED ASHUBH ────────────────────────────────
    {
        "name": "Varjit Tithi Nakshatra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Forbidden nakshatra+vara — strictly avoid for auspicious muhurtas.",
        "vara_map": {
            0: [13],   # Sunday: Hasta
            1: [5],    # Monday: Mrigashira
            2: [1],    # Tuesday: Ashvini
            3: [22],   # Wednesday: Shravana
            4: [8],    # Thursday: Pushya
            5: [27],   # Friday: Revati
            6: [4],    # Saturday: Rohini
        },
    },
    {
        "name": "Utpat Nakshatra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Calamity — creates turbulence and unexpected trouble.",
        "vara_map": {
            0: [16],   # Sunday: Vishakha
            1: [20],   # Monday: Purva Ashadha
            2: [23],   # Tuesday: Dhanishtha
            3: [27],   # Wednesday: Revati
            4: [4],    # Thursday: Rohini
            5: [8],    # Friday: Pushya
            6: [12],   # Saturday: Uttara Phalguni
        },
    },
    {
        "name": "Mrityu Yoga Nakshatra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Death yoga via Nakshatra — extremely inauspicious. No muhurta should be given.",
        "vara_map": {
            0: [17],   # Sunday: Anuradha
            1: [21],   # Monday: Uttara Ashadha
            2: [24],   # Tuesday: Shatabhisha
            3: [1],    # Wednesday: Ashvini
            4: [5],    # Thursday: Mrigashira
            5: [9],    # Friday: Ashlesha
            6: [13],   # Saturday: Hasta
        },
    },
    {
        "name": "Kaan Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "One-eyed — incomplete results. Especially bad for legal, contractual, medical muhurtas.",
        "vara_map": {
            0: [18],   # Sunday: Jyeshtha
            1: [28],   # Monday: Abhijit
            2: [25],   # Tuesday: Purva Bhadrapada
            3: [2],    # Wednesday: Bharani
            4: [6],    # Thursday: Ardra
            5: [10],   # Friday: Magha
            6: [14],   # Saturday: Chitra
        },
    },
    {
        "name": "Dagdha Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Burnt — all good effects are burnt away. Work does not bear fruit.",
        "vara_map": {
            0: [2],    # Sunday: Bharani
            1: [14],   # Monday: Chitra
            2: [21],   # Tuesday: Uttara Ashadha
            3: [23],   # Wednesday: Dhanishtha
            4: [12],   # Thursday: Uttara Phalguni
            5: [18],   # Friday: Jyeshtha
            6: [27],   # Saturday: Revati
        },
    },
    {
        "name": "Yam Ghant",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Bell of Yama — highly inauspicious. Signals proximity to harmful outcomes.",
        "vara_map": {
            0: [10],   # Sunday: Magha
            1: [16],   # Monday: Vishakha
            2: [6],    # Tuesday: Ardra
            3: [19],   # Wednesday: Mula
            4: [3],    # Thursday: Kritika
            5: [4],    # Friday: Rohini
            6: [13],   # Saturday: Hasta
        },
    },
    {
        "name": "Musal Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Pestle — crushes efforts. Especially bad for business starts and partnerships.",
        "vara_map": {
            0: [28],   # Sunday: Abhijit
            1: [25],   # Monday: Purva Bhadrapada
            2: [2],    # Tuesday: Bharani
            3: [6],    # Wednesday: Ardra
            4: [10],   # Thursday: Magha
            5: [14],   # Friday: Chitra
            6: [18],   # Saturday: Jyeshtha
        },
    },
    {
        "name": "Kaal Dand",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Staff of time — punishes actions started in it. Bad for government and legal matters.",
        "vara_map": {
            0: [2],    # Sunday: Bharani
            1: [6],    # Monday: Ardra
            2: [10],   # Tuesday: Magha
            3: [14],   # Wednesday: Chitra
            4: [18],   # Thursday: Jyeshtha
            5: [28],   # Friday: Abhijit
            6: [25],   # Saturday: Purva Bhadrapada
        },
    },
    {
        "name": "Vajra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Thunderbolt — strikes suddenly. Harmful for marriage, travel, new partnerships.",
        "vara_map": {
            0: [9],    # Sunday: Ashlesha
            1: [13],   # Monday: Hasta
            2: [17],   # Tuesday: Anuradha
            3: [21],   # Wednesday: Uttara Ashadha
            4: [24],   # Thursday: Shatabhisha
            5: [1],    # Friday: Ashvini
            6: [5],    # Saturday: Mrigashira
        },
    },
    {
        "name": "Rakshas Yoga",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "highly_inauspicious",
        "severe": True,
        "meaning": "Demon — one of the most feared yogas. All auspicious muhurtas forbidden.",
        "vara_map": {
            0: [24],   # Sunday: Shatabhisha
            1: [1],    # Monday: Ashvini
            2: [5],    # Tuesday: Mrigashira
            3: [9],    # Wednesday: Ashlesha
            4: [13],   # Thursday: Hasta
            5: [17],   # Friday: Anuradha
            6: [21],   # Saturday: Uttara Ashadha
        },
    },
    {
        "name": "Dhwanksh",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Crow — brings bad news, separation, dark outcomes. Avoid family and social events.",
        "vara_map": {
            0: [6],    # Sunday: Ardra
            1: [10],   # Monday: Magha
            2: [14],   # Tuesday: Chitra
            3: [18],   # Wednesday: Jyeshtha
            4: [28],   # Thursday: Abhijit
            5: [25],   # Friday: Purva Bhadrapada
            6: [2],    # Saturday: Bharani
        },
    },
    {
        "name": "Dhumra",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Smoke — clouds clarity. Results unclear or obscured. Avoid contracts and negotiations.",
        "vara_map": {
            0: [3],    # Sunday: Kritika
            1: [7],    # Monday: Punarvasu
            2: [11],   # Tuesday: Purva Phalguni
            3: [15],   # Wednesday: Swati
            4: [19],   # Thursday: Mula
            5: [22],   # Friday: Shravana
            6: [26],   # Saturday: Uttara Bhadrapada
        },
    },
    {
        "name": "Gad",
        "nature": "ashubh",
        "trigger": "nakshatra",
        "severity": "inauspicious",
        "meaning": "Disease — brings illness or heavy obstacles. Avoided for health and medical muhurtas.",
        "vara_map": {
            0: [22],   # Sunday: Shravana
            1: [26],   # Monday: Uttara Bhadrapada
            2: [3],    # Tuesday: Kritika
            3: [7],    # Wednesday: Punarvasu
            4: [11],   # Thursday: Purva Phalguni
            5: [15],   # Friday: Swati
            6: [19],   # Saturday: Mula
        },
    },
    # ── SECTION 4: NAKSHATRA-BASED SHUBH ─────────────────────────────────
    {
        "name": "Anand",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Joy/bliss — brings happiness. Good for celebrations and social gatherings.",
        "vara_map": {
            0: [1],    # Sunday: Ashvini
            1: [5],    # Monday: Mrigashira
            2: [9],    # Tuesday: Ashlesha
            3: [13],   # Wednesday: Hasta
            4: [17],   # Thursday: Anuradha
            5: [21],   # Friday: Uttara Ashadha
            6: [24],   # Saturday: Shatabhisha
        },
    },
    {
        "name": "Shrivatsa",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Divine mark of Vishnu — brings prosperity and divine grace. Good for financial muhurtas.",
        "vara_map": {
            0: [8],    # Sunday: Pushya
            1: [12],   # Monday: Uttara Phalguni
            2: [16],   # Tuesday: Vishakha
            3: [20],   # Wednesday: Purva Ashadha
            4: [23],   # Thursday: Dhanishtha
            5: [27],   # Friday: Revati
            6: [4],    # Saturday: Rohini
        },
    },
    {
        "name": "Saumya",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Gentle/benevolent — calmness and pleasant outcomes. Good for relationships and healing.",
        "vara_map": {
            0: [5],    # Sunday: Mrigashira
            1: [9],    # Monday: Ashlesha
            2: [13],   # Tuesday: Hasta
            3: [17],   # Wednesday: Anuradha
            4: [21],   # Thursday: Uttara Ashadha
            5: [24],   # Friday: Shatabhisha
            6: [1],    # Saturday: Ashvini
        },
    },
    {
        "name": "Chatra",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Royal canopy — protection and prestige. Good for authority and leadership muhurtas.",
        "vara_map": {
            0: [11],   # Sunday: Purva Phalguni
            1: [15],   # Monday: Swati
            2: [19],   # Tuesday: Mula
            3: [22],   # Wednesday: Shravana
            4: [26],   # Thursday: Uttara Bhadrapada
            5: [3],    # Friday: Kritika
            6: [7],    # Saturday: Punarvasu
        },
    },
    {
        "name": "Shubh",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Auspicious/good — blesses any work started in it with good results.",
        "vara_map": {
            0: [20],   # Sunday: Purva Ashadha
            1: [23],   # Monday: Dhanishtha
            2: [27],   # Tuesday: Revati
            3: [4],    # Wednesday: Rohini
            4: [8],    # Thursday: Pushya
            5: [12],   # Friday: Uttara Phalguni
            6: [16],   # Saturday: Vishakha
        },
    },
    {
        "name": "Amrit",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Nectar — excellent, long-lasting, fruitful results. Highly recommended for muhurtas.",
        "vara_map": {
            0: [21],   # Sunday: Uttara Ashadha
            1: [24],   # Monday: Shatabhisha
            2: [1],    # Tuesday: Ashvini
            3: [5],    # Wednesday: Mrigashira
            4: [9],    # Thursday: Ashlesha
            5: [13],   # Friday: Hasta
            6: [17],   # Saturday: Anuradha
        },
    },
    {
        "name": "Mitra",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Friend — friendly, cooperative energy. Excellent for partnerships and marriages.",
        "vara_map": {
            0: [12],   # Sunday: Uttara Phalguni
            1: [16],   # Monday: Vishakha
            2: [20],   # Tuesday: Purva Ashadha
            3: [23],   # Wednesday: Dhanishtha
            4: [27],   # Thursday: Revati
            5: [4],    # Friday: Rohini
            6: [8],    # Saturday: Pushya
        },
    },
    {
        "name": "Siddha Yoga",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "auspicious",
        "meaning": "Accomplished — work reaches its intended goal. Great for precision tasks.",
        "vara_map": {
            0: [19],   # Sunday: Mula
            1: [22],   # Monday: Shravana
            2: [26],   # Tuesday: Uttara Bhadrapada
            3: [3],    # Wednesday: Kritika
            4: [7],    # Thursday: Punarvasu
            5: [11],   # Friday: Purva Phalguni
            6: [15],   # Saturday: Swati
        },
    },
    {
        "name": "Amrit Siddhi",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Nectar of accomplishment — highest auspicious yoga. Work is blessed with completion and longevity.",
        "vara_map": {
            0: [13],   # Sunday: Hasta
            1: [22],   # Monday: Shravana
            2: [1],    # Tuesday: Ashvini
            3: [17],   # Wednesday: Anuradha
            4: [8],    # Thursday: Pushya
            5: [27],   # Friday: Revati
            6: [4],    # Saturday: Rohini
        },
    },
    # ── SECTION 5: SPECIAL SHUBH VARA-NAKSHATRA ──────────────────────────
    {
        "name": "Sarvartha Siddhi",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Accomplishment of all purposes — extremely powerful. Fulfils any objective.",
        "vara_map": {
            0: [13, 19, 7, 1],        # Sunday: Hasta, Mula, Punarvasu, Ashvini
            1: [22, 4, 5, 8, 17],     # Monday: Shravana, Rohini, Mrigashira, Pushya, Anuradha
            2: [1, 26, 3, 9],          # Tuesday: Ashvini, Uttara Bhadrapada, Krittika, Ashlesha
            3: [4, 3, 5],              # Wednesday: Rohini, Krittika, Mrigashira
            4: [27, 17, 1, 7, 8],      # Thursday: Revati, Anuradha, Ashvini, Punarvasu, Pushya
            5: [27, 17, 1, 7, 22],    # Friday: Revati, Anuradha, Ashvini, Punarvasu, Shravana
            6: [4, 22, 15],            # Saturday: Rohini, Shravana, Swati
        },
    },
    {
        "name": "Ravi Pushya Amrit",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Sun-Pushya nectar — extremely auspicious conjunction of Sunday and Pushya nakshatra.",
        "vara_map": {0: [8]},   # Sunday + Pushya
    },
    {
        "name": "Guru Pushya Amrit",
        "nature": "shubh",
        "trigger": "nakshatra",
        "severity": "highly_auspicious",
        "meaning": "Guru-Pushya nectar — most auspicious conjunction of Thursday and Pushya nakshatra.",
        "vara_map": {4: [8]},   # Thursday + Pushya
    },
    # ── SECTION 6: TRIPUSHKAR & DWIPUSHKAR ───────────────────────────────
    {
        "name": "Tripushkar",
        "nature": "ashubh",
        "trigger": "tithi_and_nakshatra",
        "severity": "inauspicious",
        "meaning": "Triple multiplication — events triple in effect. Losses triple; avoid inauspicious acts.",
        "vara_map": {0: True, 2: True, 6: True},   # Sunday, Tuesday, Saturday
        "tithi_values": [2, 7, 12, 17, 22, 27],    # Dvitiya/Saptami/Dwadashi both Shukla & Krishna
        "nakshatra_values": [3, 7, 12, 16, 21, 25],
    },
    {
        "name": "Dwipushkar",
        "nature": "ashubh",
        "trigger": "tithi_and_nakshatra",
        "severity": "inauspicious",
        "meaning": "Double multiplication — events double in effect. Losses double; avoid inauspicious acts.",
        "vara_map": {0: True, 3: True, 5: True},   # Sunday, Wednesday, Friday
        "tithi_values": [2, 7, 12, 17, 22, 27],
        "nakshatra_values": [5, 14, 23],   # Mrigashira, Chitra, Dhanishtha — 2-to-2 rashi split
    },
]


# ---------------------------------------------------------------------------
# Special Rules — 4 Moon-position based yogas (no Vara dependency)
# ---------------------------------------------------------------------------

SPECIAL_RULES: list[dict] = [
    {
        "name": "Gandmool Nakshatra",
        "nature": "ashubh",
        "trigger": "gandmool",
        "severity": "inauspicious",
        "meaning": "Junction nakshatra — inauspicious for births and new beginnings. Purification rites advised.",
    },
    {
        "name": "Panchak",
        "nature": "ashubh",
        "trigger": "panchak",
        "severity": "inauspicious",
        "meaning": "Last 5 nakshatras — avoid funeral rites, travel south, collecting wood, construction, and marriage.",
    },
    {
        "name": "Bhadra (Vishti)",
        "nature": "ashubh",
        "trigger": "bhadra",
        "severity": "inauspicious",
        "meaning": "Vishti Karana — inauspicious half-tithi period. Avoid all new undertakings, travel, and auspicious ceremonies.",
    },
    {
        "name": "Jwalamukhi",
        "nature": "ashubh",
        "trigger": "jwalamukhi",
        "severity": "inauspicious",
        "meaning": "Flame-mouth — combustive energy; avoid fire-related activities, surgery, and auspicious starts.",
    },
]
