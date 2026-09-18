"""
tests/test_hindi_calendar_pdf_tithi_month.py -- Regression for the same
sunrise/6-ghati mismatch fixed elsewhere this session (parva-tithi double-fire,
panchang_service.py's primary Tithi, vrats/provider.py), now for the Hindi
calendar PDF.

RESOLVED: the three generate_hindi_calendar_pdf*.py scripts this file was
written against are gone, replaced by hindi_calendar_pdf.py, which computes the
month and the Jain Tithi at the 6-ghati reference (and now also reports a
separate plain-sunrise Hindu Tithi column). See tests/test_hindi_calendar_pdf.py
for the tests that exercise that module directly.

These two tests are kept because they pin the underlying primitive against a
concrete, user-confirmed date (2026-03-19, Chaitra Shukla 1): the first records
what plain sunrise produces, the second what the 6-ghati reference produces.
They are the arithmetic the PDF depends on, independent of how it is packaged.
"""
import unittest

from astronomy import get_sunrise, local_time_to_jd
from panchang import JAIN_TITHI_OFFSET_DAYS, generate_daily_panchang, get_hindu_month, get_planetary_longitude

LAT, LON, TZ_OFFSET, AYANAMSA = 19.0760, 72.8777, 5.5, "Lahiri"


class HindiPdfTithiMonthMismatchTests(unittest.TestCase):
    def test_plain_sunrise_still_shows_the_contradiction_on_2026_03_19(self):
        """Sanity check on the bug these 3 files still have: as of this test,
        their jd_sr-based Tithi/month computation for 2026-03-19 (user-confirmed
        Chaitra Shukla 1) shows the same "Chaitra month, Amavasya Tithi"
        contradiction fixed elsewhere. If this test starts failing, the PDF
        scripts may already have been fixed to use the 6-ghati reference --
        update this test (and this file's docstring) accordingly."""
        jd_start = local_time_to_jd(2026, 3, 19, 0.0, TZ_OFFSET)
        jd_sr = get_sunrise(jd_start, LAT, LON)

        h_month_raw, _, _ = get_hindu_month(jd_sr, AYANAMSA)
        sun_lon = get_planetary_longitude(jd_sr, "Sun", AYANAMSA)
        moon_lon = get_planetary_longitude(jd_sr, "Moon", AYANAMSA)
        panchang = generate_daily_panchang(jd_sr, AYANAMSA, sun_lon=sun_lon, moon_lon=moon_lon)

        self.assertEqual(h_month_raw, "Phalguna")
        self.assertEqual(panchang["Tithi_Index"], 30)  # Amavasya

    def test_6ghati_reference_agrees_on_2026_03_19(self):
        """What the fix must produce once applied: month and Tithi computed at
        the same 6-ghati reference agree (Chaitra + Shukla Pratipada), matching
        panchang_service.py's already-fixed primary Tithi and hindu_month."""
        jd_start = local_time_to_jd(2026, 3, 19, 0.0, TZ_OFFSET)
        jd_sr = get_sunrise(jd_start, LAT, LON)
        reference_jd = jd_sr + JAIN_TITHI_OFFSET_DAYS

        h_month_raw, _, _ = get_hindu_month(reference_jd, AYANAMSA)
        sun_lon = get_planetary_longitude(reference_jd, "Sun", AYANAMSA)
        moon_lon = get_planetary_longitude(reference_jd, "Moon", AYANAMSA)
        panchang = generate_daily_panchang(reference_jd, AYANAMSA, sun_lon=sun_lon, moon_lon=moon_lon)

        self.assertEqual(h_month_raw, "Chaitra")
        self.assertEqual(panchang["Tithi_Index"], 1)  # Shukla Pratipada


if __name__ == "__main__":
    unittest.main()
