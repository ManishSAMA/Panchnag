"""Data integrity tests for yoga_rules.py.

No ephemeris calls — pure structural validation of rule data.
Run these before creating yoga_rules.py; they should fail (RED) until GREEN.
"""

import pytest
from yoga_rules import AANANDADI_YOGAS, DAINIKA_RULES, SPECIAL_RULES

_NATURES = frozenset({"shubh", "ashubh"})
_SEVERITIES = frozenset({"highly_auspicious", "auspicious", "inauspicious", "highly_inauspicious"})
_DAINIKA_TRIGGERS = frozenset({"tithi", "nakshatra", "tithi_and_nakshatra"})
_SPECIAL_TRIGGERS = frozenset({"gandmool", "panchak", "bhadra", "jwalamukhi"})


# ---------------------------------------------------------------------------
# Aanandadi Yogas (ordered list, formula-based — no planet_map)
# ---------------------------------------------------------------------------

class TestAanandadiRules:
    def test_exactly_28_yogas(self):
        assert len(AANANDADI_YOGAS) == 28

    def test_all_names_unique(self):
        names = [y["name"] for y in AANANDADI_YOGAS]
        assert len(names) == len(set(names))

    def test_required_keys_present(self):
        # No planet_map — yogas are determined by formula, not planet positions
        required = {"name", "nature", "severe", "severity", "fal", "varjya", "meaning"}
        for yoga in AANANDADI_YOGAS:
            missing = required - yoga.keys()
            assert not missing, f"Yoga '{yoga.get('name')}' missing keys: {missing}"

    def test_no_planet_map_field(self):
        for yoga in AANANDADI_YOGAS:
            assert "planet_map" not in yoga, f"Yoga '{yoga['name']}' must not have planet_map"

    def test_nature_values_valid(self):
        for yoga in AANANDADI_YOGAS:
            assert yoga["nature"] in _NATURES, f"Yoga '{yoga['name']}': invalid nature '{yoga['nature']}'"

    def test_severity_values_valid(self):
        for yoga in AANANDADI_YOGAS:
            assert yoga["severity"] in _SEVERITIES, f"Yoga '{yoga['name']}': invalid severity"

    def test_shubh_yogas_never_severe(self):
        for yoga in AANANDADI_YOGAS:
            if yoga["nature"] == "shubh":
                assert yoga["severe"] is False, f"Shubh yoga '{yoga['name']}' has severe=True"

    def test_severe_field_is_bool(self):
        for yoga in AANANDADI_YOGAS:
            assert isinstance(yoga["severe"], bool), f"Yoga '{yoga['name']}': severe must be bool"

    def test_exactly_four_severe_yogas(self):
        severe = {y["name"] for y in AANANDADI_YOGAS if y["severe"]}
        assert severe == {"Kaal", "Utpat", "Mrityu", "Rakshasa"}

    def test_severe_yogas_have_full_day_varjya(self):
        for yoga in AANANDADI_YOGAS:
            if yoga["severe"]:
                assert yoga["varjya"] == "full_day", \
                    f"Severe yoga '{yoga['name']}' must have full_day varjya"

    def test_exactly_five_highly_auspicious(self):
        ha = {y["name"] for y in AANANDADI_YOGAS if y["severity"] == "highly_auspicious"}
        assert ha == {"Anand", "Shreevatsa", "Padma", "Siddhi", "Amrut"}

    def test_varjya_is_valid_type(self):
        for yoga in AANANDADI_YOGAS:
            v = yoga["varjya"]
            assert v is None or v == "full_day" or (isinstance(v, tuple) and len(v) == 2), \
                f"Yoga '{yoga['name']}': invalid varjya {v!r}"

    def test_varjya_tuple_values_are_non_negative(self):
        for yoga in AANANDADI_YOGAS:
            if isinstance(yoga["varjya"], tuple):
                ghati, pala = yoga["varjya"]
                assert ghati >= 0 and pala >= 0, f"Yoga '{yoga['name']}' varjya has negative values"

    def test_anand_is_index_1_and_highly_auspicious(self):
        assert AANANDADI_YOGAS[0]["name"] == "Anand"
        assert AANANDADI_YOGAS[0]["nature"] == "shubh"
        assert AANANDADI_YOGAS[0]["severity"] == "highly_auspicious"

    def test_kaal_is_index_2_and_severe(self):
        assert AANANDADI_YOGAS[1]["name"] == "Kaal"
        assert AANANDADI_YOGAS[1]["severe"] is True
        assert AANANDADI_YOGAS[1]["varjya"] == "full_day"

    def test_utpat_is_index_16_and_severe(self):
        assert AANANDADI_YOGAS[15]["name"] == "Utpat"
        assert AANANDADI_YOGAS[15]["severe"] is True

    def test_mrityu_is_index_17_and_severe(self):
        assert AANANDADI_YOGAS[16]["name"] == "Mrityu"
        assert AANANDADI_YOGAS[16]["severe"] is True

    def test_amrut_is_index_21_and_highly_auspicious(self):
        assert AANANDADI_YOGAS[20]["name"] == "Amrut"
        assert AANANDADI_YOGAS[20]["severity"] == "highly_auspicious"
        assert AANANDADI_YOGAS[20]["varjya"] is None

    def test_rakshasa_is_index_25_and_severe(self):
        assert AANANDADI_YOGAS[24]["name"] == "Rakshasa"
        assert AANANDADI_YOGAS[24]["severe"] is True

    def test_vriddhi_is_index_28(self):
        assert AANANDADI_YOGAS[27]["name"] == "Vriddhi"
        assert AANANDADI_YOGAS[27]["nature"] == "shubh"


