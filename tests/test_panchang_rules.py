import unittest

from astronomy import get_planetary_longitude, jd_to_zoned_datetime
from panchang import get_nakshatra, get_tithi
from panchang_service import (
    JAIN_OFFSET_CHECK,
    SPECIAL_RULE_OFFSET,
    calculate_jain_tithi,
    generate_location_panchang,
    resolve_location,
)


class PanchangRuleTests(unittest.TestCase):
    def test_jaipur_udaya_tithi_uses_sunrise(self):
        result = generate_location_panchang(
            "2025-01-01",
            lat=26.9124,
            lon=75.7873,
        )

        sunrise_jd = result["events"]["sunrise"]["jd"]
        sun_lon = get_planetary_longitude(sunrise_jd, "Sun")
        moon_lon = get_planetary_longitude(sunrise_jd, "Moon")
        expected_tithi = get_tithi(sun_lon, moon_lon)

        self.assertEqual(result["panchang"]["tithi"]["index"], expected_tithi)
        self.assertEqual(result["rules"]["primary_day_rule"], "udaya_tithi")

    def test_special_reference_uses_exact_2h45m_after_sunrise(self):
        result = generate_location_panchang(
            "2025-08-15",
            lat=19.0760,
            lon=72.8777,
        )

        sunrise_dt = jd_to_zoned_datetime(result["events"]["sunrise"]["jd"], result["timezone"])
        special_dt = jd_to_zoned_datetime(
            result["rules"]["special_reference"]["reference"]["jd"],
            result["timezone"],
        )

        self.assertIsNotNone(sunrise_dt)
        self.assertIsNotNone(special_dt)
        self.assertLess(abs((special_dt - sunrise_dt) - SPECIAL_RULE_OFFSET).total_seconds(), 1.0)

        special_jd = result["rules"]["special_reference"]["reference"]["jd"]
        sun_lon = get_planetary_longitude(special_jd, "Sun")
        moon_lon = get_planetary_longitude(special_jd, "Moon")

        self.assertEqual(result["rules"]["special_reference"]["tithi"]["index"], get_tithi(sun_lon, moon_lon))
        self.assertEqual(
            result["rules"]["special_reference"]["nakshatra"]["index"],
            get_nakshatra(moon_lon),
        )

        comparison_rules = {
            item["rule"]: item for item in result["rules"]["reference_checks"]
        }
        self.assertIn("sunrise_plus_2h24m_candidate", comparison_rules)
        self.assertIn("sunrise_plus_2h45m_legacy", comparison_rules)

    def test_jain_tithi_uses_exact_2h24m_after_sunrise(self):
        result = generate_location_panchang(
            "2025-08-15",
            lat=19.0760,
            lon=72.8777,
        )

        sunrise_dt = jd_to_zoned_datetime(result["events"]["sunrise"]["jd"], result["timezone"])
        jain_reference_dt = jd_to_zoned_datetime(
            result["panchang"]["jain_tithi"]["reference"]["jd"],
            result["timezone"],
        )

        self.assertIsNotNone(sunrise_dt)
        self.assertIsNotNone(jain_reference_dt)
        self.assertLess(abs((jain_reference_dt - sunrise_dt) - JAIN_OFFSET_CHECK).total_seconds(), 1.0)

        jain_reference_jd = result["panchang"]["jain_tithi"]["reference"]["jd"]
        sun_lon = get_planetary_longitude(jain_reference_jd, "Sun")
        moon_lon = get_planetary_longitude(jain_reference_jd, "Moon")

        self.assertEqual(result["panchang"]["jain_tithi"]["index"], get_tithi(sun_lon, moon_lon))
        self.assertEqual(result["structured"]["jain_tithi"], result["panchang"]["jain_tithi"]["name"])

    def test_calculate_jain_tithi_accepts_date_and_location(self):
        location = resolve_location(lat=26.9124, lon=75.7873)
        jain_tithi = calculate_jain_tithi("2025-01-01", location)

        self.assertIn("Jain_Tithi_Index", jain_tithi)
        self.assertIn("Jain_Tithi_End_JD", jain_tithi)
        self.assertGreater(jain_tithi["Jain_Tithi_Reference_JD"], 0.0)

    def test_sunrise_resolves_to_requested_local_date(self):
        result = generate_location_panchang(
            "2025-03-21",
            lat=28.6139,
            lon=77.2090,
        )

        sunrise_dt = jd_to_zoned_datetime(result["events"]["sunrise"]["jd"], result["timezone"])
        sunset_dt = jd_to_zoned_datetime(result["events"]["sunset"]["jd"], result["timezone"])

        self.assertIsNotNone(sunrise_dt)
        self.assertIsNotNone(sunset_dt)
        self.assertEqual(sunrise_dt.date().isoformat(), "2025-03-21")
        self.assertGreater(sunset_dt, sunrise_dt)

    def test_resolve_location_validates_coordinate_ranges(self):
        with self.assertRaisesRegex(ValueError, "Latitude must be between -90 and 90 degrees."):
            resolve_location(lat=120.0, lon=77.2090)

        with self.assertRaisesRegex(ValueError, "Longitude must be between -180 and 180 degrees."):
            resolve_location(lat=28.6139, lon=220.0)


if __name__ == "__main__":
    unittest.main()
