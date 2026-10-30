"""Every Tirthankar kalyanak carries a Hindi name.

The mobile app and the Hindi exports read `name_hindi`; without it a kalyanak
falls back to word-by-word substitution of the English name. The terms follow
the Digambar sources the kalyanak dates come from (गर्भ, not च्यवन), and the
Tirthankar spellings follow hindi_calendar_pdf.TRANSLATIONS_MAP.
"""

from __future__ import annotations

import re

from jain_observances.registry import FESTIVAL_REGISTRY

KALYANAK_WORD_HINDI = {
    "Conception": "गर्भ",
    "Birth": "जन्म",
    "Austerity": "दीक्षा",
    "Omniscience": "केवलज्ञान",
    "Liberation": "मोक्ष",
}

TIRTHANKAR_KALYANAK = re.compile(r"^Shri (?P<tirthankar>.+) Ji - (?P<kind>\w+) Kalyanak$")
HINDI_SHAPE = re.compile(r"^श्री (?P<tirthankar>[ऀ-ॿ() ]+) जी — (?P<kind>\S+) कल्याणक$")


def kalyanaks() -> list[dict]:
    return [f for f in FESTIVAL_REGISTRY if f["category"] == "kalyanak"]


def tirthankar_kalyanaks() -> list[dict]:
    return [f for f in kalyanaks() if TIRTHANKAR_KALYANAK.match(f["name"])]


def test_every_kalyanak_has_a_devanagari_hindi_name():
    missing = [f["id"] for f in kalyanaks()
               if not any("ऀ" <= ch <= "ॿ" for ch in f.get("name_hindi", ""))]

    assert missing == []


def test_tirthankar_kalyanak_hindi_names_have_the_shri_ji_shape():
    misshapen = [(f["id"], f.get("name_hindi")) for f in tirthankar_kalyanaks()
                 if not HINDI_SHAPE.match(f.get("name_hindi", ""))]

    assert misshapen == []


def test_hindi_kalyanak_word_matches_the_english_kind():
    mismatched = [
        (f["id"], f["name_hindi"])
        for f in tirthankar_kalyanaks()
        if HINDI_SHAPE.match(f.get("name_hindi", "")) is None
        or HINDI_SHAPE.match(f["name_hindi"])["kind"]
        != KALYANAK_WORD_HINDI[TIRTHANKAR_KALYANAK.match(f["name"])["kind"]]
    ]

    assert mismatched == []


def test_one_tirthankar_reads_the_same_in_every_kalyanak():
    hindi_by_tirthankar: dict[str, set[str]] = {}
    for f in tirthankar_kalyanaks():
        english = TIRTHANKAR_KALYANAK.match(f["name"])["tirthankar"].replace("Pushpadanta", "Pushpadant")
        shaped = HINDI_SHAPE.match(f.get("name_hindi", ""))
        hindi_by_tirthankar.setdefault(english, set()).add(shaped["tirthankar"] if shaped else "")

    assert {name: spellings for name, spellings in hindi_by_tirthankar.items() if len(spellings) != 1} == {}


def test_neminath_omniscience_reads_as_the_calendar_spells_it():
    neminath = next(f for f in kalyanaks() if f["name"] == "Shri Neminath Ji - Omniscience Kalyanak")

    assert neminath["name_hindi"] == "श्री नेमिनाथ जी — केवलज्ञान कल्याणक"


def test_kalyanaks_outside_the_tirthankar_pattern_keep_their_own_hindi_names():
    others = {f["id"]: f["name_hindi"] for f in kalyanaks() if not TIRTHANKAR_KALYANAK.match(f["name"])}

    assert others == {
        "mahavir_janma_kalyanak": "महावीर जन्म कल्याणक",
        "parshvanath_jayanti": "श्री पार्श्वनाथ जयंती",
        "chaitra_amavasya_kalyanak_varshant": "तीर्थंकर मोक्ष कल्याणक, लब्धि विधान प्रारम्भ एवं विक्रम संवत वर्षांत",
    }
