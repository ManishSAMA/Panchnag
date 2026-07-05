"""
tests/test_samvat.py — Unit tests for Vikram Samvat and Vira Nirvana Samvat calculations.

Tests the two pure functions get_vikram_samvat() and get_vira_nirvana_samvat()
using known festival dates for 2025:
  - Chaitra Shukla Pratipada (VS New Year): March 30, 2025
  - Diwali (Kartik Krishna Amavasya):       October 20, 2025
"""

import unittest
from datetime import date

from panchang import get_vikram_samvat, get_vira_nirvana_samvat


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
