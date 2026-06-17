"""Integration tests for yoga_service.py.

Uses real ephemeris (swisseph) and known dates from Jaipur, India.
These tests verify that specific yogas fire (or don't fire) on well-known
dates that were validated against traditional almanac sources.

Coordinates: Jaipur, India — lat=26.9124, lon=75.7873
Timezone: Asia/Kolkata
Ayanamsa: Lahiri (default)
"""

import pytest
from datetime import date

LAT = 26.9124
LON = 75.7873
TZ = "Asia/Kolkata"


# ---------------------------------------------------------------------------
# Fixtures: compute sunrise JDs for known test dates
# ---------------------------------------------------------------------------

def _sunrise(d: date) -> tuple[float, float]:
    """Return (sunrise_jd, next_sunrise_jd) for Jaipur on date d."""
    from astronomy import get_sunrise, local_date_anchor_jd
    from datetime import timedelta

    anchor = local_date_anchor_jd(d, TZ)
    next_anchor = local_date_anchor_jd(d + timedelta(days=1), TZ)
    return get_sunrise(anchor, LAT, LON), get_sunrise(next_anchor, LAT, LON)


def _detect(d: date) -> dict:
    from yoga_service import detect_all_yogas_for_day
    sunrise_jd, next_sunrise_jd = _sunrise(d)
    return detect_all_yogas_for_day(
        date_obj=d,
        sunrise_jd=sunrise_jd,
        next_sunrise_jd=next_sunrise_jd,
        tz_name=TZ,
    )


def _yoga_names(result: dict, key: str) -> set[str]:
    return {y["name"] for y in result[key]}


def _has_yoga(result: dict, key: str, name: str) -> bool:
    return any(y["name"] == name for y in result[key])


# ---------------------------------------------------------------------------
# Response structure tests
# ---------------------------------------------------------------------------

class TestResponseStructure:
    def test_required_top_level_keys(self):
        result = _detect(date(2026, 6, 7))
        for key in ("vara", "tithi", "nakshatra", "yogas", "recommendation",
                    "aanandadi_yogas", "aanandadi_recommendation", "special_yogas"):
            assert key in result, f"Missing top-level key: '{key}'"

    def test_vara_in_range(self):
        result = _detect(date(2026, 6, 7))
        assert 0 <= result["vara"] <= 6

    def test_tithi_in_range(self):
        result = _detect(date(2026, 6, 7))
        assert 1 <= result["tithi"] <= 30

    def test_nakshatra_in_range(self):
        result = _detect(date(2026, 6, 7))
        assert 1 <= result["nakshatra"] <= 28

    def test_recommendation_is_valid_string(self):
        valid = {"highly_auspicious", "auspicious", "caution", "avoid", "neutral"}
        result = _detect(date(2026, 6, 7))
        assert result["recommendation"] in valid
        assert result["aanandadi_recommendation"] in valid

    def test_aanandadi_always_returns_seven_matches(self):
        result = _detect(date(2026, 6, 7))
        assert len(result["aanandadi_yogas"]) == 7

    def test_dainika_yoga_has_required_fields(self):
        result = _detect(date(2026, 6, 18))
        yogas = result["yogas"]
        assert len(yogas) > 0
        for y in yogas:
            for field in ("name", "nature", "severity", "severe", "meaning",
                          "trigger_kind", "trigger_detail", "start_time", "end_time",
                          "start_local", "end_local", "start_jd", "end_jd"):
                assert field in y, f"Dainika yoga missing field '{field}'"

    def test_aanandadi_yoga_has_required_fields(self):
        result = _detect(date(2026, 6, 7))
        for y in result["aanandadi_yogas"]:
            for field in ("name", "nature", "severity", "fal", "meaning", "severe",
                          "triggering_planet", "trigger_nakshatra_index",
                          "start_time", "end_time", "start_local", "end_local",
                          "varjya_minutes"):
                assert field in y, f"Aanandadi yoga missing field '{field}'"

    def test_special_yoga_has_required_fields(self):
        result = _detect(date(2026, 3, 20))  # Gandmool day
        special = result["special_yogas"]
        assert len(special) > 0
        for y in special:
            for field in ("name", "nature", "severity", "meaning",
                          "start_time", "end_time", "start_local", "end_local"):
                assert field in y, f"Special yoga missing field '{field}'"

    def test_time_strings_are_hhmm_format(self):
        result = _detect(date(2026, 6, 18))
        for y in result["yogas"]:
            for field in ("start_time", "end_time"):
                t = y[field]
                assert len(t) == 5 and t[2] == ":", f"Time '{t}' not HH:MM format"

    def test_start_time_before_end_time(self):
        result = _detect(date(2026, 6, 18))
        for y in result["yogas"]:
            assert y["start_jd"] < y["end_jd"], f"Yoga '{y['name']}' has start >= end"


