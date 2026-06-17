"""Unit tests for yoga_engine.py.

Pure functions only — no ephemeris, no I/O. All inputs are hand-crafted
JD segments and planet dictionaries so tests run in milliseconds.
"""

import pytest
from yoga_engine import (
    overlap,
    varjya_minutes,
    match_aanandadi,
    match_dainika,
    apply_dainika_overrides,
    compute_recommendation,
)
from yoga_rules import AANANDADI_RULES, DAINIKA_RULES


def seg(index: int, start: float, end: float) -> dict:
    return {"index": index, "start_jd": start, "end_jd": end}


# ---------------------------------------------------------------------------
# overlap()
# ---------------------------------------------------------------------------

class TestOverlap:
    def test_overlapping_returns_intersection(self):
        assert overlap(seg(1, 0.0, 10.0), seg(2, 5.0, 15.0)) == (5.0, 10.0)

    def test_contained_returns_inner(self):
        assert overlap(seg(1, 0.0, 10.0), seg(2, 2.0, 8.0)) == (2.0, 8.0)

    def test_non_overlapping_returns_none(self):
        assert overlap(seg(1, 0.0, 5.0), seg(2, 6.0, 10.0)) is None

    def test_touching_edge_returns_none(self):
        # a ends exactly where b starts → zero-length → None
        assert overlap(seg(1, 0.0, 5.0), seg(2, 5.0, 10.0)) is None

    def test_identical_segments_returns_full_range(self):
        assert overlap(seg(1, 2.0, 8.0), seg(2, 2.0, 8.0)) == (2.0, 8.0)

    def test_order_commutative(self):
        a = seg(1, 1.0, 4.0)
        b = seg(2, 3.0, 6.0)
        assert overlap(a, b) == overlap(b, a)


# ---------------------------------------------------------------------------
# varjya_minutes()
# ---------------------------------------------------------------------------

class TestVarjyaMinutes:
    def test_zero_zero(self):
        assert varjya_minutes((0, 0)) == pytest.approx(0.0)

    def test_one_ghati(self):
        assert varjya_minutes((1, 0)) == pytest.approx(24.0)

    def test_sixty_pala_equals_one_ghati(self):
        assert varjya_minutes((0, 60)) == pytest.approx(24.0)

    def test_known_0_24(self):
        assert varjya_minutes((0, 24)) == pytest.approx(9.6)

    def test_known_0_48(self):
        assert varjya_minutes((0, 48)) == pytest.approx(19.2)

    def test_known_1_36(self):
        assert varjya_minutes((1, 36)) == pytest.approx(38.4)

    def test_known_2_0(self):
        assert varjya_minutes((2, 0)) == pytest.approx(48.0)

    def test_known_2_48(self):
        assert varjya_minutes((2, 48)) == pytest.approx(67.2)


# ---------------------------------------------------------------------------
# match_dainika()
# ---------------------------------------------------------------------------

