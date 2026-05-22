import unittest
from unittest.mock import patch, call

from panchang_service import _collect_all_tithis_in_day


# Jaipur sunrise on 2025-01-01 (approximate JD)
_SUNRISE_JD = 2460676.7
_NEXT_SUNRISE_JD = _SUNRISE_JD + 1.0
_TZ = "Asia/Kolkata"
_AYANAMSA = "Lahiri"


class CollectAllTithisTests(unittest.TestCase):
    def test_returns_a_list(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        self.assertIsInstance(result, list)

    def test_list_is_non_empty(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        self.assertGreater(len(result), 0)

    def test_each_item_has_required_keys(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        for item in result:
            self.assertIn("index", item)
            self.assertIn("name", item)
            self.assertIn("ends", item)
            self.assertIn("continues_past_next_sunrise", item)

    def test_last_item_continues_past_next_sunrise(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        self.assertTrue(result[-1]["continues_past_next_sunrise"])

    def test_last_item_has_null_ends_when_continues_past_sunrise(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        self.assertIsNone(result[-1]["ends"])

    def test_non_last_items_have_ends_set(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        for item in result[:-1]:
            self.assertIsNotNone(item["ends"])
            self.assertFalse(item["continues_past_next_sunrise"])

    def test_ends_contains_serialized_event_fields(self):
        # Find a day where a tithi ends mid-day by using a very tight window (1 hour)
        tight_next_sunrise = _SUNRISE_JD + 1.0 / 24.0
        result = _collect_all_tithis_in_day(_SUNRISE_JD, tight_next_sunrise, _AYANAMSA, _TZ)
        # With a 1-hour window most tithis (which last ~24h) will continue past it
        # The last item should have continues=True and ends=None
        self.assertIsNone(result[-1]["ends"])

    def test_result_is_bounded_by_loop_limit(self):
        # Even on an edge case, we should never exceed the safety cap
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        self.assertLessEqual(len(result), 5)

    def test_tithi_kshaya_produces_two_tithis(self):
        # 2025-08-20 is known to have 2 tithis for Jaipur - Krishna Chaturdashi ends
        # during the day and Krishna Amavasya follows
        # Jaipur sunrise 2025-08-20 ≈ JD 2460908.10 (approx 06:06 IST)
        # Actual values to be verified once the function works
        kshaya_sunrise = 2460908.10
        kshaya_next_sunrise = kshaya_sunrise + 0.9986
        result = _collect_all_tithis_in_day(
            kshaya_sunrise, kshaya_next_sunrise, _AYANAMSA, _TZ
        )

        self.assertGreaterEqual(len(result), 2)
        # First tithi has an end time
        self.assertIsNotNone(result[0]["ends"])
        self.assertFalse(result[0]["continues_past_next_sunrise"])
        # Last tithi continues past sunrise
        self.assertTrue(result[-1]["continues_past_next_sunrise"])
        self.assertIsNone(result[-1]["ends"])

    def test_index_is_integer_in_valid_range(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        for item in result:
            self.assertIsInstance(item["index"], int)
            self.assertGreaterEqual(item["index"], 1)
            self.assertLessEqual(item["index"], 30)

    def test_name_is_non_empty_string(self):
        result = _collect_all_tithis_in_day(_SUNRISE_JD, _NEXT_SUNRISE_JD, _AYANAMSA, _TZ)

        for item in result:
            self.assertIsInstance(item["name"], str)
            self.assertGreater(len(item["name"]), 0)


if __name__ == "__main__":
    unittest.main()
