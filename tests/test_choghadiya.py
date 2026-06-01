import unittest
from datetime import datetime

from app import app


class ChoghadiyaApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_choghadiya_returns_16_slots_for_valid_request(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("slots", data)
        self.assertEqual(len(data["slots"]), 16)

    def test_choghadiya_has_8_day_and_8_night_slots(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        data = response.get_json()
        day_slots = [s for s in data["slots"] if s["period"] == "day"]
        night_slots = [s for s in data["slots"] if s["period"] == "night"]
        self.assertEqual(len(day_slots), 8)
        self.assertEqual(len(night_slots), 8)

    def test_choghadiya_saturday_day_starts_with_kaal(self):
        # April 18 2026 is Saturday — Saturday day Choghadiya starts with Kaal
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        data = response.get_json()
        first_day = next(s for s in data["slots"] if s["period"] == "day")
        self.assertEqual(first_day["name"], "Kaal")

    def test_choghadiya_saturday_day_sequence_matches_reference_table(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-05-23", "lat": 28.6139, "lon": 77.2090},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        day_names = [s["name"] for s in data["slots"] if s["period"] == "day"]

        self.assertEqual(
            day_names,
            ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"],
        )

    def test_choghadiya_saturday_night_sequence_matches_reference_table(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        data = response.get_json()
        night_names = [s["name"] for s in data["slots"] if s["period"] == "night"]

        self.assertEqual(
            night_names,
            ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],
        )

    def test_choghadiya_sunday_night_sequence_matches_reference_table(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-05-24", "lat": 28.4595, "lon": 77.0266},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        night_names = [s["name"] for s in data["slots"] if s["period"] == "night"]

        self.assertEqual(
            night_names,
            ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],
        )

    def test_choghadiya_friday_delhi_matches_expected_sequence(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-05-22", "lat": 28.6139, "lon": 77.2090},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        first_day = next(s for s in data["slots"] if s["period"] == "day")
        self.assertEqual(first_day["name"], "Char")

        fourth_day = [s for s in data["slots"] if s["period"] == "day"][3]
        self.assertEqual(fourth_day["name"], "Kaal")

        night_names = [s["name"] for s in data["slots"] if s["period"] == "night"]
        self.assertEqual(
            night_names,
            ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog"],
        )

        sunrise = datetime.strptime(data["sunrise"], "%H:%M")
        self.assertEqual(sunrise.hour, 5)
        self.assertIn(sunrise.minute, (27, 28, 29, 30))

    def test_choghadiya_delhi_uses_equal_day_and_equal_night_slot_durations(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-05-22", "lat": 28.6139, "lon": 77.2090},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        day_slots = [s for s in data["slots"] if s["period"] == "day"]
        night_slots = [s for s in data["slots"] if s["period"] == "night"]

        self.assertAlmostEqual(data["day_slot_duration_minutes"], 102.7, places=1)
        self.assertTrue(all(s["duration_minutes"] == day_slots[0]["duration_minutes"] for s in day_slots))
        self.assertTrue(all(s["duration_minutes"] == night_slots[0]["duration_minutes"] for s in night_slots))
        self.assertNotEqual(day_slots[0]["duration_minutes"], night_slots[0]["duration_minutes"])
        self.assertEqual(day_slots[0]["name"], "Char")
        self.assertEqual(day_slots[0]["start_time"], data["sunrise"])
        self.assertEqual(day_slots[3]["name"], "Kaal")
        self.assertIn(day_slots[3]["start_time"], ("10:35", "10:36"))
        self.assertEqual(day_slots[4]["name"], "Shubh")
        self.assertEqual(night_slots[0]["name"], "Rog")
        self.assertEqual(night_slots[0]["start_time"], data["sunset"])

    def test_choghadiya_includes_utc_and_local_timezone_aware_boundaries(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-05-22", "lat": 28.6139, "lon": 77.2090},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        slot = data["slots"][0]

        self.assertEqual(data["timezone"], "Asia/Kolkata")
        self.assertTrue(data["sunrise_utc"].endswith("+00:00"))
        self.assertTrue(slot["start_utc"].endswith("+00:00"))
        self.assertIn("+05:30", slot["start_local"])

    def test_choghadiya_night_slots_after_midnight_include_next_calendar_date(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-05-22", "lat": 28.6139, "lon": 77.2090},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        night_slots = [s for s in data["slots"] if s["period"] == "night"]

        after_midnight = next(s for s in night_slots if s["start_local"].startswith("2026-05-23"))
        self.assertIn("May 23", after_midnight["start_label"])

    def test_choghadiya_returns_400_when_sun_does_not_rise_or_set(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-06-21", "lat": 78.2232, "lon": 15.6469},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("sunrise or sunset", response.get_json()["error"].lower())

    def test_choghadiya_slot_has_required_fields(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        data = response.get_json()
        slot = data["slots"][0]
        for field in ("name", "meaning", "nature", "start_time", "end_time", "period"):
            self.assertIn(field, slot)

    def test_choghadiya_response_includes_sunrise_and_sunset(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        data = response.get_json()
        self.assertIn("sunrise", data)
        self.assertIn("sunset", data)

    def test_choghadiya_returns_400_for_missing_date(self):
        response = self.client.post(
            "/choghadiya",
            json={"lat": 26.9124, "lon": 75.7873},
        )
        self.assertEqual(response.status_code, 400)

    def test_choghadiya_returns_400_for_missing_coordinates(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18"},
        )
        self.assertEqual(response.status_code, 400)

    def test_choghadiya_returns_400_for_invalid_date_format(self):
        response = self.client.post(
            "/choghadiya",
            json={"date": "18-04-2026", "lat": 26.9124, "lon": 75.7873},
        )
        self.assertEqual(response.status_code, 400)
