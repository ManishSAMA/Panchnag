import unittest
from datetime import date
from unittest.mock import patch

from astronomy import get_planetary_longitude, jd_to_zoned_datetime
from panchang import calculate_bhadra_kaal, get_karana
from panchang_service import generate_location_panchang
from export import format_row_data
from export_pdf import generate_pdf_calendar


class BhadraKaalTests(unittest.TestCase):
    def test_zodiac_residence_mapping(self):
        """Verify that all 12 Rashi indices map to the correct residence and risk level."""
        # This will test the residence and risk logic indirectly or directly.
        # We can implement a helper function in panchang.py and test it.
        from panchang import get_bhadra_residence_and_risk
        
        # Earth: Cancer (3), Leo (4), Aquarius (10), Pisces (11) -> High
        for r_idx in [3, 4, 10, 11]:
            res, risk = get_bhadra_residence_and_risk(r_idx)
            self.assertEqual(res, "Earth")
            self.assertEqual(risk, "High")
            
        # Heaven: Aries (0), Taurus (1), Gemini (2), Scorpio (7) -> Low
        for r_idx in [0, 1, 2, 7]:
            res, risk = get_bhadra_residence_and_risk(r_idx)
            self.assertEqual(res, "Heaven")
            self.assertEqual(risk, "Low")
            
        # Underworld: Virgo (5), Libra (6), Sagittarius (8), Capricorn (9) -> Low
        for r_idx in [5, 6, 8, 9]:
            res, risk = get_bhadra_residence_and_risk(r_idx)
            self.assertEqual(res, "Underworld")
            self.assertEqual(risk, "Low")

    def test_cycle_validation_mismatch(self):
        """Test that if the Vishti Karana is active but its index is not standard, an error is raised."""
        from panchang import validate_vishti_karana
        
        # Standard Vishti 1-based indices: {8, 15, 22, 29, 36, 43, 50, 57}
        # Standard match should not raise an error
        for idx in [8, 15, 22, 29, 36, 43, 50, 57]:
            validate_vishti_karana(idx, "Vishti (Bhadra)")
            
        # Non-Vishti index with Vishti name should raise ValueError
        with self.assertRaises(ValueError):
            validate_vishti_karana(1, "Vishti (Bhadra)")
            
        # Vishti index with non-Vishti name should raise ValueError
        with self.assertRaises(ValueError):
            validate_vishti_karana(8, "Bava")

    def test_no_vishti_overlap_returns_empty(self):
        """If there is no Vishti Karana overlapping the sunrise-to-next-sunrise window, return empty list."""
        # Pick a date where Vishti is not active.
        # e.g., 2025-01-01 (Tithi Shukla Dwitiya/Tritiya has no Vishti. Vishti is on Chaturthi 2nd half)
        # Sunrise for 2025-01-01 in Jaipur is approx JD 2460676.57
        # Let's call calculate_bhadra_kaal for 2025-01-01
        result = generate_location_panchang("2025-01-01", lat=26.9124, lon=75.7873)
        bhadra = result.get("bhadra_kaal")
        self.assertIsNotNone(bhadra)
        self.assertEqual(bhadra["has_windows"], False)
        self.assertEqual(bhadra["windows"], [])
        self.assertEqual(bhadra["risk_level"], "Low")

    def test_bhada_crossing_sunrise_is_clipped(self):
        """Test that a Bhadra window crossing the sunrise or next sunrise boundary is clipped correctly."""
        # Pick a date where Bhadra crosses sunrise.
        # For example, on a day when Bhadra starts before sunrise or ends after next sunrise.
        # We can verify that clipped_start or clipped_end is True.
        # Let's inspect 2025-01-03 or 2025-01-04 (Shukla Chaturthi is around Jan 3-4, 2025).
        # We will search a range or verify via a mock that clipping works.
        # Let's write a mock test to precisely verify clipping.
        from panchang import calculate_bhadra_kaal
        
        with patch('panchang.calculate_karana_details') as mock_karana:
            # Mock a single Karana period that starts before sunrise and ends after sunrise
            mock_karana.return_value = {
                'Karana_Index': 8,
                'Karana_Name': 'Vishti (Bhadra)',
                'Karana_Start_JD': 10.0,
                'Karana_End_JD': 20.0
            }
            
            # Sunrise-to-next-sunrise is 12.0 to 13.0
            # Vishti starts at 10.0 (< 12.0) and ends at 20.0 (> 13.0)
            with patch('panchang.get_planetary_longitude') as mock_lon:
                mock_lon.return_value = 100.0  # Cancer Rashi
                segments = calculate_bhadra_kaal(12.0, 13.0)
                
                self.assertEqual(len(segments), 1)
                seg = segments[0]
                self.assertEqual(seg["start_jd"], 12.0)
                self.assertEqual(seg["end_jd"], 13.0)
                self.assertEqual(seg["clipped_start"], True)
                self.assertEqual(seg["clipped_end"], True)

    def test_moon_rashi_transition_splits_vishti(self):
        """Test that if the Moon Rashi transitions from one sign to another inside Vishti, it is split."""
        from panchang import calculate_bhadra_kaal
        
        with patch('panchang.calculate_karana_details') as mock_karana:
            mock_karana.return_value = {
                'Karana_Index': 8,
                'Karana_Name': 'Vishti (Bhadra)',
                'Karana_Start_JD': 10.0,
                'Karana_End_JD': 20.0
            }
            
            # We want Moon Rashi to be Gemini (Index 2, low risk) at JD 10.0,
            # and Cancer (Index 3, high risk) at JD 20.0.
            # Rashi boundary transition is at Moon Longitude 90.0 (from Gemini to Cancer).
            # Let's mock get_planetary_longitude:
            # - At JD 10.0, longitude is 85.0 (Gemini)
            # - At JD 15.0, longitude is 90.0 (exact transition)
            # - At JD 20.0, longitude is 95.0 (Cancer)
            def mock_lon_func(jd, planet, ayanamsa='Lahiri'):
                if planet == 'Moon':
                    # Linear longitude: 85.0 at 10.0, 95.0 at 20.0
                    return 85.0 + (jd - 10.0) * 1.0
                return 0.0  # Sun
                
            with patch('panchang.get_planetary_longitude', side_effect=mock_lon_func):
                segments = calculate_bhadra_kaal(10.0, 20.0)
                
                self.assertEqual(len(segments), 2)
                
                # Segment 1: Low risk (Gemini)
                seg1 = segments[0]
                self.assertEqual(seg1["start_jd"], 10.0)
                self.assertAlmostEqual(seg1["end_jd"], 15.0, places=3)
                self.assertEqual(seg1["residence"], "Heaven")
                self.assertEqual(seg1["risk_level"], "Low")
                
                # Segment 2: High risk (Cancer)
                seg2 = segments[1]
                self.assertAlmostEqual(seg2["start_jd"], 15.0, places=3)
                self.assertEqual(seg2["end_jd"], 20.0)
                self.assertEqual(seg2["residence"], "Earth")
                self.assertEqual(seg2["risk_level"], "High")

    def test_daily_api_returns_payload(self):
        """Verify that the daily Panchang API payload contains the correctly structured bhadra_kaal field."""
        result = generate_location_panchang("2025-01-03", lat=26.9124, lon=75.7873)
        
        self.assertIn("bhadra_kaal", result)
        bk = result["bhadra_kaal"]
        self.assertIn("has_windows", bk)
        self.assertIn("is_active", bk)
        self.assertIn("risk_level", bk)
        self.assertIn("windows", bk)
        
        for w in bk["windows"]:
            self.assertIn("start", w)
            self.assertIn("end", w)
            self.assertIn("moon_rashi", w)
            self.assertIn("residence", w)
            self.assertIn("risk_level", w)
            self.assertIn("is_active", w)
            self.assertIn("clipped_start", w)
            self.assertIn("clipped_end", w)

    def test_flat_export_columns(self):
        """Verify that format_row_data adds readable Bhadra columns to the row dictionary."""
        # Create dummy panchang & bhadra data
        panchang = {
            "Vara_Name": "Ravivara (Sunday)",
            "Tithi_Index": 1,
            "Tithi_Name": "Shukla Pratipada",
            "Nakshatra_Index": 1,
            "Nakshatra_Name": "Ashwini",
            "Nakshatra_Pada": 1,
            "Yoga_Index": 1,
            "Yoga_Name": "Vishkumbha",
            "Karana_Index": 1,
            "Karana_Name": "Kimstughna",
            "Karana_Start_JD": 2460676.5,
            "Karana_End_JD": 2460677.0,
        }
        
        bhadra_kaal = [
            {
                "start_jd": 2460676.6,
                "end_jd": 2460676.8,
                "moon_rashi": "Karka (Cancer)",
                "residence": "Earth",
                "risk_level": "High",
                "clipped_start": False,
                "clipped_end": False
            }
        ]
        
        row = format_row_data(
            date_str="2025-01-01",
            julian_date=2460676.5,
            planets={"Sun": 250.0, "Moon": 95.0},
            panchang=panchang,
            jain_tithi={"Jain_Tithi_Index": 1, "Jain_Tithi_Name": "Shukla Pratipada", "Jain_Tithi_End_JD": 2460676.9},
            sunrise_str="07:18:00",
            sunset_str="17:40:00",
            moonrise_str="08:00:00",
            moonset_str="19:00:00",
            ayanamsa_dec=24.0,
            bhadra_kaal=bhadra_kaal,
        )
        
        self.assertIn("Has_Bhadra", row)
        self.assertIn("Bhadra_Windows", row)
        self.assertIn("Bhadra_Max_Risk", row)
        self.assertEqual(row["Has_Bhadra"], True)
        self.assertEqual(row["Bhadra_Max_Risk"], "High")
        self.assertIn("Earth", row["Bhadra_Windows"])

    def test_pdf_generation_runs_successfully(self):
        """Verify that generating the PDF table with the Bhadra column runs without error."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test_calendar.pdf")
            # Generate calendar for 2025 for Jaipur (only 1-2 months are generated in actual calls, 
            # but generate_pdf_calendar generates 12. Let's make sure it finishes successfully)
            generate_pdf_calendar(2025, pdf_path, lat=26.9124, lon=75.7873)
            self.assertTrue(os.path.exists(pdf_path))


if __name__ == "__main__":
    unittest.main()
