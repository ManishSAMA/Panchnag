"""
tests/test_vrat_provider.py -- Unit tests for SwissEphTithiProvider
(jain_observances/vrats/provider.py), the shared provider the Vrat modules
use for tithi/month lookups.
"""
import unittest
from datetime import date

from jain_observances.vrats.provider import SwissEphTithiProvider

LAT, LON = 19.0760, 72.8777  # Mumbai


class HinduMonthUsesSixGhatiTests(unittest.TestCase):
    """Regression: get_hindu_month_name / is_adhik_month called get_hindu_month()
    at plain sunrise, while daslakshan.py and ratnatraya.py already compute their
    own tithi cutoff at sunrise + 144min (6 ghati) -- see their `cutoff_time`
    expressions. On 2026-03-19 (confirmed by the user as Chaitra Shukla 1) the two
    disagree: sunrise still says Phalguna, 6-ghati says Chaitra. Provider must
    match every other 6-ghati call site in the codebase (db_generator.py,
    export.py, panchang_service.py, festival_service.py)."""

    def setUp(self):
        self.provider = SwissEphTithiProvider(ayanamsa="Lahiri")

    def test_get_hindu_month_name_matches_6ghati_not_sunrise(self):
        self.assertEqual(
            self.provider.get_hindu_month_name(date(2026, 3, 19), LAT, LON),
            "Chaitra",
        )

    def test_is_adhik_month_evaluated_at_6ghati(self):
        # Not an Adhik month either way for this date -- this pins the mechanism
        # (which reference_jd is used), not a specific True/False outcome.
        from panchang import get_hindu_month
        from astronomy import get_sunrise, local_date_anchor_jd
        from location_service import get_timezone_name

        tz_name = get_timezone_name(LAT, LON)
        anchor_jd = local_date_anchor_jd(date(2026, 3, 19), tz_name, clock="standard")
        sunrise_jd = get_sunrise(anchor_jd, LAT, LON)
        _, _, expected = get_hindu_month(sunrise_jd + (2.4 / 24.0), "Lahiri")

        self.assertEqual(
            self.provider.is_adhik_month(date(2026, 3, 19), LAT, LON),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
