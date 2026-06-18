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
        valid = {"highly_auspicious", "auspicious", "caution", "avoid", "neutral", "mixed"}
        result = _detect(date(2026, 6, 7))
        assert result["recommendation"] in valid
        assert result["aanandadi_recommendation"] in valid

    def test_aanandadi_returns_at_least_one_match(self):
        # One yoga per Moon nakshatra window — at least 1, usually 1–2 per day
        result = _detect(date(2026, 6, 7))
        assert len(result["aanandadi_yogas"]) >= 1

    def test_dainika_yoga_has_required_fields(self):
        result = _detect(date(2026, 6, 18))
        yogas = result["yogas"]
        assert len(yogas) > 0
        for y in yogas:
            for field in ("name", "nature", "severity", "severe", "meaning",
                          "trigger_kind", "trigger_detail", "start_time", "end_time",
                          "start_local", "end_local", "start_jd", "end_jd",
                          "is_nullified", "nullified_by"):
                assert field in y, f"Dainika yoga missing field '{field}'"

    def test_aanandadi_yoga_has_required_fields(self):
        result = _detect(date(2026, 6, 7))
        for y in result["aanandadi_yogas"]:
            for field in ("name", "nature", "severity", "fal", "meaning", "severe",
                          "yoga_index", "trigger_nakshatra_index",
                          "start_time", "end_time", "start_local", "end_local",
                          "varjya_minutes", "is_nullified", "nullified_by"):
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

    def test_no_dwipushkar_june21_2026(self):
        # June 21 Moon is in Uttara Phalguni (12) which is a Tripushkar nakshatra,
        # not a Dwipushkar nakshatra (Mrigashira/Chitra/Dhanishtha only)
        result = _detect(date(2026, 6, 21))
        assert not _has_yoga(result, "yogas", "Dwipushkar"), \
            "Dwipushkar must NOT fire on June 21 2026 (nak 12 is Tripushkar, not Dwipushkar)"

    def test_dwipushkar_march25_2026(self):
        # Wednesday (vara=3) + Mrigashira (nak=5) + Tithi 7 → Dwipushkar
        result = _detect(date(2026, 3, 25))
        assert _has_yoga(result, "yogas", "Dwipushkar"), \
            "Dwipushkar must fire on March 25 2026 (Wednesday + Mrigashira + Tithi 7)"

    def test_tripushkar_and_dwipushkar_never_fire_same_day(self):
        # Sanity check: their nakshatra sets are mutually exclusive, so they can never coexist
        result = _detect(date(2026, 6, 21))
        has_trip = _has_yoga(result, "yogas", "Tripushkar")
        has_dwi = _has_yoga(result, "yogas", "Dwipushkar")
        assert not (has_trip and has_dwi), \
            "Tripushkar and Dwipushkar cannot both fire on the same day"

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
    def test_june7_sunday_dhanishtha_gives_matanga(self):
        # June 7 2026 is Sunday (vara=0). Moon in Dhanishtha (std=23, 28-nak=24).
        # Y = (24 − 0) % 28 = 24 → Matanga
        result = _detect(date(2026, 6, 7))
        yogas = result["aanandadi_yogas"]
        assert any(y["trigger_nakshatra_index"] == 23 for y in yogas), \
            "Moon should be in Dhanishtha (23) on June 7"
        matanga = next((y for y in yogas if y["name"] == "Matanga"), None)
        assert matanga is not None, f"Expected Matanga on Sunday+Dhanishtha, got {[y['name'] for y in yogas]}"
        assert matanga["yoga_index"] == 24

    def test_june18_thursday_pushya_gives_shubha(self):
        # Thursday (vara=4) + Pushya (8): Y=(8-16)%28=20 → Shubha
        result = _detect(date(2026, 6, 18))
        yogas = result["aanandadi_yogas"]
        assert any(y["trigger_nakshatra_index"] == 8 for y in yogas), \
            "Moon should transit Pushya (8) on June 18"
        shubha = next((y for y in yogas if y["name"] == "Shubha"), None)
        assert shubha is not None, f"Expected Shubha (Thursday+Pushya), got {[y['name'] for y in yogas]}"

    def test_june18_thursday_ashlesha_gives_amrut(self):
        # Thursday (vara=4) + Ashlesha (9): Y=(9-16)%28=21 → Amrut
        result = _detect(date(2026, 6, 18))
        amrut = next((y for y in result["aanandadi_yogas"] if y["name"] == "Amrut"), None)
        assert amrut is not None, "Amrut expected when Moon enters Ashlesha on Thursday"
        assert amrut["yoga_index"] == 21

    def test_june18_returns_two_aanandadi_yogas(self):
        # Moon transitions Pushya→Ashlesha on June 18 → two yogas
        result = _detect(date(2026, 6, 18))
        assert len(result["aanandadi_yogas"]) == 2, \
            f"Expected 2 Aanandadi yogas on June 18 (Moon transits Pushya then Ashlesha), " \
            f"got {len(result['aanandadi_yogas'])}"

    def test_aanandadi_yoga_names_are_valid(self):
        from yoga_rules import AANANDADI_YOGAS
        valid_names = {y["name"] for y in AANANDADI_YOGAS}
        result = _detect(date(2026, 6, 7))
        for y in result["aanandadi_yogas"]:
            assert y["name"] in valid_names, f"Invalid Aanandadi yoga name: {y['name']}"

    def test_yoga_index_in_range(self):
        result = _detect(date(2026, 6, 7))
        for y in result["aanandadi_yogas"]:
            assert 1 <= y["yoga_index"] <= 28, f"yoga_index {y['yoga_index']} out of 1–28"

    def test_aanandadi_severe_yoga_implies_avoid_or_mixed_recommendation(self):
        # Tuesday (vara=2) + Moon in Mrigashira (std=5): Y=(5-8)%28=25 → Rakshasa (severe)
        # Around June 16, 2026.
        from yoga_rules import AANANDADI_YOGAS
        severe_names = {y["name"] for y in AANANDADI_YOGAS if y["severe"]}
        result = _detect(date(2026, 6, 16))
        severe_matches = [y for y in result["aanandadi_yogas"] if y["name"] in severe_names]
        if not severe_matches:
            pytest.skip("No severe Aanandadi yoga on June 16 — Moon may not be in Mrigashira")
        assert result["aanandadi_recommendation"] in {"avoid", "mixed"}, \
            f"Severe Aanandadi yoga present but recommendation is '{result['aanandadi_recommendation']}'"

    def test_aanandadi_varjya_end_after_start(self):
        # Try several dates until we find one with a tuple varjya (non-severe ashubh yoga)
        for d in (date(2026, 6, d) for d in range(7, 22)):
            result = _detect(d)
            for y in result["aanandadi_yogas"]:
                if y["varjya_minutes"] is not None and y["varjya_minutes"] != "full_day":
                    assert y.get("varjya_start_jd") is not None
                    assert y.get("varjya_end_jd") is not None
                    assert y["varjya_end_jd"] > y["varjya_start_jd"], \
                        f"varjya end must be after start for '{y['name']}'"
                    return  # found and tested — done
        pytest.skip("No non-severe ashubh Aanandadi yoga found in Jun 7–21")


