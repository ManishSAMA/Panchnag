# -*- coding: utf-8 -*-
"""Hindi rendering of the flat range-export table (plans/hindi-excel-export.md).

Same rows and columns as the English export; headers and text values become
Hindi, while numbers, dates and 24-hour times stay in Latin digits so the sheet
still sorts and filters.

TRANSLATION STATUS: machine-drafted, NOT yet reviewed by a native reviewer.
"""
from __future__ import annotations

import re

from astronomy import RASHI_NAMES
from hindi_calendar_pdf import MONTH_NAMES_HINDI, WEEKDAYS_HINDI, format_tithi, translate_fest
from hindi_observance_map import NAME_HI, TITHI_PREFIX_HI
from panchang import (
    FIXED_KARANAS_END, FIXED_KARANAS_START, HINDU_MONTH_COMMON_NAMES, MOVABLE_KARANAS,
    NAKSHATRA_NAMES, TITHI_NAMES, VARA_NAMES, YOGA_NAMES,
)

RASHI_HI = ("मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
            "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन")

NAKSHATRA_HI = (
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य",
    "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाति",
    "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण",
    "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती",
)

YOGA_HI = (
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड", "सुकर्मा", "धृति",
    "शूल", "गण्ड", "वृद्धि", "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात",
    "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म", "इन्द्र", "वैधृति",
)

_KARANA_NAMES = (*MOVABLE_KARANAS, *FIXED_KARANAS_START, *FIXED_KARANAS_END)
KARANA_HI = ("बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि (भद्रा)",
             "किंस्तुघ्न", "शकुनि", "चतुष्पद", "नाग")

# Common (colloquial) month names in their Hindi forms -- the English column
# carries Gujarati-style forms (Maagsar, Bhadarvo, ...), keyed here by Sanskrit name.
MONTH_COMMON_HI = {
    "Chaitra": "चैत", "Vaishakha": "बैसाख", "Jyeshtha": "जेठ", "Ashadha": "आषाढ़",
    "Shravana": "सावन", "Bhadrapada": "भादों", "Ashwin": "क्वार", "Kartika": "कातिक",
    "Agrahayana": "अगहन", "Pausha": "पूस", "Magha": "माघ", "Phalguna": "फागुन",
}

PLANET_HI = {
    "Sun": "सूर्य", "Moon": "चंद्र", "Mars": "मंगल", "Mercury": "बुध", "Jupiter": "गुरु",
    "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
}

PROFILE_HI = {
    "shwetambar_murtipujak_tapagachchha": "श्वेतांबर मूर्तिपूजक तपागच्छ",
    "shwetambar_sthanakvasi": "श्वेतांबर स्थानकवासी",
    "shwetambar_terapanthi": "श्वेतांबर तेरापंथी",
}

RESIDENCE_HI = {"Heaven": "स्वर्ग", "Earth": "पृथ्वी", "Underworld": "पाताल"}
RISK_HI = {"High": "उच्च", "Low": "निम्न"}
NONE_HI = "कोई नहीं"

HEADER_HI = {
    "Date": "दिनांक",
    "Vikram_Samvat": "विक्रम संवत",
    "Vira_Nirvana_Samvat": "वीर निर्वाण संवत",
    "Julian_Date": "जूलियन दिनांक",
    "Weekday": "वार",
    "Hindu_Month": "हिंदू मास",
    "Hindu_Month_Common": "मास (प्रचलित)",
    "Tithi_No": "तिथि क्रमांक",
    "Tithi": "तिथि",
    "Jain_Tithi_No": "जैन तिथि क्रमांक",
    "Jain_Tithi": "जैन तिथि",
    "Jain_Tithi_End_Time": "जैन तिथि समाप्ति",
    "Nakshatra_No": "नक्षत्र क्रमांक",
    "Nakshatra": "नक्षत्र",
    "Nakshatra_Pada": "नक्षत्र चरण",
    "Yoga_No": "योग क्रमांक",
    "Yoga": "योग",
    "Karana_No": "करण क्रमांक",
    "Karana": "करण",
    "Karana Start": "करण प्रारंभ",
    "Karana End": "करण समाप्ति",
    "Has_Bhadra": "भद्रा",
    "Bhadra_Windows": "भद्रा काल",
    "Bhadra_Max_Risk": "भद्रा अधिकतम जोखिम",
    "Has_Panchak": "पंचक",
    "Panchak_Window": "पंचक काल",
    "Jain_Festivals": "जैन पर्व",
    "Jain_Parva_Tithis": "जैन पर्व तिथि",
    "Festival_Profile": "परंपरा",
    "Festival_Review_Needed": "समीक्षा आवश्यक",
    "Ayanamsa_Dec": "अयनांश (दशमलव)",
    "Ayanamsa_DMS": "अयनांश (अंश-कला-विकला)",
}

_EVENT_HI = {"Sunrise": "सूर्योदय", "Sunset": "सूर्यास्त", "Moonrise": "चंद्रोदय", "Moonset": "चंद्रास्त"}
_PART_HI = {"Rashi": "राशि", "Ansha": "अंश", "Kala": "कला", "Vikala": "विकला"}

