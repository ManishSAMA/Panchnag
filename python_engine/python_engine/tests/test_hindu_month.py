import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from astronomy import get_julian_date
from panchang import get_hindu_month, find_sankrantis_in_range


def _noon_jd(year: int, month: int, day: int) -> float:
    return get_julian_date(year, month, day, 12.0)


class HinduMonthGroundTruthTest(unittest.TestCase):
    def _assert_month(
        self, year: int, month: int, day: int,
        expected_name: str, expected_adhika: bool,
    ) -> None:
        jd = _noon_jd(year, month, day)
        name, _common, is_adhika = get_hindu_month(jd)
        self.assertEqual(name, expected_name,
            f"{year}-{month:02d}-{day:02d}: expected month '{expected_name}', got '{name}'")
        self.assertEqual(is_adhika, expected_adhika,
            f"{year}-{month:02d}-{day:02d}: expected is_adhika={expected_adhika}, got {is_adhika}")

    def test_chaitra_2025_04_01(self):
        self._assert_month(2025, 4, 1, "Chaitra", False)

    def test_vaishakha_2025_05_01(self):
        self._assert_month(2025, 5, 1, "Vaishakha", False)

    def test_ashadha_2025_07_24(self):
        # July 24 is the day of new moon (19:12 UTC); noon UTC is still in Ashadha
        self._assert_month(2025, 7, 24, "Ashadha", False)

    def test_adhika_shravana_2023_07_25(self):
        # 2023 had Adhika Shravana (July 17 – August 16, 2023): no Sankranti in that month
        self._assert_month(2023, 7, 25, "Adhika Shravana", True)

    def test_shravana_after_adhika_2023_08_25(self):
        # Real Shravana after the 2023 Adhika month
        self._assert_month(2023, 8, 25, "Shravana", False)

    def test_bhadrapada_2025_09_20(self):
        self._assert_month(2025, 9, 20, "Bhadrapada", False)

    def test_pausha_2024_01_15(self):
        self._assert_month(2024, 1, 15, "Pausha", False)

    def test_phalguna_2024_03_10(self):
        self._assert_month(2024, 3, 10, "Phalguna", False)


class SankrantiDetectionTest(unittest.TestCase):
    def test_mesha_sankranti_detected_near_2025_04_14(self):
        start = _noon_jd(2025, 4, 12)
        end = _noon_jd(2025, 4, 16)
        sankrantis = find_sankrantis_in_range(start, end)
        self.assertIn(0, sankrantis,
            f"Expected Mesha (sign 0) Sankranti in range, got {sankrantis}")


if __name__ == '__main__':
    unittest.main()
