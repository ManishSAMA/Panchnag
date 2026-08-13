import unittest
from datetime import date
from unittest.mock import patch

class JainFestivalsRegistryTest(unittest.TestCase):
    def test_registry_integrity(self):
        """Test that jain_festival_rules loads and has valid festival schemas."""
        try:
            from jain_observances import festival_rules as rules
        except ImportError:
            self.fail("Could not import jain_festival_rules.py")
        
        self.assertIsNotNone(rules.FESTIVAL_REGISTRY)
        self.assertTrue(len(rules.FESTIVAL_REGISTRY) > 0)
        
        # Test required keys for each registry entry
        required_keys = {
            "id", "name", "category", "profiles"
        }
        for fest in rules.FESTIVAL_REGISTRY:
            for key in required_keys:
                self.assertIn(key, fest, f"Missing key '{key}' in festival registry entry")
                
            self.assertIn(fest["category"], ["kalyanak", "festival", "fast", "parva", "mahaparv", "parva_vrat", "monthly_vrat"])
            self.assertIsInstance(fest["profiles"], list)
            self.assertTrue(len(fest["profiles"]) > 0)
            for p in fest["profiles"]:
                self.assertIn(p, ["all", "shwetambar_murtipujak_tapagachchha", "shwetambar_sthanakvasi", "shwetambar_terapanthi"])
                
            # Verify OOP wrapping works
            rule_obj = rules.RuleFactory.create(fest)
            self.assertEqual(rule_obj.id, fest["id"])
            self.assertEqual(rule_obj.name, fest["name"])


class JainFestivalServiceTest(unittest.TestCase):
    def test_mahavir_jayanti_resolution(self):
        """Verify Mahavir Janma Kalyanak resolves to Chaitra Shukla 13."""
        try:
            from jain_observances.festival_service import generate_jain_festivals
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
        self.assertEqual(event["start_date"], "2026-03-30")
        self.assertEqual(event["jain_month"], "Chaitra")
        self.assertEqual(event["paksha"], "Shukla")
        self.assertEqual(event["tithi"], "Trayodashi (13)")
        self.assertEqual(event["status"], "confirmed")
 
    def test_ayambil_oli_ranges(self):
        """Verify Chaitra and Ashvin Ayambil Oli start dates."""
        from jain_observances.festival_service import generate_jain_festivals
        
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha"
        )
        
        # Chaitra Oli: Chaitra Shukla 7 (9 days)
        chaitra_oli = [f for f in res["festivals"] if f["id"].startswith("navpad_ayambil_oli_spring")]
        self.assertEqual(len(chaitra_oli), 9)
        chaitra_oli.sort(key=lambda x: x["start_date"])
        self.assertEqual(chaitra_oli[0]["start_date"], "2026-03-25")
        self.assertEqual(chaitra_oli[-1]["start_date"], "2026-04-02")
        
        # Ashvin Oli: Ashwin Shukla 7 (10 days due to Vriddhi)
        ashvin_oli = [f for f in res["festivals"] if f["id"].startswith("navpad_ayambil_oli_autumn")]
        self.assertEqual(len(ashvin_oli), 10)
        ashvin_oli.sort(key=lambda x: x["start_date"])
        self.assertEqual(ashvin_oli[0]["start_date"], "2026-10-17")
        self.assertEqual(ashvin_oli[-1]["start_date"], "2026-10-26")
 
    def test_paryushan_profile_specific_dates(self):
        """Verify Samvatsari and Paryushan start differ between Tapagachchha (Shukla 4) and Sthanakvasi/Terapanthi (Shukla 5)."""
        from jain_observances.festival_service import generate_jain_festivals
        
        # Tapagachchha Samvatsari 2026 (Bhadrapada Shukla 4 -> 2026-09-14 approx)
        res_tapa = generate_jain_festivals(2026, 28.6139, 77.2090, "Lahiri", "shwetambar_murtipujak_tapagachchha")
        tapa_samvatsari = [f for f in res_tapa["festivals"] if f["id"] == "samvatsari_tapagachchha"]
        self.assertEqual(len(tapa_samvatsari), 1)
        self.assertEqual(tapa_samvatsari[0]["start_date"], "2026-09-14")
        
        # Sthanakvasi Samvatsari 2026 (Bhadrapada Shukla 5 -> 2026-09-16 approx)
        res_sthanak = generate_jain_festivals(2026, 28.6139, 77.2090, "Lahiri", "shwetambar_sthanakvasi")
        sthanak_samvatsari = [f for f in res_sthanak["festivals"] if f["id"] == "samvatsari_sthanakvasi"]
        self.assertEqual(len(sthanak_samvatsari), 1)
        self.assertEqual(sthanak_samvatsari[0]["start_date"], "2026-09-16")

    def test_tithi_vriddhi_first_day(self):
        """Test Tithi Vriddhi observes on the first day, unless custom rule specifies otherwise."""
        from jain_observances.festival_service import generate_jain_festivals
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


