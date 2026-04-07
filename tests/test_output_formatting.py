import unittest

from export import apply_element_continuity_formatting, strip_internal_output_fields


class OutputFormattingTests(unittest.TestCase):
    def test_repeating_elements_only_show_end_info_on_last_day(self):
        rows = [
            {
                "Date": "2026-01-01",
                "Tithi": "Ekadashi",
                "Nakshatra": "Rohini",
                "Yoga": "Shobhana",
                "Jain_Tithi": "Shukla Dwitiya",
                "__Tithi_End_JD": 2461043.9,
                "__Nakshatra_End_JD": 2461043.8,
                "__Yoga_End_JD": 2461043.7,
            },
            {
                "Date": "2026-01-02",
                "Tithi": "Ekadashi",
                "Nakshatra": "Rohini",
                "Yoga": "Atiganda",
                "Jain_Tithi": "Shukla Tritiya",
                "__Tithi_End_JD": 2461044.1,
                "__Nakshatra_End_JD": 2461044.2,
                "__Yoga_End_JD": 2461044.3,
            },
            {
                "Date": "2026-01-03",
                "Tithi": "Dwadashi",
                "Nakshatra": "Mrigashirsha",
                "Yoga": "Atiganda",
                "Jain_Tithi": "Shukla Chaturthi",
                "__Tithi_End_JD": 2461045.1,
                "__Nakshatra_End_JD": 2461045.2,
                "__Yoga_End_JD": 2461045.3,
            },
        ]

        formatted = apply_element_continuity_formatting(rows, tz_offset=5.5)

        self.assertEqual(formatted[0]["Tithi"], "Ekadashi")
        self.assertEqual(formatted[0]["__Tithi_Is_First_Occurrence"], True)
        self.assertEqual(formatted[0]["__Tithi_Is_Last_Occurrence"], False)
        self.assertEqual(formatted[1]["__Tithi_Is_Continuation"], True)
        self.assertEqual(formatted[1]["__Tithi_Is_Last_Occurrence"], True)

        self.assertEqual(formatted[0]["Nakshatra"], "Rohini")
        self.assertEqual(formatted[1]["__Nakshatra_Is_Continuation"], True)
        self.assertEqual(formatted[1]["__Nakshatra_Is_Last_Occurrence"], True)

        self.assertEqual(formatted[0]["__Yoga_Is_First_Occurrence"], True)
        self.assertEqual(formatted[0]["__Yoga_Is_Last_Occurrence"], True)
        self.assertEqual(formatted[1]["Yoga"], "Atiganda")
        self.assertEqual(formatted[1]["__Yoga_Is_First_Occurrence"], True)
        self.assertEqual(formatted[1]["__Yoga_Is_Last_Occurrence"], False)
        self.assertEqual(formatted[2]["__Yoga_Is_Continuation"], True)
        self.assertEqual(formatted[2]["__Yoga_Is_Last_Occurrence"], True)

    def test_single_day_occurrence_keeps_end_info(self):
        rows = [{
            "Date": "2026-02-01",
            "Tithi": "Panchami",
            "Nakshatra": "Hasta",
            "Yoga": "Dhruva",
            "Jain_Tithi": "Shukla Panchami",
            "__Tithi_End_JD": 2461073.2,
            "__Nakshatra_End_JD": 2461073.3,
            "__Yoga_End_JD": 2461073.4,
        }]

        formatted = apply_element_continuity_formatting(rows, tz_offset=5.5)

        self.assertEqual(formatted[0]["__Tithi_Is_First_Occurrence"], True)
        self.assertEqual(formatted[0]["__Tithi_Is_Last_Occurrence"], True)
        self.assertEqual(formatted[0]["__Nakshatra_Is_First_Occurrence"], True)
        self.assertEqual(formatted[0]["__Nakshatra_Is_Last_Occurrence"], True)
        self.assertEqual(formatted[0]["__Yoga_Is_First_Occurrence"], True)
        self.assertEqual(formatted[0]["__Yoga_Is_Last_Occurrence"], True)
        self.assertEqual(formatted[0]["Jain_Tithi_PDF"], "Shukla Panchami")

    def test_strip_internal_fields_removes_helper_keys(self):
        rows = apply_element_continuity_formatting([{
            "Date": "2026-02-01",
            "Tithi": "Panchami",
            "Nakshatra": "Hasta",
            "Yoga": "Dhruva",
            "Jain_Tithi": "Shukla Panchami",
            "__Tithi_End_JD": 2461073.2,
            "__Nakshatra_End_JD": 2461073.3,
            "__Yoga_End_JD": 2461073.4,
        }], tz_offset=5.5)

        cleaned = strip_internal_output_fields(rows)

        self.assertEqual(len(cleaned), 1)
        self.assertNotIn("__Tithi_End_JD", cleaned[0])
        self.assertNotIn("Jain_Tithi_PDF", cleaned[0])


if __name__ == "__main__":
    unittest.main()
