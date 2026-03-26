import unittest
from unittest.mock import patch

from app import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("app.search_locations")
    def test_search_location_endpoint(self, mock_search_locations):
        mock_search_locations.return_value = [
            {
                "display_name": "Jaipur, Rajasthan, India",
                "lat": 26.9124,
                "lon": 75.7873,
            }
        ]

        response = self.client.get("/search-location?q=jaipur")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["results"][0]["display_name"], "Jaipur, Rajasthan, India")

    @patch("app.geocode_city")
    def test_get_coordinates_endpoint(self, mock_geocode_city):
        mock_geocode_city.return_value = {
            "display_name": "Mumbai, Maharashtra, India",
            "lat": 19.0760,
            "lon": 72.8777,
        }

        response = self.client.get("/get-coordinates?city=Mumbai")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["lat"], 19.0760)
        self.assertEqual(payload["lon"], 72.8777)

    def test_generate_panchang_with_manual_coordinates(self):
        response = self.client.post(
            "/generate-panchang",
            json={
                "date": "2025-01-01",
                "lat": 26.9124,
                "lon": 75.7873,
                "ayanamsa": "Lahiri",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["date"], "2025-01-01")
        self.assertEqual(payload["rules"]["primary_day_rule"], "udaya_tithi")
        self.assertIn("sunrise", payload["events"])

    @patch("app.generate_location_panchang")
    def test_generate_panchang_uses_city_if_coordinates_are_missing(self, mock_generate):
        mock_generate.return_value = {"ok": True}

        response = self.client.post(
            "/generate-panchang",
            json={
                "date": "2025-01-01",
                "city": "Jaipur",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True})
        mock_generate.assert_called_once()
        _, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["city"], "Jaipur")
        self.assertIsNone(kwargs["lat"])
        self.assertIsNone(kwargs["lon"])


if __name__ == "__main__":
    unittest.main()