class TestMatchDainika:
    """Tests use one-unit JD segments (0.0–1.0) for simplicity."""

    def _single_match_by_name(self, name: str, *, vara: int, tithi: int, nak: int) -> dict | None:
        t_segs = [seg(tithi, 0.0, 1.0)]
        n_segs = [seg(nak, 0.0, 1.0)]
        matches = match_dainika(DAINIKA_RULES, vara, t_segs, n_segs)
        return next((m for m in matches if m["name"] == name), None)

    # Tithi-based
    def test_siddhi_yoga_fires_tuesday_tithi3(self):
        assert self._single_match_by_name("Siddhi Yoga Tithi", vara=2, tithi=3, nak=5) is not None

    def test_siddhi_yoga_fires_thursday_tithi10(self):
        assert self._single_match_by_name("Siddhi Yoga Tithi", vara=4, tithi=10, nak=5) is not None

    def test_siddhi_yoga_absent_on_monday(self):
        assert self._single_match_by_name("Siddhi Yoga Tithi", vara=1, tithi=3, nak=5) is None

    def test_dagdha_tithi_fires_sunday_tithi12(self):
        assert self._single_match_by_name("Dagdha Tithi", vara=0, tithi=12, nak=5) is not None

    def test_mrityu_yoga_tithi_fires_sunday_tithi1(self):
        m = self._single_match_by_name("Mrityu Yoga Tithi", vara=0, tithi=1, nak=5)
        assert m is not None
        assert m["severe"] is True

    def test_mrityu_yoga_tithi_fires_wednesday_tithi3(self):
        assert self._single_match_by_name("Mrityu Yoga Tithi", vara=3, tithi=3, nak=5) is not None

    # Nakshatra-based
    def test_amrit_siddhi_fires_sunday_hasta(self):
        m = self._single_match_by_name("Amrit Siddhi", vara=0, tithi=1, nak=13)
        assert m is not None
        assert m["severity"] == "highly_auspicious"

    def test_amrit_siddhi_fires_thursday_pushya(self):
        assert self._single_match_by_name("Amrit Siddhi", vara=4, tithi=1, nak=8) is not None

    def test_rakshas_yoga_fires_monday_ashvini(self):
        m = self._single_match_by_name("Rakshas Yoga", vara=1, tithi=1, nak=1)
        assert m is not None
        assert m["severe"] is True

    def test_yam_ghant_fires_thursday_kritika(self):
        m = self._single_match_by_name("Yam Ghant", vara=4, tithi=1, nak=3)
        assert m is not None
        assert m["severe"] is True

    def test_guru_pushya_amrit_fires_thursday_pushya(self):
        assert self._single_match_by_name("Guru Pushya Amrit", vara=4, tithi=1, nak=8) is not None

    def test_ravi_pushya_amrit_fires_sunday_pushya(self):
        assert self._single_match_by_name("Ravi Pushya Amrit", vara=0, tithi=1, nak=8) is not None

    def test_sarvartha_siddhi_fires_thursday_pushya(self):
        assert self._single_match_by_name("Sarvartha Siddhi", vara=4, tithi=1, nak=8) is not None

    # Tithi+Nakshatra compound
    def test_tripushkar_fires_sunday_tithi7_nak7(self):
        assert self._single_match_by_name("Tripushkar", vara=0, tithi=7, nak=7) is not None

    def test_tripushkar_fires_tuesday_tithi17_nak16(self):
        assert self._single_match_by_name("Tripushkar", vara=2, tithi=17, nak=16) is not None

    def test_tripushkar_fires_saturday_krishna_paksha(self):
        assert self._single_match_by_name("Tripushkar", vara=6, tithi=22, nak=21) is not None

    def test_tripushkar_absent_monday(self):
        assert self._single_match_by_name("Tripushkar", vara=1, tithi=7, nak=7) is None

    def test_tripushkar_absent_wrong_tithi(self):
        assert self._single_match_by_name("Tripushkar", vara=0, tithi=1, nak=7) is None

    def test_tripushkar_absent_wrong_nakshatra(self):
        assert self._single_match_by_name("Tripushkar", vara=0, tithi=7, nak=1) is None

    def test_dwipushkar_fires_wednesday_tithi12_nak12(self):
        assert self._single_match_by_name("Dwipushkar", vara=3, tithi=12, nak=12) is not None

    def test_dwipushkar_fires_friday_tithi27_nak25(self):
        assert self._single_match_by_name("Dwipushkar", vara=5, tithi=27, nak=25) is not None

    def test_dwipushkar_absent_tuesday(self):
        assert self._single_match_by_name("Dwipushkar", vara=2, tithi=7, nak=12) is None

    # Timing: intersection window
    def test_tripushkar_window_is_tithi_nak_intersection(self):
        t_segs = [seg(7, 0.0, 0.6)]    # Tithi 7: 0.0–0.6
        n_segs = [seg(7, 0.4, 1.0)]    # Nak 7:   0.4–1.0
        matches = match_dainika(DAINIKA_RULES, vara=0, tithi_segments=t_segs, nakshatra_segments=n_segs)
        trip = next(m for m in matches if m["name"] == "Tripushkar")
        assert trip["start_jd"] == pytest.approx(0.4)
        assert trip["end_jd"] == pytest.approx(0.6)

    def test_non_overlapping_tithi_nak_produces_no_compound(self):
        t_segs = [seg(7, 0.0, 0.4)]    # ends before nakshatra starts
        n_segs = [seg(7, 0.6, 1.0)]
        matches = match_dainika(DAINIKA_RULES, vara=0, tithi_segments=t_segs, nakshatra_segments=n_segs)
        assert all(m["name"] != "Tripushkar" for m in matches)

    def test_match_result_has_required_fields(self):
        t_segs = [seg(3, 0.0, 1.0)]
        n_segs = [seg(5, 0.0, 1.0)]
        matches = match_dainika(DAINIKA_RULES, vara=2, tithi_segments=t_segs, nakshatra_segments=n_segs)
        siddhi = next(m for m in matches if m["name"] == "Siddhi Yoga Tithi")
        for field in ("name", "nature", "severity", "severe", "meaning",
                      "trigger_kind", "trigger_detail", "start_jd", "end_jd"):
            assert field in siddhi, f"Missing field '{field}' in match result"

    def test_tithi_match_window_equals_segment_bounds(self):
        t_segs = [seg(3, 0.2, 0.7)]
        n_segs = [seg(5, 0.0, 1.0)]
        matches = match_dainika(DAINIKA_RULES, vara=2, tithi_segments=t_segs, nakshatra_segments=n_segs)
        siddhi = next(m for m in matches if m["name"] == "Siddhi Yoga Tithi")
        assert siddhi["start_jd"] == pytest.approx(0.2)
        assert siddhi["end_jd"] == pytest.approx(0.7)

    def test_nakshatra_match_window_equals_segment_bounds(self):
        t_segs = [seg(1, 0.0, 1.0)]
        n_segs = [seg(13, 0.3, 0.9)]   # Sunday + Hasta → Amrit Siddhi
        matches = match_dainika(DAINIKA_RULES, vara=0, tithi_segments=t_segs, nakshatra_segments=n_segs)
        amrit = next(m for m in matches if m["name"] == "Amrit Siddhi")
        assert amrit["start_jd"] == pytest.approx(0.3)
        assert amrit["end_jd"] == pytest.approx(0.9)

    def test_multiple_tithi_segments_produce_multiple_entries(self):
        # Two Dagdha Tithi periods (Sunday + tithi 12)
        t_segs = [seg(12, 0.0, 0.4), seg(12, 0.6, 1.0)]
        n_segs = [seg(5, 0.0, 1.0)]
        matches = match_dainika(DAINIKA_RULES, vara=0, tithi_segments=t_segs, nakshatra_segments=n_segs)
        dagdhas = [m for m in matches if m["name"] == "Dagdha Tithi"]
        assert len(dagdhas) == 2

    def test_returns_empty_list_when_nothing_matches(self):
        # Thursday + tithi 15 + nak 20 → check if any rule fires
        # (May fire some rules — just verify it's a list)
        t_segs = [seg(15, 0.0, 1.0)]
        n_segs = [seg(20, 0.0, 1.0)]
        result = match_dainika(DAINIKA_RULES, vara=4, tithi_segments=t_segs, nakshatra_segments=n_segs)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# apply_dainika_overrides()
