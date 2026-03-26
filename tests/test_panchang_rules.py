import unittest

from astronomy import get_planetary_longitude, jd_to_zoned_datetime
from panchang import get_nakshatra, get_tithi
from panchang_service import SPECIAL_RULE_OFFSET, generate_location_panchang


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


if __name__ == "__main__":
    unittest.main()
