"""April 2026 Chaitra->Vaishakh boundary: a kshaya and a vriddhi in sequence.

Ruled on by the calendar owner and verified against the ephemeris. A Gregorian day
takes the Tithi active exactly 2h24m (6 ghati) after sunrise, and that single rule
produces this whole cascade at Delhi:

  28 Mar  Shukla 10   Tithi 11 begins just after this anchor (08:46:13) and ends
                      before the next day's (07:46:55 on 29 Mar), so it prevails at
                      no anchor at all -- KSHAYA. It merges onto Tithi 10's day.
  29 Mar  Shukla 12   12/13/14 all pushed forward by the loss
  01 Apr  Shukla 15   PURNIMA lands here, not 2 Apr
  02 Apr  Krishna 1   Vaishakh Krishna Paksha begins
  03 Apr  Krishna 1   Ekam is still active at this anchor too -- VRIDDHI, two days

Neither the 1 Apr Purnima nor the two-day Ekam is an error; both follow from the
anchor rule. These assertions exist so that stays true.
"""
import unittest
from datetime import date, timedelta

LAT, LON, TZ, AYA = 28.6139, 77.2090, 5.5, "Lahiri"


def _anchor_tithi(d):
    from panchang import get_sunrise, get_tithi_at_jd, local_time_to_jd, JAIN_TITHI_OFFSET_DAYS
    sr = get_sunrise(local_time_to_jd(d.year, d.month, d.day, 0.0, TZ), LAT, LON)
    return get_tithi_at_jd(sr + JAIN_TITHI_OFFSET_DAYS, AYA)


class ChaitraVaishakh2026AnomalyTest(unittest.TestCase):
    """Index 1-15 = Shukla 1-15, 16-29 = Krishna 1-14, 30 = Amavasya."""

    EXPECTED = {
        date(2026, 3, 27): 9,    # Shukla 9
        date(2026, 3, 28): 10,   # Shukla 10 (+ kshaya Tithi 11 merged here)
        date(2026, 3, 29): 12,   # Shukla 12 -- 11 skipped entirely
        date(2026, 3, 30): 13,
        date(2026, 3, 31): 14,
        date(2026, 4, 1): 15,    # PURNIMA
        date(2026, 4, 2): 16,    # Krishna 1
        date(2026, 4, 3): 16,    # Krishna 1 again -- VRIDDHI
        date(2026, 4, 4): 17,    # Krishna 2
    }

    def test_anchor_assignment_matches_the_ruled_sequence(self):
        for d, expected in sorted(self.EXPECTED.items()):
            self.assertEqual(expected, _anchor_tithi(d), f"{d}")

    def test_tithi_11_is_kshaya_and_prevails_on_no_day(self):
        d = date(2026, 3, 20)
        while d <= date(2026, 4, 5):
            self.assertNotEqual(11, _anchor_tithi(d), f"Shukla 11 should be kshaya, found on {d}")
            d += timedelta(days=1)

    def test_purnima_is_1_april_not_2_april(self):
        self.assertEqual(15, _anchor_tithi(date(2026, 4, 1)))
        self.assertNotEqual(15, _anchor_tithi(date(2026, 4, 2)))

    def test_ekam_spans_two_days_as_vriddhi(self):
        self.assertEqual(16, _anchor_tithi(date(2026, 4, 2)))
        self.assertEqual(16, _anchor_tithi(date(2026, 4, 3)))
        self.assertEqual(17, _anchor_tithi(date(2026, 4, 4)))


if __name__ == "__main__":
    unittest.main()


class VriddhiFirstDayConventionTest(unittest.TestCase):
    """When a tithi prevails at the Jain day-start on two consecutive civil days
    (vriddhi), the observance is fixed to the FIRST of the two -- overriding the
    udaya rule, which would land on the second. Confirmed as the real rule by the
    calendar owner; this pins it so it cannot drift."""

    def _snap(self, d, paksha, tithi):
        return {"date": d, "jain_paksha": paksha, "jain_tithi_in_paksha": tithi}

    def test_picks_the_first_of_two_consecutive_days(self):
        from jain_observances.festival_rules import _first_of_two_jain_daystart_days
        snaps = [
            self._snap(date(2026, 4, 1), "Krishna", 14),
            self._snap(date(2026, 4, 2), "Krishna", 1),
            self._snap(date(2026, 4, 3), "Krishna", 1),   # vriddhi second day
            self._snap(date(2026, 4, 4), "Krishna", 2),
        ]
        self.assertEqual(date(2026, 4, 2),
                         _first_of_two_jain_daystart_days(snaps, "Krishna", 1))

    def test_returns_none_when_the_tithi_spans_only_one_day(self):
        from jain_observances.festival_rules import _first_of_two_jain_daystart_days
        snaps = [
            self._snap(date(2026, 4, 2), "Krishna", 1),
            self._snap(date(2026, 4, 3), "Krishna", 2),
        ]
        self.assertIsNone(_first_of_two_jain_daystart_days(snaps, "Krishna", 1))

    def test_non_consecutive_repeats_do_not_count_as_vriddhi(self):
        from jain_observances.festival_rules import _first_of_two_jain_daystart_days
        snaps = [
            self._snap(date(2026, 4, 2), "Krishna", 1),
            self._snap(date(2026, 4, 9), "Krishna", 1),
        ]
        self.assertIsNone(_first_of_two_jain_daystart_days(snaps, "Krishna", 1))
