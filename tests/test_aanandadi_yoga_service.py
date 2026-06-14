"""
TDD tests for aanandadi_yoga_service.py

Run these BEFORE implementing the service — they should all fail initially (RED).
Then implement to GREEN.

Varjya is stored as (ghati, pala) tuples:
  duration_minutes = ghati * 24 + pala * (24/60)
- None      → no restriction
- "full_day"→ entire yoga forbidden (24:00)
- (0, 24)   → 9.6 min
- (0, 48)   → 19.2 min
- (1, 36)   → 38.4 min
- (2, 0)    → 48.0 min
- (2, 48)   → 67.2 min
"""

import unittest
from datetime import date

from astronomy import get_sunrise, local_date_anchor_jd
from location_service import get_timezone_name


JAIPUR_LAT = 26.9124
JAIPUR_LON = 75.7873
AYANAMSA = "Lahiri"

_VALID_RECOMMENDATIONS = frozenset(
    ("highly_auspicious", "auspicious", "caution", "avoid", "neutral")
)
_VALID_NATURES = frozenset(("shubh", "ashubh"))
_VALID_SEVERITIES = frozenset(
    ("highly_auspicious", "auspicious", "inauspicious", "highly_inauspicious")
)
_PLANETS = frozenset(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"))
_REQUIRED_YOGA_KEYS = frozenset((
    "name", "nature", "severity", "fal", "meaning", "severe",
    "triggering_planet", "trigger_nakshatra", "trigger_nakshatra_index",
    "start_time", "end_time", "start_local", "end_local",
    "varjya_minutes", "varjya_start_time", "varjya_end_time",
))


def _day_jds(d: date, lat: float, lon: float):
    tz = get_timezone_name(lat, lon)
    anchor = local_date_anchor_jd(d, tz)
    next_anchor = local_date_anchor_jd(date(d.year, d.month, d.day + 1), tz)
    sunrise = get_sunrise(anchor, lat, lon)
    next_sunrise = get_sunrise(next_anchor, lat, lon)
    return sunrise, next_sunrise, tz


# ---------------------------------------------------------------------------
# Phase-1 tests: validate the AANANDADI_RULES data structure (no ephemeris)
# ---------------------------------------------------------------------------

class TestAanandadiRulesIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from aanandadi_yoga_service import AANANDADI_RULES
        cls.rules = AANANDADI_RULES

    def test_has_28_rules(self):
        self.assertEqual(len(self.rules), 28)

    def test_rule_names_are_unique(self):
        names = [r["name"] for r in self.rules]
        self.assertEqual(len(names), len(set(names)))

    def test_each_rule_has_required_keys(self):
        required = {"name", "nature", "severe", "severity", "fal", "meaning",
                    "varjya", "planet_map"}
        for rule in self.rules:
            missing = required - rule.keys()
            self.assertFalse(missing, f"{rule['name']} missing keys: {missing}")

    def test_nature_is_shubh_or_ashubh(self):
        for rule in self.rules:
            self.assertIn(rule["nature"], _VALID_NATURES, rule["name"])

    def test_severity_is_valid(self):
        for rule in self.rules:
            self.assertIn(rule["severity"], _VALID_SEVERITIES, rule["name"])

    def test_planet_map_has_7_planets(self):
        for rule in self.rules:
            self.assertEqual(set(rule["planet_map"].keys()), _PLANETS, rule["name"])

    def test_nakshatra_indices_are_1_to_28(self):
        for rule in self.rules:
            for planet, nak in rule["planet_map"].items():
                self.assertIn(
                    nak, range(1, 29),
                    f"{rule['name']} {planet}: invalid nakshatra {nak}",
                )

    def test_nakshatra_indices_are_all_distinct_within_rule(self):
        """Each yoga should use 7 distinct nakshatras (one per planet)."""
        for rule in self.rules:
            values = list(rule["planet_map"].values())
            self.assertEqual(
                len(values), len(set(values)),
                f"{rule['name']} has duplicate nakshatra assignments",
            )

    def test_severe_yogas_have_full_day_varjya(self):
        for rule in self.rules:
            if rule["severe"]:
                self.assertEqual(
                    rule["varjya"], "full_day",
                    f"{rule['name']} is severe but varjya != full_day",
                )

    def test_shubh_yogas_are_not_severe(self):
        for rule in self.rules:
            if rule["nature"] == "shubh":
                self.assertFalse(rule["severe"], f"{rule['name']} shubh yoga marked severe")

    def test_severe_count_is_four(self):
        severe = [r["name"] for r in self.rules if r["severe"]]
        self.assertEqual(sorted(severe), sorted(["Kaladand", "Utpat", "Mrityu", "Rakshas"]))

    def test_highly_auspicious_count_is_three(self):
        ha = [r["name"] for r in self.rules if r["severity"] == "highly_auspicious"]
        self.assertEqual(sorted(ha), sorted(["Aanand", "Amrit", "Vardhamaan"]))

    def test_first_yoga_is_aanand(self):
        self.assertEqual(self.rules[0]["name"], "Aanand")

    def test_last_yoga_is_vardhamaan(self):
        self.assertEqual(self.rules[-1]["name"], "Vardhamaan")

    def test_aanand_planet_map(self):
        rule = next(r for r in self.rules if r["name"] == "Aanand")
        self.assertEqual(rule["planet_map"]["Sun"], 1)      # Ashvini
        self.assertEqual(rule["planet_map"]["Moon"], 5)     # Mrigashira
        self.assertEqual(rule["planet_map"]["Mars"], 9)     # Ashlesha
        self.assertEqual(rule["planet_map"]["Mercury"], 13) # Hasta
        self.assertEqual(rule["planet_map"]["Jupiter"], 17) # Anuradha
        self.assertEqual(rule["planet_map"]["Venus"], 21)   # Uttara Ashadha
        self.assertEqual(rule["planet_map"]["Saturn"], 24)  # Shatabhisha

    def test_mrityu_planet_map(self):
        rule = next(r for r in self.rules if r["name"] == "Mrityu")
        self.assertEqual(rule["planet_map"]["Sun"], 17)     # Anuradha
        self.assertEqual(rule["planet_map"]["Moon"], 21)    # Uttara Ashadha
        self.assertEqual(rule["planet_map"]["Mars"], 24)    # Shatabhisha
        self.assertEqual(rule["planet_map"]["Mercury"], 1)  # Ashvini
        self.assertEqual(rule["planet_map"]["Jupiter"], 5)  # Mrigashira
        self.assertEqual(rule["planet_map"]["Venus"], 9)    # Ashlesha
        self.assertEqual(rule["planet_map"]["Saturn"], 13)  # Hasta

    def test_rakshas_planet_map(self):
        rule = next(r for r in self.rules if r["name"] == "Rakshas")
        self.assertEqual(rule["planet_map"]["Sun"], 24)     # Shatabhisha
        self.assertEqual(rule["planet_map"]["Moon"], 1)     # Ashvini
        self.assertEqual(rule["planet_map"]["Mars"], 5)     # Mrigashira
        self.assertEqual(rule["planet_map"]["Mercury"], 9)  # Ashlesha
        self.assertEqual(rule["planet_map"]["Jupiter"], 13) # Hasta
        self.assertEqual(rule["planet_map"]["Venus"], 17)   # Anuradha
        self.assertEqual(rule["planet_map"]["Saturn"], 21)  # Uttara Ashadha

    def test_kaladand_has_abhijit_for_venus(self):
        rule = next(r for r in self.rules if r["name"] == "Kaladand")
        self.assertEqual(rule["planet_map"]["Venus"], 28)  # Abhijit

    def test_amrit_is_highly_auspicious(self):
        rule = next(r for r in self.rules if r["name"] == "Amrit")
        self.assertEqual(rule["nature"], "shubh")
        self.assertEqual(rule["severity"], "highly_auspicious")
        self.assertIsNone(rule["varjya"])

    def test_varjya_values_are_valid(self):
        valid_tuples = {(0, 24), (0, 48), (1, 36), (2, 0), (2, 48)}
        for rule in self.rules:
            v = rule["varjya"]
            if v is None or v == "full_day":
                continue
            self.assertIn(v, valid_tuples, f"{rule['name']} has unexpected varjya {v}")


# ---------------------------------------------------------------------------
# Phase-2 tests: _lon_to_nakshatra and get_planet_nakshatras
# ---------------------------------------------------------------------------

class TestLonToNakshatra(unittest.TestCase):

    def test_standard_nakshatra_in_range(self):
        from aanandadi_yoga_service import _lon_to_nakshatra
        # 0° = Ashvini (1)
        self.assertEqual(_lon_to_nakshatra(0.0), 1)
        # 13.333° = boundary Bharani (2)
        self.assertEqual(_lon_to_nakshatra(14.0), 2)

    def test_abhijit_range_returns_28(self):
        from aanandadi_yoga_service import _lon_to_nakshatra
        # Abhijit: ~276.667° – ~280.889°
        self.assertEqual(_lon_to_nakshatra(277.0), 28)
        self.assertEqual(_lon_to_nakshatra(280.0), 28)

    def test_just_before_abhijit_returns_21(self):
        from aanandadi_yoga_service import _lon_to_nakshatra
        # 276° is still in Uttara Ashadha (21)
        self.assertEqual(_lon_to_nakshatra(276.0), 21)

    def test_just_after_abhijit_returns_22(self):
        from aanandadi_yoga_service import _lon_to_nakshatra
        # 281° is in Shravana (22)
        self.assertEqual(_lon_to_nakshatra(281.0), 22)

    def test_handles_360_degree_wrap(self):
        from aanandadi_yoga_service import _lon_to_nakshatra
        self.assertEqual(_lon_to_nakshatra(360.0), 1)  # wraps to 0 = Ashvini


class TestGetPlanetNakshatras(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        d = date(2026, 6, 12)
        cls.sunrise, cls.next_sunrise, cls.tz = _day_jds(d, JAIPUR_LAT, JAIPUR_LON)

    def test_returns_dict_with_7_planets(self):
        from aanandadi_yoga_service import get_planet_nakshatras
        result = get_planet_nakshatras(self.sunrise, AYANAMSA)
        self.assertEqual(set(result.keys()), _PLANETS)

    def test_all_values_are_valid_nakshatra_indices(self):
        from aanandadi_yoga_service import get_planet_nakshatras
        result = get_planet_nakshatras(self.sunrise, AYANAMSA)
        for planet, idx in result.items():
            self.assertIn(idx, range(1, 29), f"{planet}: invalid index {idx}")


# ---------------------------------------------------------------------------
# Phase-3 tests: detect_aanandadi_yogas_for_day (shape + invariants)
# ---------------------------------------------------------------------------

class TestDetectAanandadiYogasForDay(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from aanandadi_yoga_service import detect_aanandadi_yogas_for_day
        d = date(2026, 6, 12)
        sunrise, next_sunrise, tz = _day_jds(d, JAIPUR_LAT, JAIPUR_LON)
        cls.result = detect_aanandadi_yogas_for_day(
            sunrise_jd=sunrise,
            next_sunrise_jd=next_sunrise,
            tz_name=tz,
            ayanamsa=AYANAMSA,
        )

    def test_returns_aanandadi_yogas_key(self):
        self.assertIn("aanandadi_yogas", self.result)

    def test_returns_aanandadi_recommendation_key(self):
        self.assertIn("aanandadi_recommendation", self.result)

    def test_recommendation_is_valid(self):
        self.assertIn(self.result["aanandadi_recommendation"], _VALID_RECOMMENDATIONS)

    def test_yogas_is_a_list(self):
        self.assertIsInstance(self.result["aanandadi_yogas"], list)

    def test_each_yoga_has_required_keys(self):
        for yoga in self.result["aanandadi_yogas"]:
            missing = _REQUIRED_YOGA_KEYS - yoga.keys()
            self.assertFalse(missing, f"{yoga.get('name')} missing: {missing}")

    def test_triggering_planet_is_valid(self):
        for yoga in self.result["aanandadi_yogas"]:
            self.assertIn(yoga["triggering_planet"], _PLANETS, yoga["name"])

    def test_trigger_nakshatra_index_matches_planet_map(self):
        from aanandadi_yoga_service import AANANDADI_RULES
        rule_map = {r["name"]: r for r in AANANDADI_RULES}
        for yoga in self.result["aanandadi_yogas"]:
            rule = rule_map[yoga["name"]]
            expected_nak = rule["planet_map"][yoga["triggering_planet"]]
            self.assertEqual(yoga["trigger_nakshatra_index"], expected_nak, yoga["name"])

    def test_start_time_before_end_time(self):
        for yoga in self.result["aanandadi_yogas"]:
            if yoga["start_local"] and yoga["end_local"]:
                self.assertLessEqual(
                    yoga["start_local"], yoga["end_local"],
                    f"{yoga['name']} via {yoga['triggering_planet']}: "
                    f"start={yoga['start_local']} >= end={yoga['end_local']}",
                )

    def test_nature_is_valid(self):
        for yoga in self.result["aanandadi_yogas"]:
            self.assertIn(yoga["nature"], _VALID_NATURES, yoga["name"])

    def test_severity_is_valid(self):
        for yoga in self.result["aanandadi_yogas"]:
            self.assertIn(yoga["severity"], _VALID_SEVERITIES, yoga["name"])

    def test_severe_yogas_have_avoid_recommendation(self):
        has_severe = any(y["severe"] for y in self.result["aanandadi_yogas"])
        if has_severe:
            self.assertEqual(self.result["aanandadi_recommendation"], "avoid")

    def test_no_duplicate_planet_yoga_pairs(self):
        seen = set()
        for yoga in self.result["aanandadi_yogas"]:
            key = (yoga["name"], yoga["triggering_planet"])
            self.assertNotIn(key, seen, f"Duplicate: {key}")
            seen.add(key)


# ---------------------------------------------------------------------------
# Phase-4 tests: varjya window computation
# ---------------------------------------------------------------------------

class TestVarjyaComputation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from aanandadi_yoga_service import _build_varjya, _varjya_total_minutes
        cls.build = staticmethod(_build_varjya)
        cls.total_min = staticmethod(_varjya_total_minutes)

    def test_none_varjya_returns_all_none(self):
        tz = get_timezone_name(JAIPUR_LAT, JAIPUR_LON)
        sunrise, _, _ = _day_jds(date(2026, 6, 12), JAIPUR_LAT, JAIPUR_LON)
        from astronomy import jd_to_zoned_datetime
        dt = jd_to_zoned_datetime(sunrise, tz)
        result = self.build(None, sunrise, dt, tz)
        self.assertIsNone(result["varjya_minutes"])
        self.assertIsNone(result["varjya_start_time"])
        self.assertIsNone(result["varjya_end_time"])

    def test_full_day_varjya(self):
        tz = get_timezone_name(JAIPUR_LAT, JAIPUR_LON)
        sunrise, _, _ = _day_jds(date(2026, 6, 12), JAIPUR_LAT, JAIPUR_LON)
        from astronomy import jd_to_zoned_datetime
        dt = jd_to_zoned_datetime(sunrise, tz)
        result = self.build("full_day", sunrise, dt, tz)
        self.assertEqual(result["varjya_minutes"], "full_day")
        self.assertIsNone(result["varjya_start_time"])
        self.assertIsNone(result["varjya_end_time"])

    def test_partial_varjya_produces_time_strings(self):
        tz = get_timezone_name(JAIPUR_LAT, JAIPUR_LON)
        sunrise, _, _ = _day_jds(date(2026, 6, 12), JAIPUR_LAT, JAIPUR_LON)
        from astronomy import jd_to_zoned_datetime
        dt = jd_to_zoned_datetime(sunrise, tz)
        result = self.build((2, 0), sunrise, dt, tz)
        self.assertIsInstance(result["varjya_minutes"], float)
        self.assertGreater(result["varjya_minutes"], 0)
        self.assertIsNotNone(result["varjya_start_time"])
        self.assertIsNotNone(result["varjya_end_time"])

    def test_varjya_minutes_values(self):
        self.assertAlmostEqual(self.total_min((0, 24)), 9.6,  places=3)
        self.assertAlmostEqual(self.total_min((0, 48)), 19.2, places=3)
        self.assertAlmostEqual(self.total_min((1, 36)), 38.4, places=3)
        self.assertAlmostEqual(self.total_min((2,  0)), 48.0, places=3)
        self.assertAlmostEqual(self.total_min((2, 48)), 67.2, places=3)

    def test_all_varjya_durations_are_distinct(self):
        values = [(0,24),(0,48),(1,36),(2,0),(2,48)]
        minutes = [self.total_min(v) for v in values]
        self.assertEqual(len(minutes), len(set(minutes)))

    def test_varjya_end_is_after_start(self):
        tz = get_timezone_name(JAIPUR_LAT, JAIPUR_LON)
        sunrise, _, _ = _day_jds(date(2026, 6, 12), JAIPUR_LAT, JAIPUR_LON)
        from astronomy import jd_to_zoned_datetime
        dt = jd_to_zoned_datetime(sunrise, tz)
        for spec in [(0, 24), (0, 48), (1, 36), (2, 0), (2, 48)]:
            result = self.build(spec, sunrise, dt, tz)
            self.assertLessEqual(
                result["varjya_start_time"], result["varjya_end_time"],
                f"varjya {spec}: start > end",
            )


# ---------------------------------------------------------------------------
# Phase-5 tests: known-date spot checks
# ---------------------------------------------------------------------------

class TestKnownDateSpotChecks(unittest.TestCase):
    """
    Use the known planetary positions to verify specific yogas fire.
    These are regression anchors — update if ephemeris changes ayanamsa.
    """

    def _detect(self, d: date):
        from aanandadi_yoga_service import detect_aanandadi_yogas_for_day
        sunrise, next_sunrise, tz = _day_jds(d, JAIPUR_LAT, JAIPUR_LON)
        return detect_aanandadi_yogas_for_day(
            sunrise_jd=sunrise,
            next_sunrise_jd=next_sunrise,
            tz_name=tz,
            ayanamsa=AYANAMSA,
        )

    def _active_pairs(self, result):
        return {(y["name"], y["triggering_planet"]) for y in result["aanandadi_yogas"]}

    def test_returns_at_least_one_yoga_most_days(self):
        result = self._detect(date(2026, 6, 12))
        # On any day, at least 1 of 7 planets should trigger a yoga
        # (in theory all 28 nakshatras are covered, so at least 7 yogas fire)
        self.assertGreater(len(result["aanandadi_yogas"]), 0)

    def test_each_planet_triggers_exactly_one_yoga(self):
        """Since all 28 yogas partition the 28 nakshatras per planet,
        each planet is always in exactly one yoga's nakshatra. So every planet
        triggers exactly one yoga per day."""
        result = self._detect(date(2026, 6, 12))
        from aanandadi_yoga_service import get_planet_nakshatras
        sunrise, _, tz = _day_jds(date(2026, 6, 12), JAIPUR_LAT, JAIPUR_LON)
        planet_naks = get_planet_nakshatras(sunrise, AYANAMSA)

        planets_in_result = {y["triggering_planet"] for y in result["aanandadi_yogas"]}
        # Every planet that has a nakshatra between 1-28 must appear exactly once
        for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            count = sum(
                1 for y in result["aanandadi_yogas"]
                if y["triggering_planet"] == planet
            )
            self.assertEqual(count, 1, f"{planet} triggered {count} yogas (expected 1)")

    def test_total_yoga_count_is_7(self):
        """Each of the 7 planets is always in exactly one of the 28 yoga nakshatras,
        so total active entries must always be exactly 7."""
        result = self._detect(date(2026, 6, 12))
        self.assertEqual(len(result["aanandadi_yogas"]), 7)

    def test_total_yoga_count_is_7_on_another_date(self):
        result = self._detect(date(2026, 6, 7))
        self.assertEqual(len(result["aanandadi_yogas"]), 7)
