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
        self.assertIn("jain_tithi", payload["panchang"])

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

    def test_generate_panchang_requires_complete_coordinates(self):
        response = self.client.post(
            "/generate-panchang",
            json={
                "date": "2025-01-01",
                "lat": 26.9124,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Latitude and longitude must be provided together.",
        )

    def test_generate_panchang_requires_location_input(self):
        response = self.client.post(
            "/generate-panchang",
            json={
                "date": "2025-01-01",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Provide either a city name or both latitude and longitude.",
        )

    @patch("app.generate_year_range_exports")
    def test_generate_range_endpoint_returns_downloads(self, mock_generate_range):
        mock_generate_range.return_value = {
            "location": {
                "name": "Jaipur, Rajasthan, India",
                "lat": 26.9124,
                "lon": 75.7873,
                "timezone": "Asia/Kolkata",
                "timezone_export_label": "IST",
                "timezone_export_offset_hours": 5.5,
            },
            "start_year": 2025,
            "end_year": 2026,
            "format": "csv",
            "monthly": False,
            "workers": 1,
            "rows_generated": 730,
            "files": [
                type("GeneratedFile", (), {"name": "panchang_2025_2026.csv", "path": "/tmp/panchang_2025_2026.csv"})()
            ],
        }

        response = self.client.post(
            "/generate-range-panchang",
            json={
                "start_year": 2025,
                "end_year": 2026,
                "lat": 26.9124,
                "lon": 75.7873,
                "format": "csv",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["rows_generated"], 730)
        self.assertEqual(payload["files"][0]["name"], "panchang_2025_2026.csv")
        self.assertTrue(payload["files"][0]["download_url"].startswith("/downloads/"))

    def test_generate_range_endpoint_validates_years(self):
        response = self.client.post(
            "/generate-range-panchang",
            json={
                "start_year": 2026,
                "end_year": 2025,
                "lat": 26.9124,
                "lon": 75.7873,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "start_year must be less than or equal to end_year.",
        )

    @patch("app.generate_pdf_export")
    def test_generate_pdf_endpoint_returns_download(self, mock_generate_pdf):
        mock_generate_pdf.return_value = {
            "year": 2025,
            "ayanamsa": "Lahiri",
            "location": {
                "name": "Jaipur, Rajasthan, India",
                "lat": 26.9124,
                "lon": 75.7873,
                "timezone": "Asia/Kolkata",
                "timezone_export_label": "IST",
                "timezone_export_offset_hours": 5.5,
            },
            "file": {
                "name": "panchang_2025.pdf",
                "path": "/tmp/panchang_2025.pdf",
            },
        }

        response = self.client.post(
            "/generate-pdf-panchang",
            json={
                "year": 2025,
                "lat": 26.9124,
                "lon": 75.7873,
                "ayanamsa": "Lahiri",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["year"], 2025)
        self.assertEqual(payload["file"]["name"], "panchang_2025.pdf")
        self.assertTrue(payload["file"]["download_url"].startswith("/downloads/"))

    def test_generate_pdf_endpoint_requires_year(self):
        response = self.client.post(
            "/generate-pdf-panchang",
            json={
                "lat": 26.9124,
                "lon": 75.7873,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Missing required field: year")


if __name__ == "__main__":
    unittest.main()