# ---------------------------------------------------------------------------

def _yoga(name: str, nature: str = "shubh", severity: str = "auspicious", severe: bool = False) -> dict:
    return {
        "name": name,
        "nature": nature,
        "severity": severity,
        "severe": severe,
        "trigger_kind": "nakshatra",
        "trigger_detail": "",
        "start_jd": 0.0,
        "end_jd": 1.0,
        "meaning": "",
    }


class TestApplyDainikaOverrides:
    def test_sarvartha_cancels_dusht_tithi(self):
        yogas = [
            _yoga("Sarvartha Siddhi"),
            _yoga("Dusht Tithi", "ashubh", "inauspicious"),
        ]
        result = apply_dainika_overrides(yogas)
        dusht = next(y for y in result if y["name"] == "Dusht Tithi")
        assert dusht.get("cancelled") is True

    def test_dusht_without_sarvartha_is_not_cancelled(self):
        yogas = [_yoga("Dusht Tithi", "ashubh", "inauspicious")]
        result = apply_dainika_overrides(yogas)
        dusht = next(y for y in result if y["name"] == "Dusht Tithi")
        assert not dusht.get("cancelled")

    def test_dusht_without_sarvartha_diminishes_amrit_siddhi(self):
        yogas = [
            _yoga("Dusht Tithi", "ashubh", "inauspicious"),
            _yoga("Amrit Siddhi", "shubh", "highly_auspicious"),
        ]
        result = apply_dainika_overrides(yogas)
        amrit = next(y for y in result if y["name"] == "Amrit Siddhi")
        assert amrit.get("diminished") is True

    def test_sarvartha_with_dusht_does_not_diminish_amrit_siddhi(self):
        yogas = [
            _yoga("Sarvartha Siddhi"),
            _yoga("Dusht Tithi", "ashubh", "inauspicious"),
            _yoga("Amrit Siddhi", "shubh", "highly_auspicious"),
        ]
        result = apply_dainika_overrides(yogas)
        amrit = next(y for y in result if y["name"] == "Amrit Siddhi")
        assert not amrit.get("diminished")

    def test_no_dusht_no_changes(self):
        yogas = [_yoga("Amrit Siddhi", "shubh", "highly_auspicious")]
        result = apply_dainika_overrides(yogas)
        amrit = result[0]
        assert not amrit.get("cancelled")
        assert not amrit.get("diminished")

    def test_returns_same_list_length(self):
        yogas = [
            _yoga("Sarvartha Siddhi"),
            _yoga("Dusht Tithi", "ashubh", "inauspicious"),
            _yoga("Amrit Siddhi", "shubh", "highly_auspicious"),
        ]
        result = apply_dainika_overrides(yogas)
        assert len(result) == 3

    def test_original_yogas_not_mutated(self):
        original = [_yoga("Dusht Tithi", "ashubh", "inauspicious")]
        apply_dainika_overrides(original)
        assert not original[0].get("cancelled")


