"""
tests/test_prevailing_tithi.py -- Unit tests for get_prevailing_tithi_index(),
the single day-identity Tithi anchor introduced by the tithi-unification
refactor (see plans/tithi_unification/design.md).
"""
import unittest
from datetime import date

from astronomy import get_sunrise, local_time_to_jd
from panchang import (
    get_prevailing_tithi_index,
    get_tithi_at_jd,
    JAIN_TITHI_OFFSET_DAYS,
    _find_tithi_in_range,
    _tithi_owns_civil_day,
    find_diwali,
)

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

    def test_backshifts_a_kshaya_amavasya_to_the_preceding_day(self):
        """The Kartika Amavasya of 2028 is kshaya at the 6-ghati anchor (it
        spans 17 Oct ~13:00 -> 18 Oct ~08:30, touching neither day's
        sunrise+144min). The strict prevailing-tithi scan skipped it entirely
        and ran on to the Margashirsha Amavasya; the -1 kshaya rule places it
        on 17 Oct, the Chaturdashi day. Same October window as the test above,
        exercised through _find_tithi_in_range directly since
        find_chaitra_shukla_1's own March window never hits a kshaya Amavasya
        in 2025-2028."""
        result = _find_tithi_in_range(2028, 10, 10, 46, 30, LAT, LON, TZ, AYANAMSA)
        self.assertEqual(result, date(2028, 10, 17))


class TithiOwnsCivilDayTests(unittest.TestCase):
    def test_true_when_target_prevails_at_six_ghati(self):
        """18 Mar 2026: Amavasya (30) prevails at sunrise+144min -> the day owns it."""
        self.assertTrue(_tithi_owns_civil_day(date(2026, 3, 18), 30, LAT, LON, TZ, AYANAMSA))

    def test_true_on_preceding_day_when_target_is_kshaya(self):
        """Kartika Amavasya 2028 is kshaya at the 6-ghati anchor; under the -1
        rule it merges onto 17 Oct, the Chaturdashi day."""
        self.assertTrue(_tithi_owns_civil_day(date(2028, 10, 17), 30, LAT, LON, TZ, AYANAMSA))

    def test_false_on_the_day_after_a_kshaya_target(self):
        """18 Oct 2028: the tithi AT sunrise is Amavasya, but by sunrise+144min
        it has rolled to Pratipada; the kshaya Amavasya belongs to the 17th,
        not here."""
        self.assertFalse(_tithi_owns_civil_day(date(2028, 10, 18), 30, LAT, LON, TZ, AYANAMSA))

    def test_false_on_an_unrelated_day(self):
        """10 Mar 2026 is nowhere near an Amavasya (prevailing tithi ~Krishna
        Shashthi) -- not the target and not its preceding tithi."""
        self.assertFalse(_tithi_owns_civil_day(date(2026, 3, 10), 30, LAT, LON, TZ, AYANAMSA))


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

    def test_2028_kshaya_kartika_amavasya_backshifts_to_oct_17(self):
        """Regression for the Task 5 handoff finding: the strict 6-ghati match
        skipped the kshaya Kartika Amavasya and returned 16 Nov (the
        Margashirsha Amavasya the function is meant to exclude). The -1 kshaya
        rule lands Diwali on 17 Oct.

        NOTE: 17 Oct 2028 is asserted here as the OUTPUT of this project's
        established kshaya convention (festival_rules._kshaya_backshift), not
        as an independently religiously-verified date -- that check is the
        samvat_anchors.xlsx re-run plus user sign-off."""
        self.assertEqual(find_diwali(2028, LAT, LON, TZ, AYANAMSA), date(2028, 10, 17))


if __name__ == '__main__':
    unittest.main()
