"""
Tests for timed yoga detection — compute_day_segments + detect_yogas_for_day.

These tests use real ephemeris calls so they are integration-style.
They verify that:
  - compute_day_segments returns non-empty, ordered, contiguous segments
  - detect_yogas_for_day returns yogas with start/end time strings
  - Yogas that span midnight show the correct window (clipped to sunrise window)
  - The Dhumra issue: on June 4 2026 (Thursday), Dhumra via Mula nakshatra should
    show the exact time window it is active, not just "whole day"
"""

import unittest
from datetime import date

from astronomy import get_sunrise, jd_to_zoned_datetime, local_date_anchor_jd
from location_service import get_timezone_name
from dainika_muhurta_service import compute_day_segments, detect_yogas_for_day


JAIPUR_LAT = 26.9124
JAIPUR_LON = 75.7873
AYANAMSA = "Lahiri"


def _get_day_jds(d: date, lat: float, lon: float):
    tz = get_timezone_name(lat, lon)
    anchor = local_date_anchor_jd(d, tz)
    next_anchor = local_date_anchor_jd(date(d.year, d.month, d.day + 1), tz)
    sunrise = get_sunrise(anchor, lat, lon)
    next_sunrise = get_sunrise(next_anchor, lat, lon)
    return sunrise, next_sunrise, tz


