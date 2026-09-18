"""RED test: /month-overview must include sunrise_time and sunset_time per day.

Fails until app.py's month_overview() adds those fields to day_payload.
"""
import re
import unittest
from unittest.mock import MagicMock, patch

from app import app

HH_MM = re.compile(r"^\d{2}:\d{2}$")

DUMMY_RESULT = {
    "panchang": {
        "tithi": [
            {
                "name": "Pratipada",
                "index": 1,
                "ends": {"time": "15:30:00"},
                "paksha": "Shukla",
            }
        ],
        "nakshatra": {"name": "Ashwini", "index": 1, "ends": {"time": "18:00:00"}},
        "vara": {"name": "Monday", "index": 1},
        "hindu_month": {"name": "Chaitra", "index": 1},
        "vikram_samvat": 2081,
    },
    "events": {
        "sunrise": {"time": "06:15:00"},
        "sunset": {"time": "18:45:00"},
    },
}


class TestMonthOverviewSunriseSunset(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("app.generate_location_panchang", return_value=DUMMY_RESULT)
    @patch("app.resolve_location")
    def test_every_day_has_sunrise_and_sunset_fields(self, mock_resolve, mock_panchang):
        loc = MagicMock()
        loc.lat, loc.lon, loc.name, loc.timezone = 23.0225, 72.5714, "Ahmedabad", "Asia/Kolkata"
        mock_resolve.return_value = loc

        response = self.client.get(
            "/month-overview?year=2025&month=6&lat=23.0225&lon=72.5714"
        )
        self.assertEqual(response.status_code, 200)

        days = response.get_json()["days"]
        self.assertGreater(len(days), 0)

        for day in days:
            self.assertIn(
                "sunrise_time", day,
                f"'sunrise_time' missing from day {day.get('date')}",
            )
            self.assertIn(
                "sunset_time", day,
                f"'sunset_time' missing from day {day.get('date')}",
            )
            # Non-empty values must match HH:MM format
            if day["sunrise_time"]:
                self.assertRegex(
                    day["sunrise_time"], HH_MM,
                    f"sunrise_time '{day['sunrise_time']}' is not HH:MM",
                )
            if day["sunset_time"]:
                self.assertRegex(
                    day["sunset_time"], HH_MM,
                    f"sunset_time '{day['sunset_time']}' is not HH:MM",
                )

    @patch("app.generate_location_panchang", return_value=DUMMY_RESULT)
    @patch("app.resolve_location")
    def test_sunrise_sunset_values_match_panchang_events(self, mock_resolve, mock_panchang):
        loc = MagicMock()
        loc.lat, loc.lon, loc.name, loc.timezone = 23.0225, 72.5714, "Ahmedabad", "Asia/Kolkata"
        mock_resolve.return_value = loc

        response = self.client.get(
            "/month-overview?year=2025&month=6&lat=23.0225&lon=72.5714"
        )
        days = response.get_json()["days"]

        # All days use the same mock so every day should report 06:15 / 18:45
        for day in days:
            self.assertEqual(day["sunrise_time"], "06:15", f"day {day['date']}")
            self.assertEqual(day["sunset_time"], "18:45", f"day {day['date']}")


if __name__ == "__main__":
    unittest.main()