_EVENT_HEADER = re.compile(r"^(Sunrise|Sunset|Moonrise|Moonset) \((.+)\)$")
_PLANET_HEADER = re.compile(r"^(\w+)_(Rashi|Ansha|Kala|Vikala)$")
_ENDS_WITH_STAMP = re.compile(r"^(.*?)( \[[^\]]+\])?$")
_BHADRA_DETAIL = re.compile(r"\(Residence: (\w+), Rashi: (.+?), Risk: (\w+)\)")
_PANCHAK_DETAIL = re.compile(r"\(([^)]+)\)")
_FESTIVAL_KEYS = ("Jain_Festivals", "Jain_Parva_Tithis")
_TITHI_PREFIX = re.compile(r"^\[(\w+)\] (.*)$")


def translate_header(header: str) -> str:
    if header in HEADER_HI:
        return HEADER_HI[header]
    event = _EVENT_HEADER.match(header)
    if event:
        return f"{_EVENT_HI[event.group(1)]} ({event.group(2)})"
    planet = _PLANET_HEADER.match(header)
    if planet and planet.group(1) in PLANET_HI:
        return f"{PLANET_HI[planet.group(1)]} {_PART_HI[planet.group(2)]}"
    return header


def _lookup(table_en, table_hi, name: str) -> str:
    return table_hi[table_en.index(name)] if name in table_en else name


def _with_stamp(value: str, translate) -> str:
    """Translate the name in "Name [YYYY-MM-DD HH:MM]", keeping the end stamp."""
    name, stamp = _ENDS_WITH_STAMP.match(value).groups()
    return f"{translate(name)}{stamp or ''}"


def _tithi(name: str) -> str:
    return format_tithi(TITHI_NAMES.index(name) + 1) if name in TITHI_NAMES else name


def _month(name: str, table) -> str:
    adhika = name.startswith("Adhika ")
    hindi = table(name.removeprefix("Adhika "))
    return f"अधिक {hindi}" if adhika else hindi


def _common_month(common: str) -> str:
    sanskrit = next((s for s, c in HINDU_MONTH_COMMON_NAMES.items() if c == common), None)
    return MONTH_COMMON_HI.get(sanskrit, common)


def _rashi_name(name: str) -> str:
    return _lookup(RASHI_NAMES, RASHI_HI, name)


def _bhadra_windows(value: str) -> str:
    if value == "None":
        return NONE_HI
    return _BHADRA_DETAIL.sub(
        lambda m: f"(निवास: {RESIDENCE_HI.get(m.group(1), m.group(1))}, "
                  f"राशि: {_rashi_name(m.group(2))}, जोखिम: {RISK_HI.get(m.group(3), m.group(3))})",
        value,
    )


def _panchak_window(value: str) -> str:
    if value == "None":
        return NONE_HI
    return _PANCHAK_DETAIL.sub(lambda m: f"({_lookup(NAKSHATRA_NAMES, NAKSHATRA_HI, m.group(1))})", value)


def _festival_name(festival: dict) -> str:
    """Registry Hindi name, keeping a "[Tithi]" native-tithi tag (in Hindi) up front."""
    prefixed = _TITHI_PREFIX.match(festival.get("name", ""))
    if not prefixed:
        name = translate_fest(festival)
        return NAME_HI.get(name, name)
    tithi, bare = prefixed.groups()
    name = translate_fest({**festival, "name": bare})
    return f"[{TITHI_PREFIX_HI.get(tithi, tithi)}] {NAME_HI.get(name, name)}"


def _festival_names(festivals: list[dict]) -> str:
    return "; ".join(_festival_name(f) for f in festivals)


def _translate_value(key: str, value: object, row: dict) -> object:
    if isinstance(value, bool):
        return "हाँ" if value else "नहीं"
    if key in _FESTIVAL_KEYS:
        return _festival_names(row.get(f"__{key}") or [])
    if key.endswith("_Rashi") and isinstance(value, int):
        return RASHI_HI[value - 1]
    if not isinstance(value, str):
        return value
    match key:
        case "Weekday":
            return _lookup(VARA_NAMES, WEEKDAYS_HINDI, value)
        case "Hindu_Month":
            return _month(value, lambda m: MONTH_NAMES_HINDI.get(m.upper(), m))
        case "Hindu_Month_Common":
            return _month(value, _common_month)
        case "Tithi" | "Jain_Tithi":
            return _with_stamp(value, _tithi)
        case "Nakshatra":
            return _with_stamp(value, lambda n: _lookup(NAKSHATRA_NAMES, NAKSHATRA_HI, n))
        case "Yoga":
            return _with_stamp(value, lambda n: _lookup(YOGA_NAMES, YOGA_HI, n))
        case "Karana":
            return _lookup(_KARANA_NAMES, KARANA_HI, value)
        case "Bhadra_Windows":
            return _bhadra_windows(value)
        case "Bhadra_Max_Risk":
            return RISK_HI.get(value, value)
        case "Panchak_Window":
            return _panchak_window(value)
        case "Festival_Profile":
            return PROFILE_HI.get(value, NONE_HI if value == "None" else value)
    return value


def translate_rows_to_hindi(rows: list[dict]) -> list[dict]:
    """Hindi copy of export rows. Internal ``__`` helper fields are dropped."""
    return [
        {
            translate_header(key): _translate_value(key, value, row)
            for key, value in row.items()
            if not key.startswith("__") and key != "Jain_Tithi_PDF"
        }
        for row in rows
    ]
