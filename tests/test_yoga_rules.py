"""Data integrity tests for yoga_rules.py.

No ephemeris calls — pure structural validation of rule data.
Run these before creating yoga_rules.py; they should fail (RED) until GREEN.
"""

import pytest
from yoga_rules import AANANDADI_RULES, DAINIKA_RULES, SPECIAL_RULES

_PLANETS = frozenset({"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"})
_NATURES = frozenset({"shubh", "ashubh"})
_SEVERITIES = frozenset({"highly_auspicious", "auspicious", "inauspicious", "highly_inauspicious"})
_DAINIKA_TRIGGERS = frozenset({"tithi", "nakshatra", "tithi_and_nakshatra"})
_SPECIAL_TRIGGERS = frozenset({"gandmool", "panchak", "bhadra", "jwalamukhi"})


# ---------------------------------------------------------------------------
# Aanandadi Rules
# ---------------------------------------------------------------------------

class TestAanandadiRules:
    def test_exactly_28_rules(self):
        assert len(AANANDADI_RULES) == 28

    def test_all_names_unique(self):
        names = [r["name"] for r in AANANDADI_RULES]
        assert len(names) == len(set(names))

    def test_required_keys_present(self):
        required = {"name", "nature", "severe", "severity", "fal", "varjya", "meaning", "planet_map"}
        for rule in AANANDADI_RULES:
            missing = required - rule.keys()
            assert not missing, f"Rule '{rule.get('name')}' missing keys: {missing}"

    def test_nature_values_valid(self):
        for rule in AANANDADI_RULES:
            assert rule["nature"] in _NATURES, f"Rule '{rule['name']}': invalid nature '{rule['nature']}'"

    def test_severity_values_valid(self):
        for rule in AANANDADI_RULES:
            assert rule["severity"] in _SEVERITIES, f"Rule '{rule['name']}': invalid severity"

    def test_shubh_rules_never_severe(self):
        for rule in AANANDADI_RULES:
            if rule["nature"] == "shubh":
                assert rule["severe"] is False, f"Shubh rule '{rule['name']}' has severe=True"

    def test_ashubh_severely_rules_have_bool_severe(self):
        for rule in AANANDADI_RULES:
            assert isinstance(rule["severe"], bool), f"Rule '{rule['name']}': severe must be bool"

    def test_exactly_four_severe_rules(self):
        severe = {r["name"] for r in AANANDADI_RULES if r["severe"]}
        assert severe == {"Kaladand", "Utpat", "Mrityu", "Rakshas"}

    def test_severe_rules_have_full_day_varjya(self):
        for rule in AANANDADI_RULES:
            if rule["severe"]:
                assert rule["varjya"] == "full_day", f"Severe rule '{rule['name']}' must have full_day varjya"

    def test_exactly_three_highly_auspicious(self):
        ha = {r["name"] for r in AANANDADI_RULES if r["severity"] == "highly_auspicious"}
        assert ha == {"Aanand", "Amrit", "Vardhamaan"}

    def test_planet_map_has_all_seven_planets(self):
        for rule in AANANDADI_RULES:
            assert set(rule["planet_map"].keys()) == _PLANETS, f"Rule '{rule['name']}' planet_map wrong planets"

    def test_planet_map_nakshatra_indices_in_range(self):
        for rule in AANANDADI_RULES:
            for planet, nak in rule["planet_map"].items():
                assert 1 <= nak <= 28, f"Rule '{rule['name']}', {planet}: nak {nak} out of 1–28"

    def test_each_planet_covers_all_28_nakshatras_across_rules(self):
        for planet in _PLANETS:
            assigned = {r["planet_map"][planet] for r in AANANDADI_RULES}
            assert assigned == set(range(1, 29)), f"Planet {planet} doesn't cover all 28 nakshatras"

    def test_varjya_is_valid_type(self):
        for rule in AANANDADI_RULES:
            v = rule["varjya"]
            assert v is None or v == "full_day" or (isinstance(v, tuple) and len(v) == 2), \
                f"Rule '{rule['name']}': invalid varjya {v!r}"

    def test_varjya_tuple_values_are_non_negative(self):
        for rule in AANANDADI_RULES:
            if isinstance(rule["varjya"], tuple):
                ghati, pala = rule["varjya"]
                assert ghati >= 0 and pala >= 0, f"Rule '{rule['name']}' varjya has negative values"

    def test_aanand_planet_map(self):
        rule = next(r for r in AANANDADI_RULES if r["name"] == "Aanand")
        assert rule["planet_map"] == {
            "Sun": 1, "Moon": 5, "Mars": 9, "Mercury": 13,
            "Jupiter": 17, "Venus": 21, "Saturn": 24,
        }

    def test_mrityu_planet_map(self):
        rule = next(r for r in AANANDADI_RULES if r["name"] == "Mrityu")
        assert rule["planet_map"] == {
            "Sun": 17, "Moon": 21, "Mars": 24, "Mercury": 1,
            "Jupiter": 5, "Venus": 9, "Saturn": 13,
        }

    def test_rakshas_planet_map(self):
        rule = next(r for r in AANANDADI_RULES if r["name"] == "Rakshas")
        assert rule["planet_map"] == {
            "Sun": 24, "Moon": 1, "Mars": 5, "Mercury": 9,
            "Jupiter": 13, "Venus": 17, "Saturn": 21,
        }

    def test_kaladand_venus_is_abhijit(self):
        rule = next(r for r in AANANDADI_RULES if r["name"] == "Kaladand")
        assert rule["planet_map"]["Venus"] == 28

    def test_amrit_planet_map(self):
        rule = next(r for r in AANANDADI_RULES if r["name"] == "Amrit")
        assert rule["planet_map"] == {
            "Sun": 21, "Moon": 24, "Mars": 1, "Mercury": 5,
            "Jupiter": 9, "Venus": 13, "Saturn": 17,
        }

    def test_vardhamaan_planet_map(self):
        rule = next(r for r in AANANDADI_RULES if r["name"] == "Vardhamaan")
        assert rule["planet_map"] == {
            "Sun": 27, "Moon": 4, "Mars": 8, "Mercury": 12,
            "Jupiter": 16, "Venus": 20, "Saturn": 23,
        }


# ---------------------------------------------------------------------------
# Dainika Rules
# ---------------------------------------------------------------------------

class TestDainikaRules:
    def test_exactly_42_rules(self):
        assert len(DAINIKA_RULES) == 42

    def test_all_names_unique(self):
        names = [r["name"] for r in DAINIKA_RULES]
        assert len(names) == len(set(names))

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

    def test_seven_ashubh_tithivar_rules_exist(self):
        expected = {
            "Nal Banvas", "Pandav Nash", "Vibhishan Maran",
            "Sita Haran", "Lanka Bhang", "Pandav Jung", "Bali Raja Chhal",
        }
        names = {r["name"] for r in DAINIKA_RULES}
        assert expected <= names

    def test_nal_banvas_tuesday_tithi2(self):
        rule = next(r for r in DAINIKA_RULES if r["name"] == "Nal Banvas")
        assert rule["vara_map"] == {2: [2]}

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
