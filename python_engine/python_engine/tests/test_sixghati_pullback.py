"""
tests/test_sixghati_pullback.py -- Unit tests for _sixghati_pullback
(jain_observances/festival_rules.py), the day-selection helper Kalyanaks and
other non-parva SingleTithi rules use to detect a "weak" udaya tithi.

Gap being fixed (found 2026-09-11, while investigating why the Chaitra/Phalguna
Amavasya cluster -- Ananthnath/Aranath Moksha Kalyanaks, Vikram Samvat
Varsha-Ant -- still landed on 2026-03-19 after the parva-tithi double-fire fix):
_sixghati_pullback only recognized ONE shape of "weak udaya, pull back":
the previous civil day still BUILDING TOWARD the target tithi (previous day's
sunrise AND 6-ghati are both target-1). It missed a second shape: the previous
civil day's 6-ghati has ALREADY REACHED the target tithi itself -- a short
tithi that starts before the previous day's 6-ghati mark and ends shortly
after this day's sunrise, never surviving to this day's own 6-ghati mark.
2026-03-18/19 is exactly this second shape (18th: sunrise=Chaturdashi(29),
6-ghati=Amavasya(30); 19th: sunrise=Amavasya(30), 6-ghati=Pratipada(1)).
"""
import unittest
from datetime import date

from jain_observances.festival_rules import _sixghati_pullback

MAR_18 = {
    "date": date(2026, 3, 18),
    "_sunrise_paksha": "Krishna", "_sunrise_tithi_in_paksha": 14,      # sunrise: Chaturdashi
    "paksha": "Krishna", "tithi_in_paksha": 15,
    "jain_paksha": "Krishna", "jain_tithi_in_paksha": 15,  # 6-ghati: Amavasya
}
MAR_19 = {
    "date": date(2026, 3, 19),
    "_sunrise_paksha": "Krishna", "_sunrise_tithi_in_paksha": 15,      # sunrise: Amavasya
    "paksha": "Shukla", "tithi_in_paksha": 1,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 1,    # 6-ghati: Pratipada
}


class SixGhatiPullbackReachedTargetTests(unittest.TestCase):
    def test_pulls_back_when_previous_day_already_reached_target_at_6ghati(self):
        """Regression: 2026-03-19's Amavasya is weak (6-ghati already rolled to
        Pratipada); the 18th's 6-ghati already IS Amavasya (not merely
        Chaturdashi building toward it) -- the observance must move to the 18th."""
        result = _sixghati_pullback(MAR_19, [MAR_18, MAR_19], tithi=15, paksha="Krishna")
        self.assertEqual(result, date(2026, 3, 18))

    def test_still_pulls_back_via_the_original_building_toward_shape(self):
        """The original (still valid) shape: previous day is strong for
        target-1 at both sunrise and 6-ghati. Must not regress."""
        day_snap = {
            "date": date(2026, 1, 2),
            "_sunrise_paksha": "Shukla", "_sunrise_tithi_in_paksha": 5,
            "paksha": "Shukla", "tithi_in_paksha": 6,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 6,  # weak: already Shashthi
        }
        prev_snap = {
            "date": date(2026, 1, 1),
            "_sunrise_paksha": "Shukla", "_sunrise_tithi_in_paksha": 4,
            "paksha": "Shukla", "tithi_in_paksha": 4,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 4,  # strong for Panchami-1
        }
        result = _sixghati_pullback(day_snap, [prev_snap, day_snap], tithi=5, paksha="Shukla")
        self.assertEqual(result, date(2026, 1, 1))

    def test_udaya_day_stands_when_strong(self):
        strong_snap = {
            "date": date(2026, 5, 1),
            "_sunrise_paksha": "Krishna", "_sunrise_tithi_in_paksha": 8,
            "paksha": "Krishna", "tithi_in_paksha": 8,
    "jain_paksha": "Krishna", "jain_tithi_in_paksha": 8,
        }
        result = _sixghati_pullback(strong_snap, [strong_snap], tithi=8, paksha="Krishna")
        self.assertEqual(result, date(2026, 5, 1))

    def test_does_not_pull_back_an_ordinary_non_paksha_ending_tithi(self):
        """The 'previous day already at target' shape is NOT sufficient on its own --
        it must be scoped to tithi 15 (Amavasya/Purnima). Counter-example found while
        validating the fix: Mahavir Janma Kalyanak (Chaitra Shukla Trayodashi, 13),
        2026: 30 Mar's Jain day-start already shows 13 (structurally identical shape
        to Mar 18/19's Amavasya), but the verified, correct day is the udaya day,
        31 Mar -- applying case 2 to any tithi silently moves this to the 30th."""
        mar_30 = {
            "date": date(2026, 3, 30),
            "_sunrise_paksha": "Shukla", "_sunrise_tithi_in_paksha": 12,
            "paksha": "Shukla", "tithi_in_paksha": 13,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 13,
        }
        mar_31 = {
            "date": date(2026, 3, 31),
            "_sunrise_paksha": "Shukla", "_sunrise_tithi_in_paksha": 13,
            "paksha": "Shukla", "tithi_in_paksha": 14,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 14,
        }
        result = _sixghati_pullback(mar_31, [mar_30, mar_31], tithi=13, paksha="Shukla")
        self.assertEqual(result, date(2026, 3, 31))

    def test_udaya_day_stands_on_a_run_of_weak_days_with_no_qualifying_previous_day(self):
        """Weak day whose previous day is neither building toward the target NOR
        already at it (e.g. previous day is two tithis back) -- no pullback."""
        day_snap = {
            "date": date(2026, 6, 10),
            "_sunrise_paksha": "Shukla", "_sunrise_tithi_in_paksha": 10,
            "paksha": "Shukla", "tithi_in_paksha": 11,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 11,  # weak
        }
        prev_snap = {
            "date": date(2026, 6, 9),
            "_sunrise_paksha": "Shukla", "_sunrise_tithi_in_paksha": 8,
            "paksha": "Shukla", "tithi_in_paksha": 9,
    "jain_paksha": "Shukla", "jain_tithi_in_paksha": 9,  # neither 9 nor 10
        }
        result = _sixghati_pullback(day_snap, [prev_snap, day_snap], tithi=10, paksha="Shukla")
        self.assertEqual(result, date(2026, 6, 10))


if __name__ == "__main__":
    unittest.main()