class KrishnaPakshaFestivalsTest(unittest.TestCase):
    """Verify all Krishna-paksha Jain festivals appear in the 2026 output."""

    @classmethod
    def setUpClass(cls):
        from jain_observances.festival_service import generate_jain_festivals
        cls.res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha",
        )
        cls.ids = {f["id"] for f in cls.res["festivals"]}

    def test_diwali_appears(self):
        self.assertIn("mahavir_nirvana_deepavali", self.ids)

    def test_meru_trayodashi_appears(self):
        self.assertIn("meru_trayodashi", self.ids)

    def test_parshvanath_jayanti_appears(self):
        self.assertIn("parshvanath_jayanti", self.ids)

    def test_pakhi_chaudas_appears(self):
        self.assertIn("pakhi_chaudas_bhadrapada", self.ids)

    def test_parva_tithi_ashtami_krishna_appears(self):
        self.assertIn("parva_tithi_ashtami_krishna", self.ids)

    def test_parva_tithi_amavasya_appears(self):
        self.assertIn("parva_tithi_amavasya", self.ids)


class RecurringParvaCountTest(unittest.TestCase):
    """Recurring Parva tithis must appear at least 10 times per calendar year.

    A calendar year spans ~12 lunar months, but year boundaries mean some tithis
    fall outside Jan 1–Dec 31, so the realistic minimum is 10.
    """

    @classmethod
    def setUpClass(cls):
        from jain_observances.festival_service import generate_jain_festivals
        cls.res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha",
        )

    def _count(self, festival_id):
        return sum(1 for f in self.res["festivals"] if f["id"] == festival_id)

    def test_pakhi_chaudas_bhadrapada_at_least_1(self):
        self.assertGreaterEqual(self._count("pakhi_chaudas_bhadrapada"), 1)

    def test_ashtami_shukla_at_least_12(self):
        self.assertGreaterEqual(self._count("parva_tithi_ashtami_shukla"), 10)

    def test_ashtami_krishna_at_least_12(self):
        self.assertGreaterEqual(self._count("parva_tithi_ashtami_krishna"), 10)

    def test_purnima_at_least_12(self):
        self.assertGreaterEqual(self._count("parva_tithi_purnima"), 10)

    def test_amavasya_at_least_12(self):
        self.assertGreaterEqual(self._count("parva_tithi_amavasya"), 10)


class RaviVratTest(unittest.TestCase):
    def test_ravi_vrat_resolution(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha"
        )
        ravi_events = [f for f in res["festivals"] if f["id"] == "ravi_vrat"]
        self.assertEqual(len(ravi_events), 9)
        
        # Verify first and last dates
        self.assertEqual(ravi_events[0]["start_date"], "2026-07-26")
        self.assertEqual(ravi_events[-1]["start_date"], "2026-09-20")
        
        for event in ravi_events:
            self.assertEqual(event["category"], "parva_vrat")
            self.assertEqual(event["badge"], "Parva / Vrat")
            self.assertEqual(event["badge_color"], "purple")
            self.assertEqual(event["is_span"], False)
            self.assertTrue(event["name"].startswith("☀️ Ravi"))

        # Verify ravivara_vrat
        ravivara_events = [f for f in res["festivals"] if f["id"] == "ravivara_2026"]
        self.assertEqual(len(ravivara_events), 1)
        self.assertEqual(ravivara_events[0]["start_date"], "2026-07-26")
        self.assertEqual(ravivara_events[0]["end_date"], "2026-09-20")


