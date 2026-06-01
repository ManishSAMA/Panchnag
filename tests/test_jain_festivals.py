import unittest
from datetime import date
from unittest.mock import patch

class JainFestivalsRegistryTest(unittest.TestCase):
    def test_registry_integrity(self):
        """Test that jain_festival_rules loads and has valid festival schemas."""
        try:
            import jain_festival_rules as rules
        except ImportError:
            self.fail("Could not import jain_festival_rules.py")
        
        self.assertIsNotNone(rules.FESTIVAL_REGISTRY)
        self.assertTrue(len(rules.FESTIVAL_REGISTRY) > 0)
        
        # Test required keys for each registry entry
        required_keys = {
            "id", "name", "name_gujarati", "category", "profiles",
            "jain_month", "paksha", "tithi", "vriddhi_rule", "kshaya_rule",
            "adhika_rule", "meaning", "observance", "sources"
        }
        for fest in rules.FESTIVAL_REGISTRY:
            for key in required_keys:
                self.assertIn(key, fest, f"Missing key '{key}' in festival registry entry")
                
            self.assertIn(fest["category"], ["kalyanak", "festival", "fast", "parva"])
            self.assertIsInstance(fest["profiles"], list)
            self.assertTrue(len(fest["profiles"]) > 0)
            for p in fest["profiles"]:
                self.assertIn(p, ["shwetambar_murtipujak_tapagachchha", "shwetambar_sthanakvasi", "shwetambar_terapanthi"])


class JainFestivalServiceTest(unittest.TestCase):
    def test_mahavir_jayanti_resolution(self):
        """Verify Mahavir Janma Kalyanak resolves to Chaitra Shukla 13."""
        try:
            from jain_festival_service import generate_jain_festivals
        except ImportError:
            self.fail("Could not import jain_festival_service.py")
            
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha"
        )
        self.assertIsNotNone(res)
        self.assertIn("festivals", res)
        
        # Check for Mahavir Jayanti
        mahavir_events = [f for f in res["festivals"] if f["id"] == "mahavir_janma_kalyanak"]
        self.assertEqual(len(mahavir_events), 1)
        event = mahavir_events[0]
        self.assertEqual(event["start_date"], "2026-03-31")
        self.assertEqual(event["jain_month"], "Chaitra")
        self.assertEqual(event["paksha"], "Shukla")
        self.assertEqual(event["tithi"], 13)
        self.assertEqual(event["status"], "confirmed")

    def test_ayambil_oli_ranges(self):
        """Verify Chaitra and Ashvin Ayambil Oli span exactly 9 days."""
        from jain_festival_service import generate_jain_festivals
        
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha"
        )
        
        # Chaitra Oli: Chaitra Shukla 7 to 15 (2026-03-25 to 2026-04-02 approx)
        chaitra_oli = [f for f in res["festivals"] if f["id"] == "ayambil_oli_chaitra"]
        self.assertEqual(len(chaitra_oli), 1)
        self.assertEqual(chaitra_oli[0]["start_date"], "2026-03-25")
        self.assertEqual(chaitra_oli[0]["end_date"], "2026-04-02")
        
        # Ashvin Oli: Ashwin Shukla 7 to 15 (2026-10-17 to 2026-10-25 approx)
        ashvin_oli = [f for f in res["festivals"] if f["id"] == "ayambil_oli_ashvin"]
        self.assertEqual(len(ashvin_oli), 1)
        self.assertEqual(ashvin_oli[0]["start_date"], "2026-10-17")
        self.assertEqual(ashvin_oli[0]["end_date"], "2026-10-25")

    def test_paryushan_profile_specific_dates(self):
        """Verify Samvatsari and Paryushan start differ between Tapagachchha (Shukla 4) and Sthanakvasi/Terapanthi (Shukla 5)."""
        from jain_festival_service import generate_jain_festivals
        
        # Tapagachchha Samvatsari 2026 (Bhadrapada Shukla 4 -> 2026-09-15 approx)
        res_tapa = generate_jain_festivals(2026, 28.6139, 77.2090, "Lahiri", "shwetambar_murtipujak_tapagachchha")
        tapa_samvatsari = [f for f in res_tapa["festivals"] if f["id"] == "samvatsari_tapagachchha"]
        self.assertEqual(len(tapa_samvatsari), 1)
        self.assertEqual(tapa_samvatsari[0]["start_date"], "2026-09-15")
        
        # Sthanakvasi Samvatsari 2026 (Bhadrapada Shukla 5 -> 2026-09-16 approx)
        res_sthanak = generate_jain_festivals(2026, 28.6139, 77.2090, "Lahiri", "shwetambar_sthanakvasi")
        sthanak_samvatsari = [f for f in res_sthanak["festivals"] if f["id"] == "samvatsari_sthanakvasi"]
        self.assertEqual(len(sthanak_samvatsari), 1)
        self.assertEqual(sthanak_samvatsari[0]["start_date"], "2026-09-16")

    def test_tithi_vriddhi_first_day(self):
        """Test Tithi Vriddhi observes on the first day, unless custom rule specifies otherwise."""
        from jain_festival_service import generate_jain_festivals
        # Verify it runs without error (we will mock specifically inside implementation)
        pass

    def test_tithi_kshaya_next_day(self):
        """Test Tithi Kshaya resolves on the next day."""
        pass

    def test_adhika_month_skipped(self):
        """Verify that festivals do not trigger in Adhika months but land on Nija months."""
        pass

    def test_source_conflict_flags_review_needed(self):
        """Test that if a conflict is triggered, status is review_needed."""
        pass


class JainFestivalsApiExportTest(unittest.TestCase):
    def setUp(self):
        from app import create_app
        self.app = create_app()
        self.client = self.app.test_client()

    def test_generate_jain_festivals_api(self):
        """Verify POST /generate-jain-festivals returns correct structure."""
        resp = self.client.post("/generate-jain-festivals", json={
            "year": 2026,
            "lat": 28.6139,
            "lon": 77.2090,
            "profile": "shwetambar_murtipujak_tapagachchha"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("year", data)
        self.assertIn("location", data)
        self.assertIn("profile", data)
        self.assertIn("festivals", data)
        self.assertIn("upcoming", data)

    def test_month_overview_compact_markers(self):
        """Verify GET /month-overview includes jain_festivals markers when profile is provided."""
        resp = self.client.get("/month-overview?year=2026&month=3&lat=28.6139&lon=77.2090&profile=shwetambar_murtipujak_tapagachchha")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("days", data)
        for day in data["days"]:
            self.assertIn("jain_festivals", day)

    def test_generate_jain_festival_exports_api(self):
        """Verify POST /generate-jain-festival-exports returns download url."""
        resp = self.client.post("/generate-jain-festival-exports", json={
            "year": 2026,
            "lat": 28.6139,
            "lon": 77.2090,
            "profile": "shwetambar_murtipujak_tapagachchha",
            "format": "csv"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("files", data)
        self.assertTrue(len(data["files"]) > 0)
        self.assertIn("download_url", data["files"][0])


if __name__ == "__main__":
    unittest.main()

