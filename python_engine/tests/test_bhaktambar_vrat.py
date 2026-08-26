import unittest
from datetime import date, timedelta
from typing import Dict, Any, List

from jain_observances.vrats.bhaktambar import (
    calculate_bhaktambar_vrat,
    VratSchedule,
)


class MockTithiProvider:
    """Mock provider for unit testing astronomical edge cases."""
    def __init__(self, daily_tithis: Dict[date, int]):
        self.daily_tithis = daily_tithis

    def get_sunrise(self, d: date, lat: float, lon: float):
        from datetime import datetime
        return datetime(d.year, d.month, d.day, 6, 0)

    def get_tithi_at_time(self, dt, lat: float, lon: float) -> int:
        d = dt.date()
        return self.daily_tithis.get(d, 1)


class BhaktambarVratAlgorithmTest(unittest.TestCase):
    def test_standard_shukla_span_7_days(self):
        """Standard Shukla Paksha: Tithis 8 to 14 consecutive without Kshaya/Vriddhi -> exactly 7 days."""
        start = date(2026, 4, 20)
        daily_tithis = {start + timedelta(days=i): 8 + i for i in range(7)}
        # Add boundary padding (7 and 15)
        daily_tithis[start - timedelta(days=1)] = 7
        daily_tithis[start + timedelta(days=7)] = 15

        provider = MockTithiProvider(daily_tithis)
        vrat = calculate_bhaktambar_vrat(2026, 4, "SHUKLA", 28.6139, 77.2090, provider)

        self.assertIsNotNone(vrat)
        self.assertEqual(vrat.start_date, "2026-04-20")
        self.assertEqual(vrat.end_date, "2026-04-26")
        self.assertEqual(vrat.total_fasting_days, 7)
        self.assertFalse(vrat.has_kshaya)
        self.assertFalse(vrat.has_vriddhi)

    def test_kshaya_rule_enforces_7_days_from_saptami(self):
        """If a Tithi in 8..14 is skipped (e.g. Navami 9 is skipped), start shifts back to Saptami to guarantee 7 days."""
        start = date(2026, 5, 20)
        # 8, 10, 11, 12, 13, 14 (6 days) -> Tithi 9 is skipped
        daily_tithis = {
            start - timedelta(days=1): 7,  # Saptami
            start: 8,                      # Ashtami
            start + timedelta(days=1): 10, # Dashami (Navami skipped)
            start + timedelta(days=2): 11,
            start + timedelta(days=3): 12,
            start + timedelta(days=4): 13,
            start + timedelta(days=5): 14, # Chaturdashi
            start + timedelta(days=6): 15,
        }
        provider = MockTithiProvider(daily_tithis)
        vrat = calculate_bhaktambar_vrat(2026, 5, "Shukla", 28.6139, 77.2090, provider)

        self.assertIsNotNone(vrat)
        # Starts on Saptami (May 19)
        self.assertEqual(vrat.start_date, "2026-05-19")
        self.assertEqual(vrat.end_date, "2026-05-25")
        self.assertEqual(vrat.total_fasting_days, 7)
        self.assertTrue(vrat.has_kshaya)
        self.assertFalse(vrat.has_vriddhi)

    def test_vriddhi_rule_extends_to_second_chaturdashi(self):
        """If Chaturdashi repeats, span extends to 8 days and ends on 2nd Chaturdashi."""
        start = date(2026, 6, 20)
        # 8, 9, 10, 11, 12, 13, 14, 14 (8 days)
        daily_tithis = {
            start - timedelta(days=1): 7,
            start: 8,
            start + timedelta(days=1): 9,
            start + timedelta(days=2): 10,
            start + timedelta(days=3): 11,
            start + timedelta(days=4): 12,
            start + timedelta(days=5): 13,
            start + timedelta(days=6): 14,
            start + timedelta(days=7): 14,  # 2nd Chaturdashi
            start + timedelta(days=8): 15,
        }
        provider = MockTithiProvider(daily_tithis)
        vrat = calculate_bhaktambar_vrat(2026, 6, "shukla", 28.6139, 77.2090, provider)

        self.assertIsNotNone(vrat)
        self.assertEqual(vrat.start_date, "2026-06-20")
        self.assertEqual(vrat.end_date, "2026-06-27")
        self.assertEqual(vrat.total_fasting_days, 8)
        self.assertFalse(vrat.has_kshaya)
        self.assertTrue(vrat.has_vriddhi)

    def test_krishna_paksha_case_insensitivity(self):
        """Krishna Paksha targets Tithis 23..29 (Krishna 8 to Krishna 14) and accepts any casing."""
        start = date(2026, 7, 5)
        # Krishna 8 (23) to Krishna 14 (29)
        daily_tithis = {
            start - timedelta(days=1): 22,
            start: 23,
            start + timedelta(days=1): 24,
            start + timedelta(days=2): 25,
            start + timedelta(days=3): 26,
            start + timedelta(days=4): 27,
            start + timedelta(days=5): 28,
            start + timedelta(days=6): 29,
            start + timedelta(days=7): 30,
        }
        provider = MockTithiProvider(daily_tithis)
        
        # Test various casings: KRISHNA, Krishna, krishna
        for paksha_input in ["KRISHNA", "Krishna", "krishna", "  kRiShNa  "]:
            vrat = calculate_bhaktambar_vrat(2026, 7, paksha_input, 28.6139, 77.2090, provider)
            self.assertIsNotNone(vrat, f"Failed for paksha casing: {paksha_input}")
            self.assertEqual(vrat.start_date, "2026-07-05")
            self.assertEqual(vrat.end_date, "2026-07-11")
            self.assertEqual(vrat.total_fasting_days, 7)


class BhaktambarFestivalServiceIntegrationTest(unittest.TestCase):
    def test_annual_bhaktambar_vrats_resolution_2026(self):
        """Verify that generate_jain_festivals produces Bhaktambar Vrat spans for both pakshas across the year."""
        from jain_observances.festival_service import generate_jain_festivals

        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        self.assertIn("festivals", res)

        bhak_events = [f for f in res["festivals"] if "Bhaktambar" in f.get("name", "") or "bhaktambar" in f.get("id", "")]
        # A standard year has at least 24 fortnights (12 Shukla + 12 Krishna)
        self.assertGreaterEqual(len(bhak_events), 24)

        for event in bhak_events:
            self.assertTrue(event["is_span"])
            self.assertEqual(event["badge"], "Bhaktambar Vrat")
            self.assertEqual(event["badge_color"], "purple")
            self.assertIn("duration_days", event)
            self.assertGreaterEqual(event["duration_days"], 7)  # Guaranteed minimum 7 days
            self.assertIn("has_kshaya", event)
            self.assertIn("has_vriddhi", event)
            self.assertIn("–", event["span_label"])
            self.assertEqual(event["status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