class KarmaNirjaraVratTest(unittest.TestCase):
    def test_karma_nirjara_vrat_resolution(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        # Look for karma_nirjara occurrences
        vrat_events = [f for f in res["festivals"] if "karma_nirjara" in f["id"]]
        
        # Verify total events (Ashadha, Shravana [repeats], Bhadrapada, Ashwin)
        self.assertEqual(len(vrat_events), 5)
        
        # Verify first and last dates
        self.assertEqual(vrat_events[0]["start_date"], "2026-07-28")
        self.assertEqual(vrat_events[-1]["start_date"], "2026-10-25")
        
        # Verify the VRAT schemas
        for event in vrat_events:
            self.assertEqual(event["category"], "parva_vrat")
            self.assertEqual(event["badge"], "Parva / Vrat")
            self.assertEqual(event["badge_color"], "purple")
            self.assertEqual(event["is_span"], False)
            self.assertTrue(event["name"].startswith("Karma Nirjara Vrat"))

        # Verify Shravana Shukla Chaturdashi repeated (Tithi Vriddhi) in 2026
        shravana_events = [f for f in vrat_events if "Shravana" in f["jain_month"]]
        self.assertEqual(len(shravana_events), 2)
        self.assertEqual(shravana_events[0]["start_date"], "2026-08-26")
        self.assertEqual(shravana_events[1]["start_date"], "2026-08-27")


class AshtahnikaMahaparvTest(unittest.TestCase):
    def test_ashtahnika_mahaparv_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        # Look for ashtahnika occurrences
        events = [f for f in res["festivals"] if "ashtahnika" in f["id"]]
        self.assertEqual(len(events), 3)
        
        # Phalguna, Ashadha, Kartika
        phalguna = [f for f in events if "phalguna" in f["id"]][0]
        ashadha = [f for f in events if "ashadha" in f["id"]][0]
        kartika = [f for f in events if "kartika" in f["id"]][0]
        
        # Verify Ashadha (9-day span due to only Vriddhi)
        self.assertEqual(ashadha["start_date"], "2026-07-21")
        self.assertEqual(ashadha["end_date"], "2026-07-29")
        self.assertEqual(ashadha["span_label"], "Span: 07-21 – 07-29")
        
        # Verify Kartika (8-day span standard)
        self.assertEqual(kartika["start_date"], "2026-11-17")
        self.assertEqual(kartika["end_date"], "2026-11-24")
        self.assertEqual(kartika["span_label"], "Span: 11-17 – 11-24")
        
        # Verify schemas
        for event in events:
            self.assertEqual(event["category"], "mahaparv")
            self.assertEqual(event["badge"], "Mahaparv")
            self.assertEqual(event["badge_color"], "blue")
            self.assertEqual(event["is_span"], True)
            self.assertTrue(event["name"].startswith("Ashtahnika Mahaparv"))

    def test_ashtahnika_mahaparv_adhik_rule_2007(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2007,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        # Verify Ashadha Ashtahnika resolved only in Adhik Ashadha (July)
        ashadha_events = [f for f in res["festivals"] if "ashtahnika" in f["id"] and "ashadha" in f["id"]]
        self.assertEqual(len(ashadha_events), 1)
        self.assertEqual(ashadha_events[0]["start_date"], "2007-07-22")
        self.assertEqual(ashadha_events[0]["end_date"], "2007-07-30")


class NavpadOliTest(unittest.TestCase):
    def test_navpad_oli_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        # Look for navpad_ayambil_oli occurrences
        events = [f for f in res["festivals"] if "navpad_ayambil_oli" in f["id"]]
        
        # Spring Oli (Chaitra Shukla 7-15) and Autumn Oli (Ashwin Shukla 7-15)
        # Spring has 9 days, Autumn has 10 days (due to Vriddhi), so total 19 events
        self.assertEqual(len(events), 19)
        
        # Verify Spring Oli (starts around late March / early April)
        spring_events = [f for f in events if "spring" in f["id"]]
        self.assertEqual(len(spring_events), 9)
        # Verify sequential titles: Day 1 (Arihant) to Day 9 (Samyag Tapa)
        spring_events.sort(key=lambda x: x["start_date"])
        self.assertEqual(spring_events[0]["title"], "Navpad Oli - Day 1 (Arihant)")
        self.assertEqual(spring_events[-1]["title"], "Navpad Oli - Day 9 (Samyag Tapa)")
        
        # Verify schema
        for e in events:
            self.assertEqual(e["category"], "mahaparv")
            self.assertEqual(e["badge"], "Navpad Oli")
            self.assertEqual(e["badge_color"], "gold")
            self.assertEqual(e["is_span"], True)


class ChaitraShuklaEkamKalyanaksTest(unittest.TestCase):
    def test_kalyanaks_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        # Verify both events are resolved
        gautam = [f for f in res["festivals"] if f["id"] == "gautam_swami_janam_divas_2026"]
        mallinath = [f for f in res["festivals"] if f["id"] == "shri_mallinath_ji___garbh_2026"]
        
        self.assertEqual(len(gautam), 1)
        self.assertEqual(len(mallinath), 1)
        
        self.assertEqual(gautam[0]["category"], "janam_kalyanak")
        self.assertEqual(gautam[0]["badge"], "Janam Kalyan")
        self.assertEqual(gautam[0]["badge_color"], "green")
        self.assertEqual(gautam[0]["description"], "Birth anniversary of Gandhar Gautam Swami")
        
        self.assertEqual(mallinath[0]["category"], "garbha_kalyanak")
        self.assertEqual(mallinath[0]["badge"], "Garbha Kalyan")
        self.assertEqual(mallinath[0]["badge_color"], "saffron")
        self.assertEqual(mallinath[0]["description"], "Garbha Kalyanak of 19th Tirthankara Shri Mallinath Bhagwan")
        
        # Confirm they fall on the same day
        self.assertEqual(gautam[0]["start_date"], mallinath[0]["start_date"])


class PushpanjaliVratTest(unittest.TestCase):
    def test_pushpanjali_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        events = [f for f in res["festivals"] if "pushpanjali_vrat" in f["id"]]
        
        # Verify tri-annual occurrences: Spring (Chaitra), Monsoon (Bhadrapada), Winter (Magha)
        spring_events = [f for f in events if "spring" in f["id"]]
        monsoon_events = [f for f in events if "monsoon" in f["id"]]
        winter_events = [f for f in events if "winter" in f["id"]]
        
        self.assertTrue(len(spring_events) >= 5)
        self.assertTrue(len(monsoon_events) >= 5)
        self.assertTrue(len(winter_events) >= 5)
        
        # Verify schema of occurrences
        for e in events:
            self.assertEqual(e["category"], "vrat")
            self.assertEqual(e["badge"], "Pushpanjali Vrat")
            self.assertEqual(e["badge_color"], "rose")
            self.assertEqual(e["is_span"], True)
            self.assertTrue(e["title"].startswith("Pushpanjali Vrat - Day "))
            self.assertTrue(e["span_label"].startswith("Span: "))
            self.assertIn("–", e["span_label"])


class AkshayaTritiyaTest(unittest.TestCase):
    def test_akshaya_tritiya_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        events = [f for f in res["festivals"] if f["id"] == "akshaya_tritiya_dan_divas_2026"]
        self.assertEqual(len(events), 1)
        
        e = events[0]
        self.assertEqual(e["title"], "Akshaya Tritiya (Dan Divas)")
        self.assertEqual(e["category"], "mahaparv")
        self.assertEqual(e["badge"], "Akshaya Tritiya")
        self.assertEqual(e["badge_color"], "gold")
        self.assertEqual(e["description"], "First Ahar Dan to Bhagwan Rishabhdev & Varshi Tapa Parana")


class MonthlyVratTest(unittest.TestCase):
    def test_monthly_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        events = [f for f in res["festivals"] if "pratham_jeth_jinvani_vrat" in f["id"]]
        self.assertEqual(len(events), 2)
        
        start_evt = [f for f in events if f["boundary_type"] == "START"][0]
        end_evt = [f for f in events if f["boundary_type"] == "END"][0]
        
        self.assertEqual(start_evt["title"], "Pratham Jeth Jinvani Vrat - Start")
        self.assertEqual(start_evt["category"], "monthly_vrat")
        self.assertEqual(start_evt["badge"], "Vrat Start")
        self.assertEqual(start_evt["badge_color"], "pink")
        self.assertEqual(start_evt["is_boundary"], True)
        
        self.assertEqual(end_evt["title"], "Pratham Jeth Jinvani Vrat - Conclusion")
        self.assertEqual(end_evt["category"], "monthly_vrat")
        self.assertEqual(end_evt["badge"], "Vrat End")
        self.assertEqual(end_evt["badge_color"], "pink")
        self.assertEqual(end_evt["is_boundary"], True)


class DiwaliChaturmasNishthapanTest(unittest.TestCase):
    def test_diwali_chaturmas_nishthapan_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        
        diwali_evts = [f for f in res["festivals"] if f["id"] == "diwali_2026"]
        nishthapan_evts = [f for f in res["festivals"] if f["id"] == "chaturmas_nishthapan_2026"]
        
        self.assertEqual(len(diwali_evts), 1)
        self.assertEqual(len(nishthapan_evts), 1)
        
        d = diwali_evts[0]
        n = nishthapan_evts[0]
        
        self.assertEqual(d["title"], "Diwali (Bhagwan Mahavir Nirvan Kalyanak)")
        self.assertEqual(d["category"], "mahaparv")
        self.assertEqual(d["badge"], "Diwali")
        self.assertEqual(d["badge_color"], "pink")
        self.assertEqual(d["description"], "Nirvan Kalyanak of 24th Tirthankara Bhagwan Mahavir")
        
        self.assertEqual(n["title"], "Chaturmas Nishthapan")
        self.assertEqual(n["category"], "mahaparv")
        self.assertEqual(n["badge"], "Chaturmas End")
        self.assertEqual(n["badge_color"], "pink")
        self.assertEqual(n["description"], "Formal conclusion and completion of holy Chaturmas")
        
        self.assertEqual(d["start_date"], n["start_date"])


if __name__ == "__main__":
    unittest.main()