# ---------------------------------------------------------------------------
# Dainika Rules
# ---------------------------------------------------------------------------

class TestDainikaRules:
    def test_exactly_44_rules(self):
        assert len(DAINIKA_RULES) == 44

    def test_names_unique_except_intentional_duplicates(self):
        # Raj Yog (3 rules) and Kumar Yog (Tyajya) (4 per-vara rules) are intentional duplicates
        names = [r["name"] for r in DAINIKA_RULES]
        non_duplicate_names = {n for n in names if names.count(n) == 1}
        assert len(non_duplicate_names) == len(set(non_duplicate_names))

    def test_required_keys_present(self):
        required = {"name", "nature", "trigger", "severity", "meaning", "vara_map"}
        for rule in DAINIKA_RULES:
            missing = required - rule.keys()
            assert not missing, f"Rule '{rule.get('name')}' missing: {missing}"

    def test_nature_values_valid(self):
        for rule in DAINIKA_RULES:
            assert rule["nature"] in _NATURES

    def test_trigger_values_valid(self):
        for rule in DAINIKA_RULES:
            assert rule["trigger"] in _DAINIKA_TRIGGERS

    def test_severity_values_valid(self):
        for rule in DAINIKA_RULES:
            assert rule["severity"] in _SEVERITIES

    def test_shubh_rules_never_severe(self):
        for rule in DAINIKA_RULES:
            if rule["nature"] == "shubh":
                assert not rule.get("severe", False), f"Shubh rule '{rule['name']}' has severe=True"

    def test_vara_keys_in_range(self):
        for rule in DAINIKA_RULES:
            for vara in rule["vara_map"]:
                assert isinstance(vara, int) and 0 <= vara <= 6, \
                    f"Rule '{rule['name']}' vara key {vara!r} out of 0–6"

    def test_tithi_and_nakshatra_rules_have_extra_fields(self):
        compound = [r for r in DAINIKA_RULES if r["trigger"] == "tithi_and_nakshatra"]
        assert len(compound) >= 1, "No tithi_and_nakshatra rules found"
        for rule in compound:
            assert "tithi_values" in rule, f"'{rule['name']}' missing tithi_values"
            assert "nakshatra_values" in rule, f"'{rule['name']}' missing nakshatra_values"
            assert isinstance(rule["tithi_values"], list)
            assert isinstance(rule["nakshatra_values"], list)

    def test_tripushkar_rule(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Tripushkar")
        assert rule["nature"] == "ashubh"
        assert rule["trigger"] == "tithi_and_nakshatra"
        assert set(rule["vara_map"].keys()) == {0, 2, 6}
        assert set(rule["tithi_values"]) == {2, 7, 12, 17, 22, 27}  # both Shukla & Krishna paksha
        assert set(rule["nakshatra_values"]) == {3, 7, 12, 16, 21, 25}

    def test_dwipushkar_rule(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Dwipushkar")
        assert rule["nature"] == "ashubh"
        assert rule["trigger"] == "tithi_and_nakshatra"
        assert set(rule["vara_map"].keys()) == {0, 3, 5}
        assert set(rule["tithi_values"]) == {2, 7, 12, 17, 22, 27}
        # Mrigashira(5), Chitra(14), Dhanishtha(23) — 2-to-2 rashi split creates double effect
        assert set(rule["nakshatra_values"]) == {5, 14, 23}

    def test_amrit_siddhi_rule(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Amrit Siddhi")
        assert rule["nature"] == "shubh"
        assert rule["severity"] == "highly_auspicious"
        assert rule["trigger"] == "nakshatra"
        assert rule["vara_map"][0] == [13]   # Sunday: Hasta
        assert rule["vara_map"][4] == [8]    # Thursday: Pushya

    def test_exactly_four_severe_dainika_rules(self):
        severe = {r["name"] for r in DAINIKA_RULES if r.get("severe", False)}
        assert severe == {"Mrityu Yoga Tithi", "Mrityu Yoga Nakshatra", "Yam Ghant", "Rakshas Yoga"}

    def test_sarvartha_siddhi_is_highly_auspicious(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Sarvartha Siddhi")
        assert rule["nature"] == "shubh"
        assert rule["severity"] == "highly_auspicious"

    def test_guru_pushya_amrit(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Guru Pushya Amrit")
        assert rule["severity"] == "highly_auspicious"
        assert list(rule["vara_map"].keys()) == [4]   # Thursday only
        assert rule["vara_map"][4] == [8]              # Pushya

    def test_ravi_pushya_amrit(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Ravi Pushya Amrit")
        assert rule["severity"] == "highly_auspicious"
        assert list(rule["vara_map"].keys()) == [0]   # Sunday only
        assert rule["vara_map"][0] == [8]              # Pushya

    def test_dusht_tithi_exists_and_ashubh(self):
        rule = next((r for r in DAINIKA_RULES if r["name"] == "Dusht Tithi"), None)
        assert rule is not None
        assert rule["nature"] == "ashubh"
        assert rule["trigger"] == "tithi"

    def test_sthir_yog_and_kumar_yog_in_dainika_rules(self):
        names = {r["name"] for r in DAINIKA_RULES}
        assert "Kumar Yog" in names
        assert "Sthir Yog" in names
        assert "Raj Yog" in names

    def test_siddhi_yoga_tithi_map(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Siddhi Yoga Tithi")
        assert rule["nature"] == "shubh"
        assert rule["vara_map"][2] == [3, 8, 13]   # Tuesday
        assert rule["vara_map"][4] == [5, 10, 15]  # Thursday

    def test_mrityu_yoga_tithi_map(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Mrityu Yoga Tithi")
        assert rule["vara_map"][0] == [1, 6, 11]   # Sunday
        assert rule["vara_map"][1] == [2, 7, 12]   # Monday

    def test_mrityu_yoga_nakshatra_map(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Mrityu Yoga Nakshatra")
        assert rule["vara_map"][0] == [17]   # Sunday: Anuradha
        assert rule["vara_map"][3] == [1]    # Wednesday: Ashvini

    def test_yam_ghant_map(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Yam Ghant")
        assert rule["vara_map"][0] == [10]   # Sunday: Magha
        assert rule["vara_map"][4] == [3]    # Thursday: Kritika

    def test_rakshas_yoga_map(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Rakshas Yoga")
        assert rule["vara_map"][0] == [24]   # Sunday: Shatabhisha
        assert rule["vara_map"][1] == [1]    # Monday: Ashvini


# ---------------------------------------------------------------------------
# Kumar Yog, Raj Yog, Sthir Yog
# ---------------------------------------------------------------------------

class TestKumarYog:
    def test_kumar_yog_exists(self):
        rule = next((r for r in DAINIKA_RULES if r["name"] == "Kumar Yog"), None)
        assert rule is not None

    def test_kumar_yog_shubh_tithi_and_nakshatra(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Kumar Yog")
        assert rule["nature"] == "shubh"
        assert rule["trigger"] == "tithi_and_nakshatra"

    def test_kumar_yog_applies_mon_to_thu(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Kumar Yog")
        assert set(rule["vara_map"].keys()) == {1, 2, 3, 4}

    def test_kumar_yog_tithi_values(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Kumar Yog")
        assert set(rule["tithi_values"]) == {1, 5, 6, 10, 11}

    def test_kumar_yog_nakshatra_values(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Kumar Yog")
        # Ashvini(1), Rohini(4), Punarvasu(7), Magha(10), Hasta(13), Vishakha(16), Mula(19), Shravana(22), PurvaBhadrapada(25)
        assert set(rule["nakshatra_values"]) == {1, 4, 7, 10, 13, 16, 19, 22, 25}

    def test_kumar_yog_tyajya_has_four_vara_entries(self):
        rules = [r for r in DAINIKA_RULES if r["name"] == "Kumar Yog (Tyajya)"]
        assert len(rules) == 4, f"Expected 4 per-vara entries, got {len(rules)}"

    def test_kumar_yog_tyajya_is_ashubh(self):
        for rule in (r for r in DAINIKA_RULES if r["name"] == "Kumar Yog (Tyajya)"):
            assert rule["nature"] == "ashubh"
            assert rule["trigger"] == "tithi_and_nakshatra"

    def test_kumar_yog_tyajya_monday_pair(self):
        rule = next(r for r in DAINIKA_RULES
                    if r["name"] == "Kumar Yog (Tyajya)" and 1 in r["vara_map"])
        assert set(rule["tithi_values"]) == {11}
        assert set(rule["nakshatra_values"]) == {16}   # Vishakha

    def test_kumar_yog_tyajya_tuesday_pair(self):
        rule = next(r for r in DAINIKA_RULES
                    if r["name"] == "Kumar Yog (Tyajya)" and 2 in r["vara_map"])
        assert set(rule["tithi_values"]) == {10}
        assert set(rule["nakshatra_values"]) == {25}   # Purva Bhadrapada

    def test_kumar_yog_tyajya_wednesday_pair(self):
        rule = next(r for r in DAINIKA_RULES
                    if r["name"] == "Kumar Yog (Tyajya)" and 3 in r["vara_map"])
        assert set(rule["tithi_values"]) == {9}
        assert set(rule["nakshatra_values"]) == {1, 19}   # Ashvini, Mula

    def test_kumar_yog_tyajya_thursday_pair(self):
        rule = next(r for r in DAINIKA_RULES
                    if r["name"] == "Kumar Yog (Tyajya)" and 4 in r["vara_map"])
        assert set(rule["tithi_values"]) == {10}
        assert set(rule["nakshatra_values"]) == {4}   # Rohini


class TestRajYog:
    def test_raj_yog_has_three_rules(self):
        # Type-1 (Tue+Thu compact), Type-2 (Sun-Wed), Type-2 Thursday variant
        rules = [r for r in DAINIKA_RULES if r["name"] == "Raj Yog"]
        assert len(rules) == 3, f"Expected 3 Raj Yog rules, got {len(rules)}"

    def test_raj_yog_both_shubh(self):
        for rule in (r for r in DAINIKA_RULES if r["name"] == "Raj Yog"):
            assert rule["nature"] == "shubh"
            assert rule["severity"] == "highly_auspicious"
            assert rule["trigger"] == "tithi_and_nakshatra"

    def test_raj_yog_type1_tue_and_thu(self):
        # The compact rule: Tithis 2,7,12 + Mrigashira/Chitra/Dhanishtha on Tue+Thu
        rule = next(r for r in DAINIKA_RULES
                    if r["name"] == "Raj Yog" and set(r["vara_map"].keys()) == {2, 4})
        assert set(rule["tithi_values"]) == {2, 7, 12}
        assert set(rule["nakshatra_values"]) == {5, 14, 23}   # Mrigashira, Chitra, Dhanishtha

    def test_raj_yog_type2_covers_five_varas(self):
        # The expanded rule covers Sun-Thu (varas 0-4)
        all_varas = set()
        for r in DAINIKA_RULES:
            if r["name"] == "Raj Yog" and set(r["vara_map"].keys()) != {2, 4}:
                all_varas |= set(r["vara_map"].keys())
        assert all_varas == {0, 1, 2, 3, 4}

    def test_raj_yog_type2_tithi_values(self):
        for rule in DAINIKA_RULES:
            if rule["name"] == "Raj Yog" and set(rule.get("vara_map", {}).keys()) != {2, 4}:
                assert set(rule["tithi_values"]) == {2, 3, 7, 12, 15}


class TestSthirYog:
    def test_sthir_yog_exists(self):
        rule = next((r for r in DAINIKA_RULES if r["name"] == "Sthir Yog"), None)
        assert rule is not None

    def test_sthir_yog_shubh_tithi_and_nakshatra(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Sthir Yog")
        assert rule["nature"] == "shubh"
        assert rule["trigger"] == "tithi_and_nakshatra"

    def test_sthir_yog_thu_and_sat(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Sthir Yog")
        assert set(rule["vara_map"].keys()) == {4, 6}

    def test_sthir_yog_tithi_values(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Sthir Yog")
        assert set(rule["tithi_values"]) == {4, 8, 9, 13, 14}

    def test_sthir_yog_nakshatra_values(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Sthir Yog")
        # Ashvini(1), Kritika(3), Ardra(6), UttaraPhalguni(12), Swati(15), Jyeshtha(18), UttaraAshadha(21), Shatabhisha(24), Revati(27)
        assert set(rule["nakshatra_values"]) == {1, 3, 6, 12, 15, 18, 21, 24, 27}


# ---------------------------------------------------------------------------
# Special Rules
# ---------------------------------------------------------------------------

class TestSpecialRules:
    def test_exactly_4_rules(self):
        assert len(SPECIAL_RULES) == 4

    def test_all_names_unique(self):
        names = [r["name"] for r in SPECIAL_RULES]
        assert len(names) == len(set(names))

    def test_required_keys_present(self):
        required = {"name", "nature", "severity", "meaning", "trigger"}
        for rule in SPECIAL_RULES:
            missing = required - rule.keys()
            assert not missing, f"Rule '{rule.get('name')}' missing: {missing}"

    def test_all_are_ashubh(self):
        for rule in SPECIAL_RULES:
            assert rule["nature"] == "ashubh", f"Special rule '{rule['name']}' is not ashubh"

    def test_trigger_values_valid(self):
        for rule in SPECIAL_RULES:
            assert rule["trigger"] in _SPECIAL_TRIGGERS, f"Rule '{rule['name']}': invalid trigger"

    def test_expected_rule_names(self):
        names = {r["name"] for r in SPECIAL_RULES}
        assert names == {"Gandmool Nakshatra", "Panchak", "Bhadra (Vishti)", "Jwalamukhi"}

    def test_gandmool_trigger_is_gandmool(self):
        rule = next(r for r in SPECIAL_RULES if r["name"] == "Gandmool Nakshatra")
        assert rule["trigger"] == "gandmool"

    def test_panchak_trigger_is_panchak(self):
        rule = next(r for r in SPECIAL_RULES if r["name"] == "Panchak")
        assert rule["trigger"] == "panchak"

    def test_bhadra_trigger_is_bhadra(self):
        rule = next(r for r in SPECIAL_RULES if r["name"] == "Bhadra (Vishti)")
        assert rule["trigger"] == "bhadra"

    def test_jwalamukhi_trigger_is_jwalamukhi(self):
        rule = next(r for r in SPECIAL_RULES if r["name"] == "Jwalamukhi")
        assert rule["trigger"] == "jwalamukhi"
