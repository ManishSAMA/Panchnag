"""
tests/test_prevailing_tithi.py -- Unit tests for get_prevailing_tithi_index(),
the single day-identity Tithi anchor introduced by the tithi-unification
refactor (see plans/tithi_unification/design.md).
"""
import unittest
from datetime import date

from astronomy import get_sunrise, local_time_to_jd
from panchang import get_prevailing_tithi_index, get_tithi_at_jd, JAIN_TITHI_OFFSET_DAYS, _find_tithi_in_range, find_diwali

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


class FindTithiInRangeUsesPrevailingTithiTests(unittest.TestCase):
    def test_finds_amavasya_on_march_18_2026_not_march_19(self):
        """Regression test for the parva_tithi_amavasya double-fire root cause
        (see plans/tithi_unification/design.md): under the OLD sunrise rule
        this returned March 19 (documented in the pre-refactor panchang.py
        docstring). Under the prevailing (6-ghati) rule it returns March 18,
        since Amavasya prevails at sunrise+144min on the 18th but not yet at
        sunrise itself; by the 19th's sunrise+144min it has already advanced
        to Shukla Pratipada.

        NOTE: whether March 18 is the date a real Jain panchang would print
        for this Amavasya is a SEPARATE question, verified via
        plans/tithi_unification/samvat_anchors.xlsx (Task 1/5) with the user,
        not asserted here. This test only pins the function's mechanics."""
        result = _find_tithi_in_range(
            2026, 3, 1, 52, 30, LAT, LON, TZ, AYANAMSA
        )
        self.assertEqual(result, date(2026, 3, 18))


class FindDiwaliUsesPrevailingTithiTests(unittest.TestCase):
    def test_2026_diwali_unchanged_since_sunrise_and_prevailing_agree(self):
        """For 2026, sunrise-tithi and prevailing(6-ghati)-tithi both name
        Nov 9 as Amavasya (verified live against the engine during design:
        Nov 8 prevailing=Krishna Chaturdashi, Nov 9 prevailing=Amavasya) --
        so find_diwali's OWN (sunrise-based, pradosh is a separate mechanism
        in festival_rules.py, out of scope here) result does not move this
        year. This test locks that invariance so a future change to this
        function is caught if it silently shifts an unrelated case."""
        self.assertEqual(find_diwali(2026, LAT, LON, TZ, AYANAMSA), date(2026, 11, 9))


if __name__ == '__main__':
    unittest.main()