# ---------------------------------------------------------------------------
# Known-date regression: Dainika yogas
# ---------------------------------------------------------------------------

class TestKnownDatnikaDates:
    def test_guru_pushya_amrit_june18_2026(self):
        # Thursday (vara=4) + Pushya (nak 8) → Guru Pushya Amrit
        result = _detect(date(2026, 6, 18))
        assert _has_yoga(result, "yogas", "Guru Pushya Amrit"), \
            "Guru Pushya Amrit must fire on Thursday + Pushya"

    def test_amrit_siddhi_june18_2026(self):
        result = _detect(date(2026, 6, 18))
        assert _has_yoga(result, "yogas", "Amrit Siddhi"), \
            "Amrit Siddhi must fire on June 18 (Thursday + Pushya=8)"

    def test_sarvartha_siddhi_june18_2026(self):
        result = _detect(date(2026, 6, 18))
        assert _has_yoga(result, "yogas", "Sarvartha Siddhi"), \
            "Sarvartha Siddhi must fire on June 18 (Thursday + Pushya in vara_map[4])"

    def test_june18_recommendation_is_mixed(self):
        # Mrityu Yoga Tithi (severe) alongside Guru Pushya + Amrit Siddhi (highly_auspicious)
        # → mixed signal: real danger but also real opportunity
        result = _detect(date(2026, 6, 18))
        assert result["recommendation"] == "mixed"
        assert _has_yoga(result, "yogas", "Mrityu Yoga Tithi")

    def test_guru_pushya_amrit_april23_2026(self):
        result = _detect(date(2026, 4, 23))
        assert _has_yoga(result, "yogas", "Guru Pushya Amrit")

    def test_amrit_siddhi_april23_2026(self):
        result = _detect(date(2026, 4, 23))
        assert _has_yoga(result, "yogas", "Amrit Siddhi")

    def test_april23_has_both_shubh_and_ashubh(self):
        # Tithi 7 on Thursday triggers ashubh yogas; Pushya brings shubh ones
        result = _detect(date(2026, 4, 23))
        names = _yoga_names(result, "yogas")
        assert any(result["yogas"][i]["nature"] == "shubh" for i in range(len(result["yogas"])))
        assert any(result["yogas"][i]["nature"] == "ashubh" for i in range(len(result["yogas"])))

    def test_ravi_pushya_amrit_feb1_2026(self):
        # Sunday + Pushya → Ravi Pushya Amrit
        result = _detect(date(2026, 2, 1))
        assert _has_yoga(result, "yogas", "Ravi Pushya Amrit")

    def test_tripushkar_june21_2026(self):
        result = _detect(date(2026, 6, 21))
        assert _has_yoga(result, "yogas", "Tripushkar"), \
            "Tripushkar must fire on June 21 2026"

    def test_dwipushkar_june21_2026(self):
        result = _detect(date(2026, 6, 21))
        assert _has_yoga(result, "yogas", "Dwipushkar"), \
            "Dwipushkar must fire on June 21 2026"

    def test_tripushkar_fires_april19_2026(self):
        result = _detect(date(2026, 4, 19))
        assert _has_yoga(result, "yogas", "Tripushkar")

    def test_amrit_siddhi_march20_2026(self):
        result = _detect(date(2026, 3, 20))
        assert _has_yoga(result, "yogas", "Amrit Siddhi")

    def test_amrit_siddhi_july11_2026(self):
        result = _detect(date(2026, 7, 11))
        assert _has_yoga(result, "yogas", "Amrit Siddhi")

    def test_tripushkar_july11_2026(self):
        result = _detect(date(2026, 7, 11))
        assert _has_yoga(result, "yogas", "Tripushkar")

    def test_no_tripushkar_on_thursday(self):
        # Thursday is not a Tripushkar vara (0,2,6 only)
        result = _detect(date(2026, 6, 18))
        assert not _has_yoga(result, "yogas", "Tripushkar")

    def test_no_ravi_pushya_on_monday(self):
        result = _detect(date(2026, 2, 2))  # Monday
        assert not _has_yoga(result, "yogas", "Ravi Pushya Amrit")


# ---------------------------------------------------------------------------
# Known-date regression: Aanandadi yogas
# ---------------------------------------------------------------------------