# ---------------------------------------------------------------------------
# Known-date regression: Special yogas
# ---------------------------------------------------------------------------

class TestKnownSpecialDates:
    def test_gandmool_march20_2026(self):
        result = _detect(date(2026, 3, 20))
        assert _has_yoga(result, "special_yogas", "Gandmool Nakshatra"), \
            "Gandmool must fire on March 20 2026"

    def test_gandmool_march20_is_split_per_nakshatra(self):
        # March 20: Moon passes through Revati (27) then Ashvini (1) — both Gandmool.
        # The Gandanta transition between them is the rashi junction Cancer→Leo.
        # Each nakshatra must produce its own separate entry, never merged.
        result = _detect(date(2026, 3, 20))
        gandmool_entries = [y for y in result["special_yogas"] if y["name"] == "Gandmool Nakshatra"]
        assert len(gandmool_entries) == 2, (
            f"Expected 2 separate Gandmool entries (Revati + Ashvini) on March 20, "
            f"got {len(gandmool_entries)}"
        )
        # Each entry must cover only one nakshatra
        for entry in gandmool_entries:
            naks_in_entry = entry["trigger_detail"]
            assert "Revati" in naks_in_entry or "Ashvini" in naks_in_entry, \
                f"Unexpected trigger_detail: {naks_in_entry}"
        # They must not both mention the same nakshatra
        detail_set = {e["trigger_detail"] for e in gandmool_entries}
        assert len(detail_set) == 2, "Each Gandmool entry must describe a different nakshatra"

    def test_aanandadi_ashubh_nullified_by_supreme_yoga(self):
        # Any inauspicious Aanandadi yoga that overlaps in time with a supreme Dainika yoga
        # (Guru Pushya, Ravi Pushya, Sarvartha Siddhi, Amrit Siddhi) must be nullified.
        # June 18 has Guru Pushya Amrit active → check that nullification is applied.
        result = _detect(date(2026, 6, 18))
        supreme_dainika = {y["name"] for y in result["yogas"]
                           if y["name"] in {"Guru Pushya Amrit", "Ravi Pushya Amrit",
                                            "Sarvartha Siddhi", "Amrit Siddhi"}
                           and not y.get("cancelled", False)}
        if not supreme_dainika:
            pytest.skip("No supreme Dainika yoga active on this date")
        ashubh_aanandadi = [y for y in result["aanandadi_yogas"] if y["nature"] == "ashubh"]
        if not ashubh_aanandadi:
            pytest.skip("No inauspicious Aanandadi yoga on this date")
        # At least one must be nullified if time overlap exists
        nullified = [y for y in ashubh_aanandadi if y.get("is_nullified")]
        non_nullified = [y for y in ashubh_aanandadi if not y.get("is_nullified")]
        # All non-nullified ashubh yogas must have no time overlap with any supreme yoga
        supreme_windows = [(y["start_jd"], y["end_jd"]) for y in result["yogas"]
                           if y["name"] in supreme_dainika]
        for yoga in non_nullified:
            for sw_start, sw_end in supreme_windows:
                overlaps = yoga["start_jd"] < sw_end and sw_start < yoga["end_jd"]
                assert not overlaps, (
                    f"Ashubh yoga '{yoga['name']}' overlaps supreme yoga window "
                    f"but is not nullified (is_nullified={yoga.get('is_nullified')})"
                )

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


