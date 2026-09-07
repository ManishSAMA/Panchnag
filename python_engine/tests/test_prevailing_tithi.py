"""
tests/test_prevailing_tithi.py -- Unit tests for get_prevailing_tithi_index(),
the single day-identity Tithi anchor introduced by the tithi-unification
refactor (see plans/tithi_unification/design.md).
"""
import unittest

from astronomy import get_sunrise, local_time_to_jd
from panchang import get_prevailing_tithi_index, get_tithi_at_jd, JAIN_TITHI_OFFSET_DAYS

LAT, LON, TZ = 19.0760, 72.8777, 5.5  # Mumbai -- matches main.py's sample coords
AYANAMSA = "Lahiri"


class GetPrevailingTithiIndexTests(unittest.TestCase):
    def test_evaluates_at_sunrise_plus_144_minutes_not_at_sunrise(self):
        """18 Mar 2026, Mumbai: the tithi AT sunrise is Krishna Chaturdashi (29),
        but it has already rolled to Amavasya (30) by sunrise + 144 min.
        get_prevailing_tithi_index must report the LATER (6-ghati) value, not
        the sunrise-instant one."""
        jd0 = local_time_to_jd(2026, 3, 18, 0.0, TZ)
        sunrise_jd = get_sunrise(jd0, LAT, LON)

        sunrise_instant_tithi = get_tithi_at_jd(sunrise_jd, AYANAMSA)
        self.assertEqual(sunrise_instant_tithi, 29, "sanity check on the sunrise-instant value")

        self.assertEqual(get_prevailing_tithi_index(sunrise_jd, AYANAMSA), 30)

    def test_offset_applied_is_exactly_the_jain_tithi_offset(self):
        """The prevailing tithi at sunrise_jd must equal the plain tithi
        evaluated at sunrise_jd + JAIN_TITHI_OFFSET_DAYS -- no other offset."""
        jd0 = local_time_to_jd(2026, 3, 19, 0.0, TZ)
        sunrise_jd = get_sunrise(jd0, LAT, LON)

        expected = get_tithi_at_jd(sunrise_jd + JAIN_TITHI_OFFSET_DAYS, AYANAMSA)
        self.assertEqual(get_prevailing_tithi_index(sunrise_jd, AYANAMSA), expected)

    def test_default_ayanamsa_is_lahiri(self):
        jd0 = local_time_to_jd(2026, 3, 20, 0.0, TZ)
        sunrise_jd = get_sunrise(jd0, LAT, LON)
        self.assertEqual(
            get_prevailing_tithi_index(sunrise_jd),
            get_prevailing_tithi_index(sunrise_jd, "Lahiri"),
        )


if __name__ == '__main__':
    unittest.main()