class TestKnownAanandadiDates:
    def test_june7_moon_in_dhanishtha(self):
        # Regression: Moon must be in Dhanishtha (23) at sunrise on June 7 2026
        result = _detect(date(2026, 6, 7))
        moon_match = next(
            (y for y in result["aanandadi_yogas"] if y["triggering_planet"] == "Moon"),
            None,
        )
        assert moon_match is not None
        assert moon_match["trigger_nakshatra_index"] == 23, \
            f"Moon should be in Dhanishtha (23), got {moon_match['trigger_nakshatra_index']}"

    def test_aanandadi_yoga_names_are_valid(self):
        from yoga_rules import AANANDADI_RULES
        valid_names = {r["name"] for r in AANANDADI_RULES}
        result = _detect(date(2026, 6, 7))
        for y in result["aanandadi_yogas"]:
            assert y["name"] in valid_names, f"Invalid Aanandadi yoga name: {y['name']}"

    def test_aanandadi_severe_yoga_forces_avoid(self):
        from yoga_rules import AANANDADI_RULES
        severe_names = {r["name"] for r in AANANDADI_RULES if r["severe"]}
        # Find a date where a severe yoga fires and check recommendation
        result = _detect(date(2026, 6, 7))
        for yoga in result["aanandadi_yogas"]:
            if yoga["name"] in severe_names:
                assert result["aanandadi_recommendation"] == "avoid"
                break

    def test_aanandadi_varjya_end_after_start(self):
        result = _detect(date(2026, 6, 12))
        for y in result["aanandadi_yogas"]:
            if y["varjya_minutes"] is not None and y["varjya_minutes"] != "full_day":
                assert y.get("varjya_start_jd") is not None
                assert y.get("varjya_end_jd") is not None
                # varjya must end after it starts
                assert y["varjya_end_jd"] > y["varjya_start_jd"]

    def test_triggering_planets_are_unique(self):
        result = _detect(date(2026, 6, 12))
        planets = [y["triggering_planet"] for y in result["aanandadi_yogas"]]
        assert len(planets) == len(set(planets)), "Each planet must trigger exactly one yoga per day"

    def test_slow_planet_window_exceeds_two_days(self):
        # Slow planets spend at least 7 days in a nakshatra (Sun ~14d, Mars ~7d,
        # Mercury/Venus ~5-14d, Jupiter ~18d, Saturn months).
        # A 2-day threshold clearly distinguishes real nak windows from the
        # sunrise→next_sunrise fallback (~1.00012 days).
        result = _detect(date(2026, 6, 18))
        for y in result["aanandadi_yogas"]:
            if y["triggering_planet"] != "Moon":
                duration_days = y["end_jd"] - y["start_jd"]
                assert duration_days > 2.0, (
                    f"{y['triggering_planet']} ({y['name']}) window is only "
                    f"{duration_days:.2f} days — expected nakshatra transition times, not sunrise window"
                )

    def test_slow_planet_start_end_times_differ(self):
        # The 05:33–05:33 bug: start_time == end_time for slow planets because
        # sunrise times barely change day-to-day. After the fix, times must differ.
        result = _detect(date(2026, 6, 18))
        for y in result["aanandadi_yogas"]:
            if y["triggering_planet"] != "Moon":
                assert y["start_time"] != y["end_time"], (
                    f"{y['triggering_planet']} shows same start/end time: {y['start_time']}"
                )


# ---------------------------------------------------------------------------
# Known-date regression: Special yogas
# ---------------------------------------------------------------------------

class TestKnownSpecialDates:
    def test_gandmool_march20_2026(self):
        result = _detect(date(2026, 3, 20))
        assert _has_yoga(result, "special_yogas", "Gandmool Nakshatra"), \
            "Gandmool must fire on March 20 2026"

    def test_panchak_june8_2026(self):
        result = _detect(date(2026, 6, 8))
        assert _has_yoga(result, "special_yogas", "Panchak"), \
            "Panchak must fire on June 8 2026"

    def test_jwalamukhi_jan27_2026(self):
        # Tithi 9 + Nakshatra 3 (Navami + Kritika)
        result = _detect(date(2026, 1, 27))
        assert _has_yoga(result, "special_yogas", "Jwalamukhi"), \
            "Jwalamukhi must fire on Jan 27 2026"

    def test_bhadra_fires_on_some_days(self):
        # Bhadra fires every ~7 days; June 18 was confirmed in prior tests
        result = _detect(date(2026, 6, 18))
        assert _has_yoga(result, "special_yogas", "Bhadra (Vishti)"), \
            "Bhadra must fire on June 18 2026"

    def test_special_yogas_is_a_list(self):
        result = _detect(date(2026, 6, 7))
        assert isinstance(result["special_yogas"], list)

    def test_no_gandmool_on_normal_day(self):
        # April 23 2026: Moon in Pushya (8) — not a Gandmool nakshatra
        result = _detect(date(2026, 4, 23))
        assert not _has_yoga(result, "special_yogas", "Gandmool Nakshatra"), \
            "Gandmool must NOT fire when Moon is in Pushya"
