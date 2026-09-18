import unittest
from datetime import date

from astronomy import get_planetary_longitude, jd_to_zoned_datetime
from panchang import TITHI_NAMES, VARA_NAMES, generate_daily_panchang, get_nakshatra, get_tithi
from panchang_service import (
    JAIN_OFFSET_CHECK,
    calculate_jain_tithi,
    generate_location_panchang,
    resolve_location,
)


class PanchangRuleTests(unittest.TestCase):
    def test_jaipur_all_day_tithi_list_still_starts_at_sunrise(self):
        """panchang.tithi is the descriptive list of every Tithi touching the civil
        day (sunrise to next sunrise) -- unaffected by which Tithi is the day's
        PRIMARY one (see test_primary_tithi_is_6ghati_not_udaya below)."""
        result = generate_location_panchang(
            "2025-01-01",
            lat=26.9124,
            lon=75.7873,
        )

        sunrise_jd = result["events"]["sunrise"]["jd"]
        sun_lon = get_planetary_longitude(sunrise_jd, "Sun")
        moon_lon = get_planetary_longitude(sunrise_jd, "Moon")
        expected_tithi = get_tithi(sun_lon, moon_lon)

        self.assertEqual(result["panchang"]["tithi"][0]["index"], expected_tithi)

    def test_primary_tithi_is_6ghati_not_udaya(self):
        """Regression: the daily API's headline Tithi must agree with the 6-ghati
        hindu_month it's shown alongside, not contradict it. On 2026-03-19
        (confirmed by the user as Chaitra Shukla 1 / Vikram Samvat New Year), the
        udaya (sunrise) Tithi is still Amavasya -- displaying "Chaitra month,
        Amavasya Tithi" is self-contradictory. See plans/tithi_unification/design.md's
        Full Jain decision: the separate jain_tithi reference-only field is dropped
        because there is now only one Tithi."""
        result = generate_location_panchang("2026-03-19", lat=19.0760, lon=72.8777)

        self.assertEqual(result["structured"]["tithi"], "Shukla Pratipada")
        self.assertEqual(result["panchang"]["hindu_month"]["name"], "Chaitra")
        self.assertEqual(result["rules"]["primary_day_rule"], "6_ghati_tithi")
        self.assertNotIn("jain_tithi", result["structured"])
        # panchang.jain_tithi is intentionally KEPT (unlike structured.jain_tithi):
        # app.py's range-export loop and static/app.js's home-page widget both read
        # this specific key. It's the same 6-ghati value as structured.tithi now,
        # just not yet consolidated at those call sites.
        self.assertEqual(result["panchang"]["jain_tithi"]["name"], result["structured"]["tithi"])

    def test_primary_tithi_uses_exact_2h24m_after_sunrise(self):
        """The (now sole) primary Tithi is computed at sunrise + 2h24m, not at
        plain sunrise. Formerly asserted via the separate jain_tithi reference-only
        field, which design.md's Full Jain decision removed -- there's only one
        Tithi now, so this checks it directly against the primary fields."""
        # 2026-03-19: sunrise tithi (Amavasya) and 6-ghati tithi (Shukla Pratipada)
        # genuinely differ here, so this actually exercises which one wins.
        result = generate_location_panchang(
            "2026-03-19",
            lat=19.0760,
            lon=72.8777,
        )

        sunrise_dt = jd_to_zoned_datetime(result["events"]["sunrise"]["jd"], result["timezone"])
        reference_jd = result["events"]["sunrise"]["jd"] + (JAIN_OFFSET_CHECK.total_seconds() / 86400.0)
        reference_dt = jd_to_zoned_datetime(reference_jd, result["timezone"])

        self.assertIsNotNone(sunrise_dt)
        self.assertIsNotNone(reference_dt)
        self.assertLess(abs((reference_dt - sunrise_dt) - JAIN_OFFSET_CHECK).total_seconds(), 1.0)

        sun_lon = get_planetary_longitude(reference_jd, "Sun")
        moon_lon = get_planetary_longitude(reference_jd, "Moon")
        expected_name = TITHI_NAMES[get_tithi(sun_lon, moon_lon) - 1]

        self.assertEqual(result["structured"]["tithi"], expected_name)

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

    def test_weekday_matches_requested_local_date(self):
        result = generate_location_panchang(
            "2026-05-05",
            lat=26.9124,
            lon=75.7873,
        )

        self.assertEqual(result["panchang"]["vara"]["index"], 2)
        self.assertEqual(result["panchang"]["vara"]["name"], "Mangalavara (Tuesday)")

    def test_generate_daily_panchang_local_date_overrides_jd_boundary_effect(self):
        local_date = date(2026, 5, 5)
        midnight_like_jd = 2461165.2708333335

        panchang = generate_daily_panchang(midnight_like_jd, local_date=local_date)

        self.assertEqual(panchang["Vara_Index"], 2)
        self.assertEqual(panchang["Vara_Name"], VARA_NAMES[2])


if __name__ == "__main__":
    unittest.main()
