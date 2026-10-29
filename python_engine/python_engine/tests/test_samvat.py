"""
tests/test_samvat.py — Unit tests for Vikram Samvat and Vira Nirvana Samvat calculations.

Tests the two pure functions get_vikram_samvat() and get_vira_nirvana_samvat()
using known festival dates for 2025:
  - Chaitra Shukla Pratipada (VS New Year): March 30, 2025
  - Diwali (Kartik Krishna Amavasya):       October 20, 2025
"""

import unittest
from datetime import date, timedelta

from panchang import (
    JAIN_TITHI_OFFSET_DAYS,
    find_chaitra_shukla_1,
    get_hindu_month,
    get_sunrise,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
    local_time_to_jd,
)

DELHI = (28.6139, 77.2090)
IST = 5.5


def _reference_month(day: date) -> str:
    """The Amanta month at the day's Jain reference instant (sunrise + 6 ghati)."""
    midnight = local_time_to_jd(day.year, day.month, day.day, 0.0, IST)
    return get_hindu_month(get_sunrise(midnight, *DELHI, 'modern') + JAIN_TITHI_OFFSET_DAYS)[0]


def _chaitra(year: int) -> date:
    return find_chaitra_shukla_1(year, *DELHI, IST)


class VikramSamvatTests(unittest.TestCase):
    """Vikram Samvat transitions at Chaitra Shukla Pratipada."""

    CHAITRA_2025 = date(2025, 3, 30)

    def test_january_before_chaitra_is_vs_2081(self):
        """January 2025 is before VS new year → year + 56 = 2081."""
        self.assertEqual(get_vikram_samvat(date(2025, 1, 1), self.CHAITRA_2025), 2081)

    def test_day_before_chaitra_is_vs_2081(self):
        """March 29, 2025 (day before VS new year) → 2081."""
        self.assertEqual(get_vikram_samvat(date(2025, 3, 29), self.CHAITRA_2025), 2081)

    def test_on_chaitra_shukla_1_is_vs_2082(self):
        """Chaitra Shukla 1 itself starts VS 2082 → year + 57 = 2082."""
        self.assertEqual(get_vikram_samvat(date(2025, 3, 30), self.CHAITRA_2025), 2082)

    def test_december_after_chaitra_is_vs_2082(self):
        """December 31, 2025 is after VS new year → 2082."""
        self.assertEqual(get_vikram_samvat(date(2025, 12, 31), self.CHAITRA_2025), 2082)


class ChaitraShuklaPratipadaTests(unittest.TestCase):
    """The Vikram new year: the first day from 1 March whose 6-ghati reference
    instant falls in Amanta Chaitra (Adhika Chaitra in a leap year)."""

    def test_2024_is_9_april_not_the_magha_amavasya_a_month_earlier(self):
        """Gudi Padwa 2024 was 9 April. The Amavasya of 10 March 2024 ends
        Amanta Magha; the first-Amavasya-after-1-March rule took it."""
        self.assertEqual(_chaitra(2024), date(2024, 4, 9))

    def test_a_two_day_amavasya_puts_the_new_year_after_both_days(self):
        """25 and 26 Mar 2028 are both Amavasya at the 6-ghati anchor."""
        self.assertEqual(_chaitra(2028), date(2028, 3, 27))

    def test_an_adhik_chaitra_year_turns_over_at_adhika_chaitra(self):
        """2029 has an Adhika Chaitra from 16 March; the samvat year begins
        with it (decided 2026-10-27), not with Nija Chaitra on 14 April."""
        self.assertEqual(_chaitra(2029), date(2029, 3, 16))

    def test_ordinary_years_are_unchanged(self):
        self.assertEqual(_chaitra(2025), date(2025, 3, 30))
        self.assertEqual(_chaitra(2026), date(2026, 3, 19))

    def test_every_year_turns_over_on_the_first_day_in_chaitra(self):
        for year in range(2016, 2041):
            with self.subTest(year=year):
                new_year = _chaitra(year)
                self.assertTrue(_reference_month(new_year).endswith('Chaitra'))
                self.assertEqual(_reference_month(new_year - timedelta(days=1)), 'Phalguna')


class ViraNirvanaSamvatTests(unittest.TestCase):
    """Vira Nirvana Samvat transitions the day after Diwali."""

    DIWALI_2025 = date(2025, 10, 20)

    def test_january_before_diwali_is_vns_2551(self):
        """January 2025 is before Diwali 2025 → year + 526 = 2551."""
        self.assertEqual(get_vira_nirvana_samvat(date(2025, 1, 1), self.DIWALI_2025), 2551)

    def test_on_diwali_day_is_vns_2551(self):
        """Diwali day itself is still VNS 2551 (new year starts the next day)."""
        self.assertEqual(get_vira_nirvana_samvat(date(2025, 10, 20), self.DIWALI_2025), 2551)

    def test_day_after_diwali_is_vns_2552(self):
        """Day after Diwali starts VNS 2552 → year + 527 = 2552."""
        self.assertEqual(get_vira_nirvana_samvat(date(2025, 10, 21), self.DIWALI_2025), 2552)

    def test_december_after_diwali_is_vns_2552(self):
        """December 31, 2025 is after Diwali → VNS 2552."""
        self.assertEqual(get_vira_nirvana_samvat(date(2025, 12, 31), self.DIWALI_2025), 2552)


if __name__ == '__main__':
    unittest.main()