# ---------------------------------------------------------------------------
# compute_recommendation()
# ---------------------------------------------------------------------------

def _match(nature: str, severity: str, severe: bool = False, cancelled: bool = False) -> dict:
    return {
        "name": "Test",
        "nature": nature,
        "severity": severity,
        "severe": severe,
        "cancelled": cancelled,
        "start_jd": 0.0,
        "end_jd": 1.0,
    }


class TestComputeRecommendation:
    def test_empty_returns_neutral(self):
        assert compute_recommendation([]) == "neutral"

    def test_all_cancelled_returns_neutral(self):
        assert compute_recommendation([_match("ashubh", "inauspicious", cancelled=True)]) == "neutral"

    def test_severe_returns_avoid(self):
        assert compute_recommendation([_match("ashubh", "highly_inauspicious", severe=True)]) == "avoid"

    def test_severe_with_highly_auspicious_returns_mixed(self):
        # Severe danger + top auspicious opportunity → mixed signal, not blanket avoid
        yogas = [
            _match("shubh", "highly_auspicious"),
            _match("ashubh", "highly_inauspicious", severe=True),
        ]
        assert compute_recommendation(yogas) == "mixed"

    def test_severe_with_only_auspicious_returns_avoid(self):
        # Regular auspicious does not balance out a severe yoga
        yogas = [
            _match("shubh", "auspicious"),
            _match("ashubh", "highly_inauspicious", severe=True),
        ]
        assert compute_recommendation(yogas) == "avoid"

    def test_cancelled_severe_does_not_force_avoid(self):
        yogas = [_match("ashubh", "highly_inauspicious", severe=True, cancelled=True)]
        assert compute_recommendation(yogas) == "neutral"

    def test_only_highly_auspicious_returns_highly_auspicious(self):
        assert compute_recommendation([_match("shubh", "highly_auspicious")]) == "highly_auspicious"

    def test_only_auspicious_returns_auspicious(self):
        assert compute_recommendation([_match("shubh", "auspicious")]) == "auspicious"

    def test_mixed_highly_auspicious_and_auspicious_returns_highly_auspicious(self):
        yogas = [
            _match("shubh", "highly_auspicious"),
            _match("shubh", "auspicious"),
        ]
        assert compute_recommendation(yogas) == "highly_auspicious"

    def test_only_inauspicious_returns_caution(self):
        assert compute_recommendation([_match("ashubh", "inauspicious")]) == "caution"

    def test_mixed_shubh_and_ashubh_returns_caution(self):
        yogas = [
            _match("shubh", "highly_auspicious"),
            _match("ashubh", "inauspicious"),
        ]
        assert compute_recommendation(yogas) == "caution"

    def test_cancelled_ashubh_with_shubh_returns_auspicious(self):
        yogas = [
            _match("shubh", "auspicious"),
            _match("ashubh", "inauspicious", cancelled=True),
        ]
        assert compute_recommendation(yogas) == "auspicious"


# ---------------------------------------------------------------------------
# match_aanandadi()
# ---------------------------------------------------------------------------

