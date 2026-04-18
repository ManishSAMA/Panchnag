import unittest

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

    def test_choghadiya_saturday_night_starts_with_labh(self):
        # April 18 2026 is Saturday — Saturday night Choghadiya starts with Labh
        response = self.client.post(
            "/choghadiya",
            json={"date": "2026-04-18", "lat": 26.9124, "lon": 75.7873},
        )
        data = response.get_json()
        first_night = next(s for s in data["slots"] if s["period"] == "night")
        self.assertEqual(first_night["name"], "Labh")

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