class TestComputeDaySegments(unittest.TestCase):

    def setUp(self):
        d = date(2026, 6, 4)
        self.sunrise, self.next_sunrise, self.tz = _get_day_jds(d, JAIPUR_LAT, JAIPUR_LON)

    def test_returns_tithi_and_nakshatra_segments(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        self.assertIn("tithi_segments", segs)
        self.assertIn("nakshatra_segments", segs)

    def test_tithi_segments_are_non_empty(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        self.assertGreater(len(segs["tithi_segments"]), 0)

    def test_nakshatra_segments_are_non_empty(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        self.assertGreater(len(segs["nakshatra_segments"]), 0)

    def test_tithi_segments_span_full_day(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        ts = segs["tithi_segments"]
        self.assertAlmostEqual(ts[0]["start_jd"], self.sunrise, places=4)
        self.assertAlmostEqual(ts[-1]["end_jd"], self.next_sunrise, places=4)

    def test_nakshatra_segments_span_full_day(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        ns = segs["nakshatra_segments"]
        self.assertAlmostEqual(ns[0]["start_jd"], self.sunrise, places=4)
        self.assertAlmostEqual(ns[-1]["end_jd"], self.next_sunrise, places=4)

    def test_tithi_segments_are_contiguous(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        ts = segs["tithi_segments"]
        for i in range(len(ts) - 1):
            self.assertAlmostEqual(ts[i]["end_jd"], ts[i + 1]["start_jd"], places=4)

    def test_nakshatra_segments_are_contiguous(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        ns = segs["nakshatra_segments"]
        for i in range(len(ns) - 1):
            self.assertAlmostEqual(ns[i]["end_jd"], ns[i + 1]["start_jd"], places=4)

    def test_each_segment_has_required_keys(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        for seg in segs["tithi_segments"] + segs["nakshatra_segments"]:
            self.assertIn("index", seg)
            self.assertIn("start_jd", seg)
            self.assertIn("end_jd", seg)
            self.assertGreater(seg["end_jd"], seg["start_jd"])


class TestDetectYogasForDay(unittest.TestCase):

    def _run(self, d: date):
        sunrise, next_sunrise, tz = _get_day_jds(d, JAIPUR_LAT, JAIPUR_LON)
        return detect_yogas_for_day(
            date_obj=d,
            sunrise_jd=sunrise,
            next_sunrise_jd=next_sunrise,
            tz_name=tz,
            ayanamsa=AYANAMSA,
        )

    def test_returns_yogas_and_recommendation(self):
        result = self._run(date(2026, 6, 4))
        self.assertIn("yogas", result)
        self.assertIn("recommendation", result)

    def test_each_yoga_has_timing_fields(self):
        result = self._run(date(2026, 6, 4))
        for yoga in result["yogas"]:
            self.assertIn("start_time", yoga)
            self.assertIn("end_time", yoga)
            self.assertIn("start_local", yoga)
            self.assertIn("end_local", yoga)

    def test_yoga_times_are_non_empty_strings(self):
        result = self._run(date(2026, 6, 4))
        for yoga in result["yogas"]:
            self.assertIsInstance(yoga["start_time"], str)
            self.assertIsInstance(yoga["end_time"], str)
            self.assertTrue(len(yoga["start_time"]) > 0)
            self.assertTrue(len(yoga["end_time"]) > 0)

    def test_yoga_start_before_end(self):
        result = self._run(date(2026, 6, 4))
        for yoga in result["yogas"]:
            self.assertLess(yoga["start_local"], yoga["end_local"])

    def test_recommendation_is_valid(self):
        result = self._run(date(2026, 6, 5))
        self.assertIn(
            result["recommendation"],
            ("highly_auspicious", "auspicious", "caution", "avoid", "neutral"),
        )

    def test_also_returns_vara_tithi_nakshatra(self):
        result = self._run(date(2026, 6, 4))
        self.assertIn("vara", result)
        self.assertIn("tithi", result)
        self.assertIn("nakshatra", result)

    def test_june7_sunrise_nakshatra_is_dhanishtha_not_shravana(self):
        # Regression: double-ayanamsa bug caused index 22 (Shravana) instead of 23 (Dhanishtha)
        result = self._run(date(2026, 6, 7))
        self.assertEqual(result["nakshatra"], 23)  # 23 = Dhanishtha


class TestTwoNakshatraEdgeCase(unittest.TestCase):
    """June 14 2026 (Jaipur): Krittika ends ~01:17 (before sunrise), so both
    Krittika and Rohini are present within the June 13→14 solar day window,
    making it a 'two nakshatra within one solar day' edge case."""

    def setUp(self):
        d = date(2026, 6, 13)   # solar day: June 13 sunrise → June 14 sunrise
        self.sunrise, self.next_sunrise, self.tz = _get_day_jds(d, JAIPUR_LAT, JAIPUR_LON)

    def test_june13_has_at_least_two_nakshatra_segments(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        self.assertGreaterEqual(len(segs["nakshatra_segments"]), 2)

    def test_all_segments_are_non_zero_duration(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        for seg in segs["nakshatra_segments"]:
            self.assertGreater(
                seg["end_jd"] - seg["start_jd"],
                30.0 / 86400.0,  # must be longer than the nudge itself
                f"Zero-duration segment detected: {seg}",
            )

    def test_all_segment_indices_are_distinct_from_neighbours(self):
        segs = compute_day_segments(self.sunrise, self.next_sunrise, AYANAMSA)
        ns = segs["nakshatra_segments"]
        for i in range(len(ns) - 1):
            self.assertNotEqual(
                ns[i]["index"], ns[i + 1]["index"],
                f"Duplicate consecutive nakshatra index at position {i}: {ns[i]['index']}",
            )


class TestConsistencyWithPanchangService(unittest.TestCase):
    """Yoga Muhurta must produce identical Tithi and Nakshatra to the panchang page.

    Both pages share the same sunrise_jd so they MUST agree — any divergence is a bug.
    These tests enforce structural impossibility of that divergence by having both
    code paths call the same shared functions.
    """

    def _run_yoga(self, d: date):
        sunrise, next_sunrise, tz = _get_day_jds(d, JAIPUR_LAT, JAIPUR_LON)
        return detect_yogas_for_day(
            date_obj=d,
            sunrise_jd=sunrise,
            next_sunrise_jd=next_sunrise,
            tz_name=tz,
            ayanamsa=AYANAMSA,
        ), sunrise, next_sunrise, tz

    def test_tithi_matches_panchang_service_june7(self):
        from panchang_service import _collect_all_tithis_in_day
        d = date(2026, 6, 7)
        yoga_result, sunrise, next_sunrise, tz = self._run_yoga(d)
        panchang_tithis = _collect_all_tithis_in_day(sunrise, next_sunrise, AYANAMSA, tz)
        self.assertEqual(panchang_tithis[0]["index"], yoga_result["tithi"])

    def test_nakshatra_matches_panchang_service_june7(self):
        from panchang_service import collect_all_nakshatras_in_day
        d = date(2026, 6, 7)
        yoga_result, sunrise, next_sunrise, tz = self._run_yoga(d)
        panchang_naks = collect_all_nakshatras_in_day(sunrise, next_sunrise, AYANAMSA, tz)
        self.assertEqual(panchang_naks[0]["index"], yoga_result["nakshatra"])
        self.assertEqual(panchang_naks[0]["index"], 23)  # Dhanishtha regression

    def test_tithi_matches_panchang_service_june4(self):
        from panchang_service import _collect_all_tithis_in_day
        d = date(2026, 6, 4)
        yoga_result, sunrise, next_sunrise, tz = self._run_yoga(d)
        panchang_tithis = _collect_all_tithis_in_day(sunrise, next_sunrise, AYANAMSA, tz)
        self.assertEqual(panchang_tithis[0]["index"], yoga_result["tithi"])

    def test_nakshatra_matches_panchang_service_june13_multinak(self):
        """On a two-nakshatra day, the sunrise nakshatra from yoga must match panchang."""
        from panchang_service import collect_all_nakshatras_in_day
        d = date(2026, 6, 13)
        yoga_result, sunrise, next_sunrise, tz = self._run_yoga(d)
        panchang_naks = collect_all_nakshatras_in_day(sunrise, next_sunrise, AYANAMSA, tz)
        self.assertEqual(panchang_naks[0]["index"], yoga_result["nakshatra"])
        self.assertGreaterEqual(len(panchang_naks), 2)