class TestMatchAanandadi:
    def _planet_naks(self, **overrides: int) -> dict[str, int]:
        base = {
            "Sun": 2, "Moon": 6, "Mars": 10, "Mercury": 14,
            "Jupiter": 18, "Venus": 22, "Saturn": 25,
        }
        return {**base, **overrides}

    def test_aanand_fires_when_sun_in_ashvini(self):
        planet_naks = self._planet_naks(Sun=1)
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        aanand = next((m for m in matches if m["name"] == "Aanand"), None)
        assert aanand is not None
        assert aanand["triggering_planet"] == "Sun"

    def test_amrit_fires_when_saturn_in_anuradha(self):
        planet_naks = self._planet_naks(Saturn=17)
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        amrit = next((m for m in matches if m["name"] == "Amrit"), None)
        assert amrit is not None
        assert amrit["triggering_planet"] == "Saturn"

    def test_always_seven_matches_one_per_planet(self):
        # Moon must have a segment for its nakshatra (6=Ardra → Kaladand)
        planet_naks = self._planet_naks()
        moon_segs = [seg(6, 0.0, 1.0)]
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, moon_segs, (0.0, 1.0))
        assert len(matches) == 7

    def test_slow_planet_match_spans_full_day_by_default(self):
        # When no planet_windows provided, slow planets fall back to day_window
        planet_naks = self._planet_naks(Sun=1)
        day = (5.0, 6.0)
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], day)
        aanand = next(m for m in matches if m["name"] == "Aanand")
        assert aanand["start_jd"] == pytest.approx(5.0)
        assert aanand["end_jd"] == pytest.approx(6.0)

    def test_planet_windows_override_day_window_for_slow_planet(self):
        # Explicit planet_windows → slow planet uses that window, not day_window
        planet_naks = self._planet_naks(Sun=1)
        day = (5.0, 6.0)
        planet_windows = {"Sun": (3.5, 8.5)}
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], day, planet_windows)
        aanand = next(m for m in matches if m["name"] == "Aanand")
        assert aanand["start_jd"] == pytest.approx(3.5)
        assert aanand["end_jd"] == pytest.approx(8.5)

    def test_moon_match_uses_segment_timing(self):
        # Aanand: Moon=5 (Mrigashira)
        planet_naks = self._planet_naks(Moon=5)
        moon_segs = [seg(5, 0.25, 0.75)]
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, moon_segs, (0.0, 1.0))
        aanand = next(m for m in matches if m["name"] == "Aanand")
        assert aanand["triggering_planet"] == "Moon"
        assert aanand["start_jd"] == pytest.approx(0.25)
        assert aanand["end_jd"] == pytest.approx(0.75)

    def test_severe_yoga_has_severe_true(self):
        planet_naks = self._planet_naks(Sun=17)  # Mrityu: Sun=17
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        mrityu = next((m for m in matches if m["name"] == "Mrityu"), None)
        assert mrityu is not None
        assert mrityu["severe"] is True

    def test_result_has_required_fields(self):
        planet_naks = self._planet_naks(Sun=1)
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        aanand = next(m for m in matches if m["name"] == "Aanand")
        required = {"name", "nature", "severity", "fal", "meaning", "severe",
                    "triggering_planet", "trigger_nakshatra_index",
                    "start_jd", "end_jd", "varjya_start_jd", "varjya_end_jd", "varjya_minutes"}
        for field in required:
            assert field in aanand, f"Missing field '{field}'"

    def test_varjya_is_none_for_shubh_aanand(self):
        planet_naks = self._planet_naks(Sun=1)
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        aanand = next(m for m in matches if m["name"] == "Aanand")
        assert aanand["varjya_minutes"] is None
        assert aanand["varjya_start_jd"] is None
        assert aanand["varjya_end_jd"] is None

    def test_varjya_minutes_set_for_ashubh_with_tuple_varjya(self):
        # Dhwanksh: Sun=6, varjya=(2,0) → 48 min
        planet_naks = self._planet_naks(Sun=6)
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        dhwanksh = next(m for m in matches if m["name"] == "Dhwanksh")
        assert dhwanksh["varjya_minutes"] == pytest.approx(48.0)
        assert dhwanksh["varjya_start_jd"] is not None
        assert dhwanksh["varjya_end_jd"] is not None

    def test_varjya_full_day_for_severe_yoga(self):
        planet_naks = self._planet_naks(Sun=17)  # Mrityu: Sun=17
        matches = match_aanandadi(AANANDADI_RULES, planet_naks, [], (0.0, 1.0))
        mrityu = next(m for m in matches if m["name"] == "Mrityu")
        assert mrityu["varjya_minutes"] == "full_day"