# ---------------------------------------------------------------------------
# Dainika Dosha Bhanga (cancellation hierarchy)
# ---------------------------------------------------------------------------

class TestDaiknikaDosha_Bhanga:
    def test_dainika_yoga_has_is_nullified_field(self):
        result = _detect(date(2026, 6, 18))
        for y in result["yogas"]:
            assert "is_nullified" in y, f"Dainika yoga '{y['name']}' missing is_nullified"
            assert "nullified_by" in y, f"Dainika yoga '{y['name']}' missing nullified_by"

    def test_dainika_ashubh_not_nullified_without_supreme(self):
        # June 7 is Sunday — no Guru/Ravi Pushya Amrit fires; any ashubh yogas should not be nullified
        result = _detect(date(2026, 6, 7))
        for y in result["yogas"]:
            if y["nature"] == "ashubh" and not y.get("cancelled"):
                assert y["is_nullified"] is False, \
                    f"'{y['name']}' should not be nullified when no supreme yoga is active"

    def test_dainika_ashubh_nullified_when_supreme_overlaps_june18(self):
        # June 18: Guru Pushya Amrit + Amrit Siddhi + Sarvartha Siddhi are active (05:23–11:32).
        # Any inauspicious Dainika yoga whose window overlaps that range must have is_nullified=True.
        result = _detect(date(2026, 6, 18))
        _SUPREME = {"Guru Pushya Amrit", "Ravi Pushya Amrit", "Sarvartha Siddhi", "Amrit Siddhi"}
        supreme = {y["name"]: (y["start_jd"], y["end_jd"])
                   for y in result["yogas"]
                   if y["name"] in _SUPREME and not y.get("cancelled")}
        if not supreme:
            pytest.skip("No supreme yoga found on June 18 — check ephemeris")
        for y in result["yogas"]:
            if y["nature"] != "ashubh" or y.get("cancelled"):
                continue
            overlaps_supreme = any(
                y["start_jd"] < end_jd and start_jd < y["end_jd"]
                for start_jd, end_jd in supreme.values()
            )
            if overlaps_supreme:
                assert y["is_nullified"] is True, (
                    f"'{y['name']}' overlaps a supreme Dainika yoga window "
                    f"but is_nullified={y.get('is_nullified')}"
                )
                assert y["nullified_by"] in supreme, \
                    f"nullified_by='{y['nullified_by']}' is not a known supreme yoga"
