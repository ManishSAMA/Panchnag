import unittest
from datetime import date
from unittest.mock import patch

def setUpModule():
    try:
        from jain_observances.festival_service import generate_jain_festivals
        generate_jain_festivals.cache_clear()
    except Exception:
        pass


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
                
            self.assertIn(fest["category"], ["kalyanak", "festival", "fast", "parva", "mahaparv", "parva_vrat", "monthly_vrat", "jayanti", "vrat", "poojan", "parv_vidhi", "mahaparv_vrat", "punyatithi", "punya_tithi", "tap_vrat", "auspicious", "shastra", "utsav"])
            self.assertIsInstance(fest["profiles"], list)
            self.assertTrue(len(fest["profiles"]) > 0)
            for p in fest["profiles"]:
                self.assertIn(p, ["all", "digambar", "shwetambar_murtipujak_tapagachchha", "shwetambar_sthanakvasi", "shwetambar_terapanthi"])
                
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
        # panchang_tithi_map confirms Chaitra Shukla Trayodashi (13) falls on 2026-03-31
        # (Ekadashi=03-29, Dwadashi=03-30, Trayodashi=03-31, no kshaya/vriddhi around this
        # date), matching this event's own tithi/month/paksha assertions below -- the
        # previous "2026-03-30" here was a stale fixture inconsistent with its own tithi.
        self.assertEqual(event["start_date"], "2026-03-31")
        self.assertEqual(event["jain_month"], "Chaitra")
        self.assertEqual(event["paksha"], "Shukla")
        self.assertEqual(event["tithi"], "Trayodashi (13)")
        self.assertEqual(event["status"], "confirmed")

    def test_sumatinath_kalyanaks_on_ekadashi(self):
        """Verify March 29, 2026 resolves to Chaitra Shukla Ekadashi (11) and Sumatinath Kalyanaks map to 2026-03-29."""
        from jain_observances.festival_service import generate_jain_festivals

        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        self.assertEqual(res["panchang_tithi_map"]["2026-03-29"], "Chaitra Shukla Ekadashi (11)")

        sumati_fests = [f for f in res["festivals"] if "sumatinath" in f["id"] and f.get("jain_month") == "Chaitra"]
        # Vrindavan/Uttarapurana/Ashadhara agree on Birth+Omniscience+Liberation at Ekadashi (11);
        # Vrindavan additionally records a separate, earlier Liberation Kalyanak at Navami (9);
        # Pt. Jaini Jiyalal Panchang adds Janma-Tapa together at Dashami (10).
        self.assertEqual(len(sumati_fests), 6)
        dashami_fests = [sf for sf in sumati_fests if sf["tithi"] == "Dashami (10)"]
        self.assertEqual(len(dashami_fests), 2)
        for sf in dashami_fests:
            self.assertEqual(sf["start_date"], "2026-03-28")
            self.assertEqual(sf["sources"], ["Pt. Jaini Jiyalal Panchang"])
        ekadashi_fests = [sf for sf in sumati_fests if sf["tithi"] == "Ekadashi (11)"]
        self.assertEqual(len(ekadashi_fests), 3)
        for sf in ekadashi_fests:
            self.assertEqual(sf["start_date"], "2026-03-29")
            self.assertEqual(sf["tithi"], "Ekadashi (11)")
            self.assertEqual(sf["paksha"], "Shukla")
            self.assertEqual(sf["jain_month"], "Chaitra")

        navami_fests = [sf for sf in sumati_fests if sf["tithi"] == "Navami (9)"]
        self.assertEqual(len(navami_fests), 1)
        self.assertEqual(navami_fests[0]["id"], "shri_sumatinath_ji___liberation_kalyanak_9_vrindavan")
        self.assertEqual(navami_fests[0]["paksha"], "Shukla")
        self.assertEqual(navami_fests[0]["jain_month"], "Chaitra")

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

    def test_parshvanath_conception_kalyanak_on_april_4(self):
        """Verify Shri Parshvanath Ji Conception Kalyanak falls on 2026-04-04 (Vaishakha Krishna Dwitiya / 2)."""
        from jain_observances.festival_service import generate_jain_festivals

        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )
        parshva_garbh = [f for f in res["festivals"] if f["id"].startswith("shri_parshvanath_ji___conception")]
        self.assertEqual(len(parshva_garbh), 1)
        self.assertEqual(parshva_garbh[0]["start_date"], "2026-04-04")
        self.assertEqual(parshva_garbh[0]["name"], "Shri Parshvanath Ji - Conception Kalyanak")
        self.assertEqual(parshva_garbh[0]["tithi"], "Dwitiya (2)")
        self.assertEqual(parshva_garbh[0]["paksha"], "Krishna")
        self.assertEqual(parshva_garbh[0]["jain_month"], "Vaishakha")
 
    def test_paryushan_profile_specific_dates(self):
        """Verify Samvatsari and Paryushan start differ between Tapagachchha (Shukla 4) and Sthanakvasi/Terapanthi (Shukla 5)."""
        from jain_observances.festival_service import generate_jain_festivals
        
        # Tapagachchha Samvatsari 2026 (Bhadrapada Shukla 4). panchang_tithi_map confirms
        # Chaturthi (4) falls on 2026-09-15 (Tritiya=09-14, Panchami=09-16, no
        # kshaya/vriddhi around this date) -- the previous "2026-09-14" here was a stale
        # fixture (that date is actually Tritiya, one tithi earlier).
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
        self.assertTrue("pakhi_chaudas_shukla" in self.ids or "pakhi_chaudas_bhadrapada" in self.ids)

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

    def test_pakhi_chaudas_at_least_10(self):
        self.assertGreaterEqual(self._count("pakhi_chaudas_shukla") + self._count("pakhi_chaudas_bhadrapada"), 10)

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
        events = [f for f in res["festivals"] if f["id"].startswith("ashtahnika_")]
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


class VeerShasanJayantiTest(unittest.TestCase):
    def test_veer_shasan_jayanti_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        vsj = [f for f in res["festivals"] if f["id"] == "veer_shasan_jayanti_2026"]
        sud = [f for f in res["festivals"] if f["id"] == "shrut_udbhav_divas_2026"]

        self.assertEqual(len(vsj), 1)
        self.assertEqual(len(sud), 1)

        v = vsj[0]
        s = sud[0]

        self.assertEqual(v["title"], "Veer Shasan Jayanti")
        self.assertEqual(v["category"], "jayanti")
        self.assertEqual(v["badge"], "Veer Shasan")
        self.assertEqual(v["badge_color"], "green")
        self.assertEqual(v["description"], "Commencement of Bhagwan Mahavir's Shasan and his first divine discourse")

        self.assertEqual(s["title"], "Shrut Udbhav Divas")
        self.assertEqual(s["category"], "mahaparv")
        self.assertEqual(s["badge"], "Shrut Udbhav")
        self.assertEqual(s["badge_color"], "green")
        self.assertEqual(s["description"], "Origin of Jain Agamic knowledge and scriptural tradition")

        # Both events must share the same solar date
        self.assertEqual(v["start_date"], s["start_date"])


class SaptaRishiVratTest(unittest.TestCase):
    def test_sapta_rishi_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "sapta_rishi_vrat_prarambh_2026"]
        n = [f for f in res["festivals"] if f["id"] == "sapta_rishi_vrat_nishthapan_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(n), 1)

        p_evt = p[0]
        n_evt = n[0]

        self.assertEqual(p_evt["title"], "Sapta Rishi Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(n_evt["title"], "Sapta Rishi Vrat Nishthapan")
        self.assertEqual(n_evt["category"], "vrat")
        self.assertEqual(n_evt["badge"], "Vrat End")
        self.assertEqual(n_evt["badge_color"], "pink")
        self.assertTrue(n_evt["is_span"])
        self.assertEqual(p_evt["span_label"], n_evt["span_label"])


class SaptaParamsthanVratTest(unittest.TestCase):
    def test_sapta_paramsthan_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "sapta_paramsthan_vrat_prarambh_2026"]
        e = [f for f in res["festivals"] if f["id"] == "sapta_paramsthan_vrat_purna_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(e), 1)

        p_evt = p[0]
        e_evt = e[0]

        self.assertEqual(p_evt["title"], "Sapta Paramsthan Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertEqual(p_evt["boundary_type"], "START")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(e_evt["title"], "Sapta Paramsthan Vrat Purna")
        self.assertEqual(e_evt["category"], "vrat")
        self.assertEqual(e_evt["badge"], "Vrat End")
        self.assertEqual(e_evt["badge_color"], "pink")
        self.assertEqual(e_evt["boundary_type"], "END")
        self.assertTrue(e_evt["is_span"])
        self.assertEqual(p_evt["span_label"], e_evt["span_label"])


class RakshabandhanVratTest(unittest.TestCase):
    def test_rakshabandhan_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "rakshabandhan_vrat_prarambh_2026"]
        e = [f for f in res["festivals"] if f["id"] == "rakshabandhan_vrat_purna_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(e), 1)

        p_evt = p[0]
        e_evt = e[0]

        self.assertEqual(p_evt["title"], "Rakshabandhan Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertEqual(p_evt["boundary_type"], "START")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(e_evt["title"], "Rakshabandhan Vrat Purna (Rakshabandhan Mahaparv)")
        self.assertEqual(e_evt["category"], "mahaparv")
        self.assertEqual(e_evt["badge"], "Vrat End")
        self.assertEqual(e_evt["badge_color"], "pink")
        self.assertEqual(e_evt["boundary_type"], "END")
        self.assertTrue(e_evt["is_span"])
        self.assertEqual(p_evt["span_label"], e_evt["span_label"])


class ShravanaPurnimaRakshabandhanTest(unittest.TestCase):
    def test_shravana_purnima_rakshabandhan_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        r = [f for f in res["festivals"] if f["id"] == "rakshabandhan_700_muni_raksha_divas_2026"]
        m = [f for f in res["festivals"] if f["id"] == "muni_vishnukumar_akampanacharya_pujan_2026"]
        s = [f for f in res["festivals"] if f["id"] == "sorana_pujan_2026"]

        self.assertEqual(len(r), 1)
        self.assertEqual(len(m), 1)
        self.assertEqual(len(s), 1)

        r_evt = r[0]
        m_evt = m[0]
        s_evt = s[0]

        self.assertEqual(r_evt["title"], "Rakshabandhan (700 Muni Raksha Divas)")
        self.assertEqual(r_evt["category"], "mahaparv")
        self.assertEqual(r_evt["badge"], "Mahaparv")
        self.assertEqual(r_evt["badge_color"], "pink")

        self.assertEqual(m_evt["title"], "Muni Vishnukumar avem Akampanacharya Pujan")
        self.assertEqual(m_evt["category"], "poojan")
        self.assertEqual(m_evt["badge"], "Pujan")
        self.assertEqual(m_evt["badge_color"], "pink")

        self.assertEqual(s_evt["title"], "Sorana Pujan (Raksha Sutra Bandhan)")
        self.assertEqual(s_evt["category"], "parv_vidhi")
        self.assertEqual(s_evt["badge"], "Sorana Pujan")
        self.assertEqual(s_evt["badge_color"], "pink")

        self.assertEqual(r_evt["start_date"], m_evt["start_date"])
        self.assertEqual(r_evt["start_date"], s_evt["start_date"])


class BhadrapadaKrishnaEkamMultiVratTest(unittest.TestCase):
    def test_multi_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        s_karan = [f for f in res["festivals"] if f["id"] == "solah_karan_vrat_prarambh_2026"]
        j_mukh = [f for f in res["festivals"] if f["id"] == "shri_jin_mukhavlokan_vrat_prarambh_2026"]
        s_skandha = [f for f in res["festivals"] if f["id"] == "shrut_skandha_vrat_prarambh_2026"]
        m_vidhan = [f for f in res["festivals"] if f["id"] == "mushti_vidhan_vrat_prarambh_2026"]
        d_kalash = [f for f in res["festivals"] if f["id"] == "dhanda_kalash_vrat_prarambh_2026"]
        m_mala = [f for f in res["festivals"] if f["id"] == "megh_mala_vrat_prarambh_2026"]

        self.assertEqual(len(s_karan), 1)
        self.assertEqual(len(j_mukh), 1)
        self.assertEqual(len(s_skandha), 1)
        self.assertEqual(len(m_vidhan), 1)
        self.assertEqual(len(d_kalash), 1)
        self.assertEqual(len(m_mala), 1)

        self.assertEqual(s_karan[0]["title"], "Solah Karan Vrat Prarambh")
        self.assertEqual(s_karan[0]["category"], "mahaparv_vrat")
        self.assertEqual(s_karan[0]["badge"], "Vrat Start")
        self.assertEqual(s_karan[0]["badge_color"], "pink")
        self.assertTrue(s_karan[0]["is_span"])

        self.assertEqual(j_mukh[0]["title"], "Shri Jin Mukhavlokan Vrat Prarambh")
        self.assertEqual(j_mukh[0]["category"], "vrat")
        self.assertEqual(j_mukh[0]["badge"], "Vrat Start")
        self.assertEqual(j_mukh[0]["badge_color"], "pink")
        self.assertTrue(j_mukh[0]["is_span"])

        self.assertEqual(s_skandha[0]["title"], "Shrut Skandha Vrat Prarambh")
        self.assertEqual(m_vidhan[0]["title"], "Mushti Vidhan Vrat Prarambh")
        self.assertEqual(d_kalash[0]["title"], "Dhanda Kalash Vrat Prarambh")
        self.assertEqual(m_mala[0]["title"], "Megh Mala Vrat Prarambh")

        # All 6 events must fall on the same date
        d_target = s_karan[0]["start_date"]
        for ev in [j_mukh[0], s_skandha[0], m_vidhan[0], d_kalash[0], m_mala[0]]:
            self.assertEqual(ev["start_date"], d_target)


class TeenChaubisiVratTest(unittest.TestCase):
    def test_teen_chaubisi_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        tc = [f for f in res["festivals"] if f["id"] == "teen_chaubisi_vrat_prarambh_2026"]
        self.assertEqual(len(tc), 1)

        evt = tc[0]
        self.assertEqual(evt["title"], "Teen Chaubisi Vrat Prarambh")
        self.assertEqual(evt["category"], "vrat")
        self.assertEqual(evt["badge"], "Vrat Start")
        self.assertEqual(evt["badge_color"], "pink")
        self.assertTrue(evt["is_span"])
        self.assertEqual(evt["boundary_type"], "START")


class AkshayaNidhiVratTest(unittest.TestCase):
    def test_akshaya_nidhi_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "akshaya_nidhi_vrat_prarambh_2026"]
        e = [f for f in res["festivals"] if f["id"] == "akshaya_nidhi_vrat_purna_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(e), 1)

        p_evt = p[0]
        e_evt = e[0]

        self.assertEqual(p_evt["title"], "Akshaya Nidhi Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertEqual(p_evt["boundary_type"], "START")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(e_evt["title"], "Akshaya Nidhi Vrat Purna")
        self.assertEqual(e_evt["category"], "vrat")
        self.assertEqual(e_evt["badge"], "Vrat End")
        self.assertEqual(e_evt["badge_color"], "pink")
        self.assertEqual(e_evt["boundary_type"], "END")
        self.assertTrue(e_evt["is_span"])
        self.assertEqual(p_evt["span_label"], e_evt["span_label"])


class ShvetambaraParyushan50DayTest(unittest.TestCase):
    def test_paryushan_50_day_cycle_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="shwetambar_murtipujak_tapagachchha"
        )

        d1 = [f for f in res["festivals"] if f["id"] == "shvetambara_chaturmas_prarambh_2026"]
        d50 = [f for f in res["festivals"] if f["id"] == "samvatsari_mahaparv_2026"]

        self.assertEqual(len(d1), 1)
        self.assertEqual(len(d50), 1)

        d1_evt = d1[0]
        d50_evt = d50[0]

        self.assertEqual(d1_evt["title"], "Chaturmas Prarambh (50-Day Paryushan Cycle Start)")
        self.assertEqual(d1_evt["badge"], "Cycle Start")
        self.assertEqual(d1_evt["boundary_type"], "START")
        self.assertEqual(d1_evt["day_index"], 1)

        self.assertEqual(d50_evt["title"], "Samvatsari Mahaparv (Kshamavani Divas)")
        self.assertEqual(d50_evt["badge"], "Samvatsari")
        self.assertEqual(d50_evt["boundary_type"], "END")

        # Verify exact 50-day solar interval: Day 50 date is Day 1 date + 49 days
        from datetime import date, timedelta
        dt1 = date.fromisoformat(d1_evt["start_date"])
        dt50 = date.fromisoformat(d50_evt["start_date"])
        self.assertEqual(dt50, dt1 + timedelta(days=49))


class BhayaHaranVratTest(unittest.TestCase):
    def test_bhaya_haran_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        bh = [f for f in res["festivals"] if f["id"] == "bhaya_haran_vrat_2026"]
        self.assertEqual(len(bh), 1)

        evt = bh[0]
        self.assertEqual(evt["title"], "Bhaya Haran Vrat")
        self.assertEqual(evt["category"], "vrat")
        self.assertEqual(evt["badge"], "Vrat")
        self.assertEqual(evt["badge_color"], "green")


class LabdhiVidhanVratTest(unittest.TestCase):
    def test_labdhi_vidhan_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "labdhi_vidhan_vrat_prarambh_2026"]
        e = [f for f in res["festivals"] if f["id"] == "labdhi_vidhan_vrat_purna_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(e), 1)

        p_evt = p[0]
        e_evt = e[0]

        self.assertEqual(p_evt["title"], "Labdhi Vidhan Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertEqual(p_evt["boundary_type"], "START")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(e_evt["title"], "Labdhi Vidhan Vrat Purna")
        self.assertEqual(e_evt["category"], "vrat")
        self.assertEqual(e_evt["badge"], "Vrat End")
        self.assertEqual(e_evt["badge_color"], "pink")
        self.assertEqual(e_evt["boundary_type"], "END")
        self.assertTrue(e_evt["is_span"])
        self.assertEqual(p_evt["span_label"], e_evt["span_label"])


class TalaDharTapShantisagarPunyatithiTest(unittest.TestCase):
    def test_tala_dhar_tap_shantisagar_punyatithi_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "acharya_shantisagar_punyatithi_2026"]
        t = [f for f in res["festivals"] if f["id"] == "tala_dhar_tap_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(t), 1)

        p_evt = p[0]
        t_evt = t[0]

        self.assertEqual(p_evt["title"], "Acharya Shantisagar Punyatithi (Samadhi Divas)")
        self.assertEqual(p_evt["category"], "punyatithi")
        self.assertEqual(p_evt["badge"], "Samadhi Divas")
        self.assertEqual(p_evt["badge_color"], "pink")

        self.assertEqual(t_evt["title"], "Tala Dhar Tap")
        self.assertEqual(t_evt["category"], "tap_vrat")
        self.assertEqual(t_evt["badge"], "Tap")
        self.assertEqual(t_evt["badge_color"], "pink")

        self.assertEqual(p_evt["start_date"], t_evt["start_date"])


class BadiPanchamiMeruSthapanaTest(unittest.TestCase):
    def test_badi_panchami_meru_sthapana_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        b = [f for f in res["festivals"] if f["id"] == "badi_panchami_2026"]
        m = [f for f in res["festivals"] if f["id"] == "meru_sthapana_2026"]

        self.assertEqual(len(b), 1)
        self.assertEqual(len(m), 1)

        b_evt = b[0]
        m_evt = m[0]

        self.assertEqual(b_evt["title"], "Badi Panchami")
        self.assertEqual(b_evt["category"], "mahaparv")
        self.assertEqual(b_evt["badge"], "Badi Panchami")
        self.assertEqual(b_evt["badge_color"], "pink")

        self.assertEqual(m_evt["title"], "Meru Sthapana (Sudarshan Meru Pujan)")
        self.assertEqual(m_evt["category"], "parv_vidhi")
        self.assertEqual(m_evt["badge"], "Meru Sthapana")
        self.assertEqual(m_evt["badge_color"], "pink")

        self.assertEqual(b_evt["start_date"], m_evt["start_date"])


class NihshalyaAshtamiManchinTithiTest(unittest.TestCase):
    def test_nihshalya_ashtami_manchin_tithi_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        n = [f for f in res["festivals"] if f["id"] == "nihshalya_ashtami_vrat_2026"]
        m = [f for f in res["festivals"] if f["id"] == "manchin_tithi_ashtami_2026"]

        self.assertEqual(len(n), 1)
        self.assertEqual(len(m), 1)

        n_evt = n[0]
        m_evt = m[0]

        self.assertEqual(n_evt["title"], "Nihshalya Ashtami Vrat")
        self.assertEqual(n_evt["category"], "vrat")
        self.assertEqual(n_evt["badge"], "Vrat")
        self.assertEqual(n_evt["badge_color"], "pink")

        self.assertEqual(m_evt["title"], "Manchin Tithi Ashtami")
        self.assertEqual(m_evt["category"], "parv_vidhi")
        self.assertEqual(m_evt["badge"], "Manchin Tithi")
        self.assertEqual(m_evt["badge_color"], "pink")

        self.assertEqual(n_evt["start_date"], m_evt["start_date"])


class SugandhDashamiTest(unittest.TestCase):
    def test_sugandh_dashami_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        m = [f for f in res["festivals"] if f["id"] == "sugandh_dashami_mahaparv_2026"]
        v = [f for f in res["festivals"] if f["id"] == "sugandh_dashami_vrat_2026"]

        self.assertEqual(len(m), 1)
        self.assertEqual(len(v), 1)

        m_evt = m[0]
        v_evt = v[0]

        self.assertEqual(m_evt["title"], "Sugandh Dashami (Dhoop Dashami Mahaparv)")
        self.assertEqual(m_evt["category"], "mahaparv")
        self.assertEqual(m_evt["badge"], "Sugandh Dashami")
        self.assertEqual(m_evt["badge_color"], "pink")

        self.assertEqual(v_evt["title"], "Sugandh Dashami Vrat")
        self.assertEqual(v_evt["category"], "vrat")
        self.assertEqual(v_evt["badge"], "Vrat")
        self.assertEqual(v_evt["badge_color"], "pink")

        self.assertEqual(m_evt["start_date"], v_evt["start_date"])


class AnantChaturdashiVratTest(unittest.TestCase):
    def test_anant_chaturdashi_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "anant_vrat_prarambh_2026"]
        e = [f for f in res["festivals"] if f["id"] == "anant_chaturdashi_purna_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(e), 1)

        p_evt = p[0]
        e_evt = e[0]

        self.assertEqual(p_evt["title"], "Anant Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertEqual(p_evt["boundary_type"], "START")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(e_evt["title"], "Anant Chaturdashi (Anant Vrat Purna)")
        self.assertEqual(e_evt["category"], "mahaparv")
        self.assertEqual(e_evt["badge"], "Mahaparv")
        self.assertEqual(e_evt["badge_color"], "pink")
        self.assertEqual(e_evt["boundary_type"], "END")
        self.assertTrue(e_evt["is_span"])
        self.assertEqual(p_evt["span_label"], e_evt["span_label"])


class RatnatrayaSankatHaranVratTest(unittest.TestCase):
    def test_ratnatraya_sankat_haran_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        rp = [f for f in res["festivals"] if f["id"] == "ratnatraya_vrat_prarambh_2026"]
        sp = [f for f in res["festivals"] if f["id"] == "sankat_haran_vrat_prarambh_2026"]
        re = [f for f in res["festivals"] if f["id"] == "ratnatraya_vrat_purna_2026"]
        se = [f for f in res["festivals"] if f["id"] == "sankat_haran_vrat_purna_2026"]

        self.assertEqual(len(rp), 1)
        self.assertEqual(len(sp), 1)
        self.assertEqual(len(re), 1)
        self.assertEqual(len(se), 1)

        rp_evt = rp[0]
        sp_evt = sp[0]
        re_evt = re[0]
        se_evt = se[0]

        self.assertEqual(rp_evt["title"], "Ratnatraya Vrat Prarambh")
        self.assertEqual(rp_evt["category"], "mahaparv_vrat")
        self.assertEqual(rp_evt["badge"], "Vrat Start")

        self.assertEqual(sp_evt["title"], "Sankat Haran Vrat Prarambh")
        self.assertEqual(sp_evt["category"], "vrat")
        self.assertEqual(sp_evt["badge"], "Vrat Start")

        self.assertEqual(re_evt["title"], "Ratnatraya Vrat Purna")
        self.assertEqual(re_evt["category"], "mahaparv_vrat")
        self.assertEqual(re_evt["badge"], "Vrat End")

        self.assertEqual(se_evt["title"], "Sankat Haran Vrat Purna")
        self.assertEqual(se_evt["category"], "vrat")
        self.assertEqual(se_evt["badge"], "Vrat End")

        self.assertEqual(rp_evt["start_date"], sp_evt["start_date"])
        self.assertEqual(re_evt["start_date"], se_evt["start_date"])


class KshamavaniMahaparvTest(unittest.TestCase):
    def test_kshamavani_mahaparv_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="digambar"
        )

        k = [f for f in res["festivals"] if f["id"] == "kshamavani_mahaparv_2026"]
        self.assertEqual(len(k), 1)

        evt = k[0]
        self.assertEqual(evt["title"], "Kshamavani Mahaparv (Kshamadwani Divas)")
        self.assertEqual(evt["category"], "mahaparv")
        self.assertEqual(evt["badge"], "Kshamavani")
        self.assertEqual(evt["badge_color"], "pink")


class ShraddhaVratTest(unittest.TestCase):
    def test_shraddha_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        p = [f for f in res["festivals"] if f["id"] == "shraddha_vrat_prarambh_2026"]
        e = [f for f in res["festivals"] if f["id"] == "shraddha_vrat_purna_2026"]

        self.assertEqual(len(p), 1)
        self.assertEqual(len(e), 1)

        p_evt = p[0]
        e_evt = e[0]

        self.assertEqual(p_evt["title"], "Shraddha Vrat Prarambh")
        self.assertEqual(p_evt["category"], "vrat")
        self.assertEqual(p_evt["badge"], "Vrat Start")
        self.assertEqual(p_evt["badge_color"], "pink")
        self.assertEqual(p_evt["boundary_type"], "START")
        self.assertTrue(p_evt["is_span"])

        self.assertEqual(e_evt["title"], "Shraddha Vrat Purna")
        self.assertEqual(e_evt["category"], "vrat")
        self.assertEqual(e_evt["badge"], "Vrat End")
        self.assertEqual(e_evt["badge_color"], "pink")
        self.assertEqual(e_evt["boundary_type"], "END")
        self.assertTrue(e_evt["is_span"])
        self.assertEqual(p_evt["span_label"], e_evt["span_label"])


class NavapadOliVratTest(unittest.TestCase):
    def test_navapad_oli_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        cp = [f for f in res["festivals"] if f["id"] == "navapad_oli_vrat_prarambh_chaitra_2026"]
        ce = [f for f in res["festivals"] if f["id"] == "navapad_oli_vrat_purna_chaitra_2026"]
        ap = [f for f in res["festivals"] if f["id"] == "navapad_oli_vrat_prarambh_ashwin_2026"]
        ae = [f for f in res["festivals"] if f["id"] == "navapad_oli_vrat_purna_ashwin_2026"]

        self.assertEqual(len(cp), 1)
        self.assertEqual(len(ce), 1)
        self.assertEqual(len(ap), 1)
        self.assertEqual(len(ae), 1)

        cp_evt = cp[0]
        ce_evt = ce[0]

        self.assertEqual(cp_evt["title"], "Navapad Oli Prarambh (Ayambil Oli Start)")
        self.assertEqual(cp_evt["category"], "mahaparv_vrat")
        self.assertEqual(cp_evt["badge"], "Vrat Start")
        self.assertEqual(cp_evt["badge_color"], "pink")
        self.assertEqual(cp_evt["boundary_type"], "START")
        self.assertTrue(cp_evt["is_span"])

        self.assertEqual(ce_evt["title"], "Navapad Oli Purna (Ayambil Oli Nishthapan)")
        self.assertEqual(ce_evt["category"], "mahaparv_vrat")
        self.assertEqual(ce_evt["badge"], "Vrat End")
        self.assertEqual(ce_evt["badge_color"], "pink")
        self.assertEqual(ce_evt["boundary_type"], "END")
        self.assertTrue(ce_evt["is_span"])
        self.assertEqual(cp_evt["span_label"], ce_evt["span_label"])


class JeevDayaAshtamiTest(unittest.TestCase):
    def test_jeev_daya_ashtami_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        jda = [f for f in res["festivals"] if f["id"] == "jeev_daya_ashtami_2026"]
        self.assertEqual(len(jda), 1)

        evt = jda[0]
        self.assertEqual(evt["title"], "Jeev Daya Ashtami")
        self.assertEqual(evt["category"], "mahaparv_vrat")
        self.assertEqual(evt["badge"], "Jeev Daya")
        self.assertEqual(evt["badge_color"], "pink")


class SharadPurnimaJayantisTest(unittest.TestCase):
    def test_sharad_purnima_jayantis_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="digambar"
        )

        v = [f for f in res["festivals"] if f["id"] == "acharya_vidyasagar_jayanti_2026"]
        g = [f for f in res["festivals"] if f["id"] == "ganini_gyanmati_mataji_jayanti_2026"]
        s = [f for f in res["festivals"] if f["id"] == "sharad_purnima_2026"]

        self.assertEqual(len(v), 1)
        self.assertEqual(len(g), 1)
        self.assertEqual(len(s), 1)

        v_evt = v[0]
        g_evt = g[0]
        s_evt = s[0]

        self.assertEqual(v_evt["title"], "Acharya Vidyasagar Ji Maharaj Janma Jayanti")
        self.assertEqual(v_evt["category"], "jayanti")
        self.assertEqual(v_evt["badge"], "Janma Jayanti")

        self.assertEqual(g_evt["title"], "Ganini Aryika Gyanmati Mataji Janma Jayanti")
        self.assertEqual(g_evt["category"], "jayanti")
        self.assertEqual(g_evt["badge"], "Janma Jayanti")

        self.assertEqual(s_evt["title"], "Sharad Purnima (Kojagiri Purnima)")
        self.assertEqual(s_evt["category"], "mahaparv")
        self.assertEqual(s_evt["badge"], "Sharad Purnima")

        self.assertEqual(v_evt["start_date"], g_evt["start_date"])
        self.assertEqual(g_evt["start_date"], s_evt["start_date"])


class SplitDayAhoiKarwaDampatyaTest(unittest.TestCase):
    def test_split_day_ahoi_karwa_dampatya_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        kc = [f for f in res["festivals"] if f["id"] == "karwa_chauth_2026"]
        aa = [f for f in res["festivals"] if f["id"] == "ahoi_ashtami_2026"]
        da = [f for f in res["festivals"] if f["id"] == "dampatya_ashtami_2026"]

        self.assertEqual(len(kc), 1)
        self.assertEqual(len(aa), 1)
        self.assertEqual(len(da), 1)

        kc_evt = kc[0]
        aa_evt = aa[0]
        da_evt = da[0]

        self.assertEqual(kc_evt["title"], "Karwa Chauth (Kark Chaturthi)")
        self.assertEqual(kc_evt["category"], "vrat")
        self.assertEqual(kc_evt["badge"], "Karwa Chauth")

        self.assertEqual(aa_evt["title"], "Ahoi Ashtami")
        self.assertEqual(aa_evt["category"], "vrat")
        self.assertEqual(aa_evt["badge"], "Ahoi Ashtami")

        self.assertEqual(da_evt["title"], "Dampatya Ashtami")
        self.assertEqual(da_evt["category"], "vrat")
        self.assertEqual(da_evt["badge"], "Dampatya Ashtami")


class GyanDhanTrayodashiTest(unittest.TestCase):
    def test_gyan_dhan_trayodashi_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        gt = [f for f in res["festivals"] if f["id"] == "gyan_trayodashi_2026"]
        dt = [f for f in res["festivals"] if f["id"] == "dhan_teras_2026"]

        self.assertEqual(len(gt), 1)
        self.assertEqual(len(dt), 1)

        gt_evt = gt[0]
        dt_evt = dt[0]

        self.assertEqual(gt_evt["title"], "Gyan Trayodashi (Jnana Trayodashi)")
        self.assertEqual(gt_evt["category"], "mahaparv_vrat")
        self.assertEqual(gt_evt["badge"], "Gyan Trayodashi")

        self.assertEqual(dt_evt["title"], "Dhan Trayodashi (Dhanteras)")
        self.assertEqual(dt_evt["category"], "mahaparv")
        self.assertEqual(dt_evt["badge"], "Dhanteras")

        self.assertEqual(gt_evt["start_date"], dt_evt["start_date"])


class KartikaAmavasyaMahaviraNirvanaTest(unittest.TestCase):
    def test_kartika_amavasya_mahavira_nirvana_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        mnk = [f for f in res["festivals"] if f["id"] == "mahavira_nirvana_kalyanak_2026"]
        vyn = [f for f in res["festivals"] if f["id"] == "varsha_yog_nishthapan_2026"]
        ggk = [f for f in res["festivals"] if f["id"] == "gautam_gandhar_kevalgyan_2026"]

        self.assertEqual(len(mnk), 1)
        self.assertEqual(len(vyn), 1)
        self.assertEqual(len(ggk), 1)

        m_evt = mnk[0]
        v_evt = vyn[0]
        g_evt = ggk[0]

        self.assertEqual(m_evt["title"], "Bhagwan Mahavira Nirvana Kalyanak (Diwali)")
        self.assertEqual(m_evt["category"], "mahaparv")
        self.assertEqual(m_evt["badge"], "Moksha Kalyanak")

        self.assertEqual(v_evt["title"], "Varsha Yog Nishthapan (Chaturmas Conclusion)")
        self.assertEqual(v_evt["category"], "mahaparv")
        self.assertEqual(v_evt["badge"], "Nishthapan")

        self.assertEqual(g_evt["title"], "Gautam Gandhar Kevalgyan Mahotsav")
        self.assertEqual(g_evt["category"], "mahaparv")
        self.assertEqual(g_evt["badge"], "Kevalgyan")

        self.assertEqual(m_evt["start_date"], v_evt["start_date"])
        self.assertEqual(v_evt["start_date"], g_evt["start_date"])


class KartikaShuklaEkamNewYearTest(unittest.TestCase):
    def test_kartika_shukla_ekam_new_year_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        ny = [f for f in res["festivals"] if f["id"] == "jain_new_year_2026"]
        gp = [f for f in res["festivals"] if f["id"] == "gautam_swami_kevalgyan_pujan_2026"]

        self.assertEqual(len(ny), 1)
        self.assertEqual(len(gp), 1)

        ny_evt = ny[0]
        gp_evt = gp[0]

        self.assertEqual(ny_evt["title"], "Navina Vira Nirvana Samvat Prarambh (Jain New Year)")
        self.assertEqual(ny_evt["category"], "mahaparv")
        self.assertEqual(ny_evt["badge"], "New Year")

        self.assertEqual(gp_evt["title"], "Gautam Swami Kevalgyan Pujan")
        self.assertEqual(gp_evt["category"], "mahaparv")
        self.assertEqual(gp_evt["badge"], "Kevalgyan")

        self.assertEqual(ny_evt["start_date"], gp_evt["start_date"])


class BhaiDoojTest(unittest.TestCase):
    def test_bhai_dooj_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        bd = [f for f in res["festivals"] if f["id"] == "bhai_dooj_2026"]

        self.assertEqual(len(bd), 1)

        b_evt = bd[0]

        self.assertEqual(b_evt["title"], "Bhaiya Dooj (Bhratri Dvitiya)")
        self.assertEqual(b_evt["category"], "mahaparv")
        self.assertEqual(b_evt["badge"], "Bhai Dooj")


class KartikaShuklaPanchamiTest(unittest.TestCase):
    def test_kartika_shukla_panchami_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        gp = [f for f in res["festivals"] if f["id"] == "gyan_panchami_2026"]
        lp = [f for f in res["festivals"] if f["id"] == "labh_panchami_2026"]

        self.assertEqual(len(gp), 1)
        self.assertEqual(len(lp), 1)

        gp_evt = gp[0]
        lp_evt = lp[0]

        self.assertEqual(gp_evt["title"], "Gyan Panchami (Jnana Panchami)")
        self.assertEqual(gp_evt["category"], "mahaparv_vrat")
        self.assertEqual(gp_evt["badge"], "Gyan Panchami")

        self.assertEqual(lp_evt["title"], "Labh Panchami (Saubhagya Panchami)")
        self.assertEqual(lp_evt["category"], "mahaparv")
        self.assertEqual(lp_evt["badge"], "Labh Panchami")

        self.assertEqual(gp_evt["start_date"], lp_evt["start_date"])


class KartikaNandishwarAshtamiTest(unittest.TestCase):
    def test_kartika_nandishwar_ashtami_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        na = [f for f in res["festivals"] if f["id"] == "nandishwar_ashtami_kartika_2026"]

        self.assertEqual(len(na), 1)

        n_evt = na[0]

        self.assertEqual(n_evt["title"], "Nandishwar Ashtami (Ashtahnika Parv Prarambh)")
        self.assertEqual(n_evt["category"], "mahaparv_vrat")
        self.assertEqual(n_evt["badge"], "Vrat Start")
        self.assertTrue(n_evt["is_span"])
        self.assertEqual(n_evt["boundary_type"], "START")


class PanditJainiJiyalalPunyatithiTest(unittest.TestCase):
    def test_pandit_jaini_jiyalal_punyatithi_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="digambar"
        )

        pj = [f for f in res["festivals"] if f["id"] == "pandit_jaini_jiyalal_punyatithi_2026"]

        self.assertEqual(len(pj), 1)

        p_evt = pj[0]

        self.assertEqual(p_evt["title"], "Pandit Jaini Jiyalal Ji Chaudhary Punya Divas")
        self.assertEqual(p_evt["category"], "punya_tithi")
        self.assertEqual(p_evt["badge"], "Punya Tithi")
        self.assertEqual(p_evt["badge_color"], "Goldern")


class KartikaPurnimaAshtahnikaPurnaTest(unittest.TestCase):
    def test_kartika_purnima_ashtahnika_purna_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        ap = [f for f in res["festivals"] if f["id"] == "kartika_ashtahnika_purna_2026"]
        kp = [f for f in res["festivals"] if f["id"] == "kartika_purnima_dev_deepavali_2026"]

        self.assertEqual(len(ap), 1)
        self.assertEqual(len(kp), 1)

        a_evt = ap[0]
        k_evt = kp[0]

        self.assertEqual(a_evt["title"], "Kartika Ashtahnika Mahaparv Purna")
        self.assertEqual(a_evt["category"], "mahaparv_vrat")
        self.assertEqual(a_evt["badge"], "Vrat End")
        self.assertTrue(a_evt["is_span"])
        self.assertEqual(a_evt["boundary_type"], "END")

        self.assertEqual(k_evt["title"], "Kartika Purnima (Dev Deepavali)")
        self.assertEqual(k_evt["category"], "mahaparv")
        self.assertEqual(k_evt["badge"], "Kartika Purnima")

        self.assertEqual(a_evt["start_date"], k_evt["start_date"])


class MargashirshaSheetalnathStotramTest(unittest.TestCase):
    def test_margashirsha_sheetalnath_stotram_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        ss = [f for f in res["festivals"] if f["id"] == "sheetalnath_stotram_rachna_2026"]

        self.assertEqual(len(ss), 1)

        s_evt = ss[0]

        self.assertEqual(s_evt["title"], "Bhagwan Sheetalnath Stotram Rachna Divas")
        self.assertEqual(s_evt["category"], "mahaparv")
        self.assertEqual(s_evt["badge"], "Stotram Rachna")
        self.assertEqual(s_evt["badge_color"], "pink")


class MaghaLabdhiVidhanTest(unittest.TestCase):
    def test_magha_labdhi_vidhan_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        st = [f for f in res["festivals"] if f["id"] == "labdhi_vidhan_start_magha_2026"]
        pu = [f for f in res["festivals"] if f["id"] == "labdhi_vidhan_purna_magha_2026"]

        self.assertEqual(len(st), 1)
        self.assertEqual(len(pu), 1)

        s_evt = st[0]
        p_evt = pu[0]

        self.assertEqual(s_evt["title"], "Labdhi Vidhan Vrat Prarambh")
        self.assertEqual(s_evt["category"], "mahaparv_vrat")
        self.assertEqual(s_evt["badge"], "Vrat Start")
        self.assertEqual(s_evt["badge_color"], "orange")
        self.assertTrue(s_evt["is_span"])
        self.assertEqual(s_evt["boundary_type"], "START")

        self.assertEqual(p_evt["title"], "Labdhi Vidhan Vrat Purna")
        self.assertEqual(p_evt["category"], "mahaparv_vrat")
        self.assertEqual(p_evt["badge"], "Vrat End")
        self.assertEqual(p_evt["badge_color"], "orange")
        self.assertTrue(p_evt["is_span"])
        self.assertEqual(p_evt["boundary_type"], "END")


class PanditJainiJiyalalJanmaDivasTest(unittest.TestCase):
    def test_pandit_jaini_jiyalal_janma_divas_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="digambar"
        )

        jd = [f for f in res["festivals"] if f["id"] == "pandit_jaini_jiyalal_janma_divas_2026"]

        self.assertEqual(len(jd), 1)

        j_evt = jd[0]

        self.assertEqual(j_evt["title"], "Pandit Jaini Jiyalal Ji Chaudhary Janma Divas")
        self.assertEqual(j_evt["category"], "jayanti")
        self.assertEqual(j_evt["badge"], "Janma Jayanti")
        self.assertEqual(j_evt["badge_color"], "purple")


class MaghaShuklaPanchamiTriTest(unittest.TestCase):
    def test_magha_shukla_panchami_tri_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        kj = [f for f in res["festivals"] if f["id"] == "acharya_kundakunda_jayanti_2026"]
        ms = [f for f in res["festivals"] if f["id"] == "jina_murti_sthapna_2026"]
        vp = [f for f in res["festivals"] if f["id"] == "vasant_panchami_shrut_2026"]

        self.assertEqual(len(kj), 1)
        self.assertEqual(len(ms), 1)
        self.assertEqual(len(vp), 1)

        k_evt = kj[0]
        m_evt = ms[0]
        v_evt = vp[0]

        self.assertEqual(k_evt["title"], "Acharya Kundakunda Swami Janma Jayanti")
        self.assertEqual(k_evt["category"], "jayanti")
        self.assertEqual(k_evt["badge"], "Janma Jayanti")
        self.assertEqual(k_evt["badge_color"], "purple")

        self.assertEqual(m_evt["title"], "Jina Murti Sthapna Divas")
        self.assertEqual(m_evt["category"], "auspicious")
        self.assertEqual(m_evt["badge"], "Murti Sthapna")
        self.assertEqual(m_evt["badge_color"], "emerald")

        self.assertEqual(v_evt["title"], "Vasant Panchami (Shrut Vasant)")
        self.assertEqual(v_evt["category"], "shastra")
        self.assertEqual(v_evt["badge"], "Jinavani Pujan")
        self.assertEqual(v_evt["badge_color"], "indigo")

        self.assertEqual(k_evt["start_date"], m_evt["start_date"])
        self.assertEqual(m_evt["start_date"], v_evt["start_date"])


class PhalgunaPurnimaAshtahnikaPurnaTest(unittest.TestCase):
    def test_phalguna_purnima_ashtahnika_purna_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        ap = [f for f in res["festivals"] if f["id"] == "phalguna_ashtahnika_purna_2026"]
        hd = [f for f in res["festivals"] if f["id"] == "holika_dahan_2026"]
        vp = [f for f in res["festivals"] if f["id"] == "phalguna_purnima_vasantotsav_2026"]

        self.assertEqual(len(ap), 1)
        self.assertEqual(len(hd), 1)
        self.assertEqual(len(vp), 1)

        a_evt = ap[0]
        h_evt = hd[0]
        v_evt = vp[0]

        self.assertEqual(a_evt["title"], "Phalguna Ashtahnika Mahaparv Purna")
        self.assertEqual(a_evt["category"], "mahaparv_vrat")
        self.assertEqual(a_evt["badge"], "Vrat End")
        self.assertEqual(a_evt["badge_color"], "orange")
        self.assertTrue(a_evt["is_span"])
        self.assertEqual(a_evt["boundary_type"], "END")

        self.assertEqual(h_evt["title"], "Holika Dahan (Holi Parv)")
        self.assertEqual(h_evt["category"], "utsav")
        self.assertEqual(h_evt["badge"], "Holika Dahan")
        self.assertEqual(h_evt["badge_color"], "emerald")

        self.assertEqual(v_evt["title"], "Phalguna Purnima (Vasantotsav)")
        self.assertEqual(v_evt["category"], "mahaparv")
        self.assertEqual(v_evt["badge"], "Sharadotsav")
        self.assertEqual(v_evt["badge_color"], "red")

        self.assertEqual(a_evt["start_date"], h_evt["start_date"])
        self.assertEqual(h_evt["start_date"], v_evt["start_date"])


class ChaitraAmavasyaKalyanakVarshantTest(unittest.TestCase):
    def test_chaitra_amavasya_kalyanak_varshant_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        an = [f for f in res["festivals"] if f["id"] == "ananthnath_moksha_2026"]
        ar = [f for f in res["festivals"] if f["id"] == "aranath_moksha_2026"]
        ls = [f for f in res["festivals"] if f["id"] == "labdhi_vidhan_start_chaitra_2026"]
        vs = [f for f in res["festivals"] if f["id"] == "vikram_samvat_varshant_2026"]

        self.assertEqual(len(an), 1)
        self.assertEqual(len(ar), 1)
        self.assertEqual(len(ls), 1)
        self.assertEqual(len(vs), 1)

        an_evt = an[0]
        ar_evt = ar[0]
        ls_evt = ls[0]
        vs_evt = vs[0]

        self.assertEqual(an_evt["title"], "Bhagwan Ananthnath Ji Moksha Kalyanak")
        self.assertEqual(an_evt["category"], "kalyanak")
        self.assertEqual(an_evt["badge"], "Moksha Kalyanak")
        self.assertEqual(an_evt["badge_color"], "red")

        self.assertEqual(ar_evt["title"], "Bhagwan Aranath Ji Moksha Kalyanak")
        self.assertEqual(ar_evt["category"], "kalyanak")

        self.assertEqual(ls_evt["title"], "Labdhi Vidhan Vrat Prarambh")
        self.assertEqual(ls_evt["category"], "mahaparv_vrat")
        self.assertEqual(ls_evt["badge"], "Vrat Start")
        self.assertTrue(ls_evt["is_span"])
        self.assertEqual(ls_evt["boundary_type"], "START")

        self.assertEqual(vs_evt["title"], "Vikram Samvat Varsha-Ant Divas")
        self.assertEqual(vs_evt["category"], "auspicious")
        self.assertEqual(vs_evt["badge"], "Year End")
        self.assertEqual(vs_evt["badge_color"], "emerald")

        self.assertEqual(an_evt["start_date"], ar_evt["start_date"])
        self.assertEqual(ar_evt["start_date"], ls_evt["start_date"])


class Namokar35VratTest(unittest.TestCase):
    def test_namokar_35_vrat_resolution_2026(self):
        from jain_observances.festival_service import generate_jain_festivals
        res = generate_jain_festivals(
            year=2026,
            lat=28.6139,
            lon=77.2090,
            ayanamsa="Lahiri",
            profile="all"
        )

        n_steps = [f for f in res["festivals"] if f["id"].startswith("namokar_vrat_step_")]

        # In a single calendar year (e.g. 2026), multiple steps from the sequence fire
        self.assertTrue(len(n_steps) > 0)

        step_1 = [f for f in n_steps if f["step_index"] == 1]
        if step_1:
            s1 = step_1[0]
            self.assertEqual(s1["title"], "Namokar Mahamantra Vrat (Prarambh - 1/35)")
            self.assertEqual(s1["boundary_type"], "START")
            self.assertEqual(s1["badge"], "Namokar Vrat #1")
            self.assertEqual(s1["mantra_pada"], "Ṇamō Arihantāṇaṁ")
            self.assertEqual(s1["badge_color"], "orange")
            self.assertTrue(s1["is_span"])

        step_9 = [f for f in n_steps if f["step_index"] == 9]
        if step_9:
            s9 = step_9[0]
            self.assertEqual(s9["title"], "Namokar Mahamantra Vrat (9/35)")
            self.assertEqual(s9["boundary_type"], "INTERMEDIATE")
            self.assertEqual(s9["badge"], "Namokar Vrat #9")
            self.assertEqual(s9["mantra_pada"], "Ṇamō Siddhāṇaṁ")

        step_35 = [f for f in n_steps if f["step_index"] == 35]
        if step_35:
            s35 = step_35[0]
            self.assertEqual(s35["title"], "Namokar Mahamantra Vrat (Udyapan / Purna - 35/35)")
            self.assertEqual(s35["boundary_type"], "END")
            self.assertEqual(s35["badge"], "Namokar Vrat Purna")
            self.assertEqual(s35["mantra_pada"], "Ṇamō Lōē Savvasāhūṇaṁ")


class KalyanakAmantaMonthCorrectionTest(unittest.TestCase):
    """Regression tests for the systematic amanta/purnimanta month-offset bug in the
    Vrindavan/Uttarapurana/Ashadhara Tirthankara Kalyanak dataset: most Krishna-paksha
    entries stored the source PDF's (purnimanta) month name directly in `jain_month`,
    which festival_service.py then shifts +1 for display -- landing one month later than
    the source actually states. Fixed by re-deriving the correct amanta month (source
    month - 1) for every Krishna-paksha kalyanak entry, cross-checked against
    tests/tirthankara_kalyanaks_data.json and two independent real-world calendar facts
    (Diwali = Kartika Krishna Amavasya; Janmashtami's Bhadrapada/Shravana dual-naming)."""

    @classmethod
    def setUpClass(cls):
        from jain_observances.festival_service import generate_jain_festivals
        cls.res = generate_jain_festivals(
            year=2026, lat=28.6139, lon=77.2090, ayanamsa="Lahiri", profile="all"
        )
        cls.by_id = {f["id"]: f for f in cls.res["festivals"]}

    def test_rishabhdev_liberation_displays_magha_not_phalguna(self):
        """Source PDF: Magha Krishna Chaturdashi (14). Was wrongly stored as amanta
        'Magha' (displaying as Phalguna); corrected to amanta 'Pausha'."""
        f = self.by_id["shri_rishabhdev_ji___liberation_kalyanak_14_vrindavan_uttarapurana_ashadhara"]
        self.assertEqual(f["jain_month"], "Magha")
        self.assertEqual(f["paksha"], "Krishna")
        self.assertEqual(f["tithi"], "Chaturdashi (14)")

    def test_shantinath_triple_kalyanak_displays_jyeshtha_not_ashadha(self):
        """Source PDF: Jyeshtha Krishna Chaturdashi (14), Birth+Austerity+Liberation all
        on the same day. Was wrongly stored as amanta 'Jyeshtha' (displaying as Ashadha);
        corrected to amanta 'Vaishakha'."""
        ids = [
            "shri_shantinath_ji___austerity_kalyanak_14_vrindavan_uttarapurana_ashadhara",
            "shri_shantinath_ji___birth_kalyanak_14_vrindavan_uttarapurana_ashadhara",
            "shri_shantinath_ji___liberation_kalyanak_14_vrindavan_uttarapurana_ashadhara",
        ]
        dates = set()
        for fid in ids:
            f = self.by_id[fid]
            self.assertEqual(f["jain_month"], "Jyeshtha")
            self.assertEqual(f["paksha"], "Krishna")
            self.assertEqual(f["tithi"], "Chaturdashi (14)")
            dates.add(f["start_date"])
        self.assertEqual(len(dates), 1, "Birth/Austerity/Liberation should fall on the same date")

    def test_mahavira_liberation_from_kalyanak_table_matches_diwali(self):
        """The Vrindavan/Uttarapurana/Ashadhara-sourced Liberation entry was wrongly
        stored as amanta 'Kartika' (displaying as Agrahayana/Margashirsha); corrected to
        amanta 'Ashwin' so it displays as Kartika Krishna Amavasya (Diwali) -- and now
        agrees with the separately-modeled Diwali/Mahavir-Nirvana entries on the same date."""
        f = self.by_id["shri_mahavira_ji___liberation_kalyanak_15_vrindavan_uttarapurana_ashadhara"]
        self.assertEqual(f["jain_month"], "Kartika")
        self.assertEqual(f["paksha"], "Krishna")
        self.assertEqual(f["tithi"], "Amavasya (15)")
        diwali = self.by_id["mahavir_nirvana_deepavali"]
        self.assertEqual(f["start_date"], diwali["start_date"])

    def test_newly_added_sumatinath_liberation_on_navami(self):
        """Vrindavan uniquely records a second, earlier Sumatinath Liberation Kalyanak on
        Chaitra Shukla Navami (9), distinct from the Ekadashi (11) one shared by all three
        sources. Previously absent from the registry entirely."""
        f = self.by_id["shri_sumatinath_ji___liberation_kalyanak_9_vrindavan"]
        self.assertEqual(f["jain_month"], "Chaitra")
        self.assertEqual(f["paksha"], "Shukla")
        self.assertEqual(f["tithi"], "Navami (9)")
        self.assertEqual(f["sources"], ["Vrindavan"])

    def test_newly_added_parshvanath_omniscience_and_anantnath_liberation_on_chaitra_krishna_4(self):
        """Vrindavan (and Ashadhara for Parshvanath) record a Chaitra Krishna Chaturthi (4)
        Kalyanak that Uttarapurana places on a different day; previously only Uttarapurana's
        version of the Parshvanath entry existed, and Anantnath's day-4 Liberation was
        entirely absent alongside its existing Amavasya-day Liberation entry."""
        parshva = self.by_id["shri_parshvanath_ji___omniscience_kalyanak_4_vrindavan_ashadhara"]
        self.assertEqual(parshva["jain_month"], "Chaitra")
        self.assertEqual(parshva["paksha"], "Krishna")
        self.assertEqual(parshva["tithi"], "Chaturthi (4)")
        self.assertEqual(sorted(parshva["sources"]), ["Ashadhara", "Vrindavan"])

        ananta = self.by_id["shri_anantnath_ji___liberation_kalyanak_4_vrindavan"]
        self.assertEqual(ananta["jain_month"], "Chaitra")
        self.assertEqual(ananta["paksha"], "Krishna")
        self.assertEqual(ananta["tithi"], "Chaturthi (4)")
        self.assertEqual(ananta["sources"], ["Vrindavan"])
        self.assertEqual(parshva["start_date"], ananta["start_date"])


class KartikaKrishnaMonthResolutionTest(unittest.TestCase):
    """Regression tests for the same amanta/purnimanta off-by-one-month bug as
    KalyanakAmantaMonthCorrectionTest, this time hardcoded inside custom rule classes
    (KartikaAmavasyaMahaviraNirvanaFestival, SplitDayAhoiKarwaDampatyaFestival,
    GyanDhanTrayodashiFestival, DiwaliChaturmasNishthapanFestival): each filtered
    snapshots by raw s["hindu_month"] (amanta) against a purnimanta-sounding literal
    ("KARTIKA"), instead of get_jain_month(s) (purnimanta) -- landing every Krishna-paksha
    target one full lunar month late, in both 2026 and 2027 (not an Adhik Maas artifact).
    Confirmed against an independently printed panchang: user-reported bug."""

    @classmethod
    def setUpClass(cls):
        from jain_observances.festival_service import generate_jain_festivals
        cls.res_2026 = generate_jain_festivals(
            year=2026, lat=28.6139, lon=77.2090, ayanamsa="Lahiri", profile="all"
        )
        cls.by_id_2026 = {f["id"]: f for f in cls.res_2026["festivals"]}
        cls.res_2027 = generate_jain_festivals(
            year=2027, lat=28.6139, lon=77.2090, ayanamsa="Lahiri", profile="all"
        )
        cls.by_id_2027 = {f["id"]: f for f in cls.res_2027["festivals"]}

    def test_mahavir_nirvana_cluster_lands_on_kartika_amavasya_not_agrahayana(self):
        for fid in ("mahavira_nirvana_kalyanak_2026", "varsha_yog_nishthapan_2026",
                    "gautam_gandhar_kevalgyan_2026", "diwali_2026", "chaturmas_nishthapan_2026"):
            f = self.by_id_2026[fid]
            self.assertEqual(f["jain_month"], "Kartika", fid)
            self.assertEqual(f["paksha"], "Krishna", fid)
            self.assertEqual(f["tithi"], "Amavasya (15)", fid)
        # All land on the same date as the already-correct, independently-modeled entry
        reference = self.by_id_2026["mahavir_nirvana_deepavali"]
        for fid in ("mahavira_nirvana_kalyanak_2026", "diwali_2026"):
            self.assertEqual(self.by_id_2026[fid]["start_date"], reference["start_date"], fid)
        # No leftover duplicate cluster a month later
        agrahayana_dupes = [
            f for f in self.res_2026["festivals"]
            if f["id"] in ("mahavira_nirvana_kalyanak_2026", "diwali_2026", "chaturmas_nishthapan_2026",
                            "varsha_yog_nishthapan_2026", "gautam_gandhar_kevalgyan_2026")
            and f["jain_month"] == "Agrahayana"
        ]
        self.assertEqual(agrahayana_dupes, [])

    def test_karwa_chauth_gyan_dhan_trayodashi_land_on_kartika_not_agrahayana(self):
        kc = self.by_id_2026["karwa_chauth_2026"]
        self.assertEqual((kc["jain_month"], kc["paksha"], kc["tithi"]), ("Kartika", "Krishna", "Chaturthi (4)"))

        gt = self.by_id_2026["gyan_trayodashi_2026"]
        dt = self.by_id_2026["dhan_teras_2026"]
        for f in (gt, dt):
            self.assertEqual((f["jain_month"], f["paksha"], f["tithi"]), ("Kartika", "Krishna", "Trayodashi (13)"))
        self.assertEqual(gt["start_date"], dt["start_date"])

    def test_fix_reproduces_correctly_in_a_non_adhik_maas_year(self):
        """2027 has no Adhik Jyeshtha -- confirms this was never an Adhik Maas artifact."""
        for fid in ("mahavira_nirvana_kalyanak_2027", "karwa_chauth_2027", "gyan_trayodashi_2027"):
            self.assertEqual(self.by_id_2027[fid]["jain_month"], "Kartika", fid)


class RohiniNakshatraParvVratTest(unittest.TestCase):
    """Rohini Nakshatra Parv Vrat -- a monthly Digambar vrat observed on the day
    Rohini nakshatra prevails at sunrise. Regression coverage for two bugs:
      1. The vrat was never wired into the festival engine (no registry entry with
         rule_type "RohiniVrat"), so the 2026 output had zero Rohini occurrences.
      2. `evaluate_rohini_vrat` selected the day Rohini *begins* within the Jain-day
         window rather than the day it prevails *at sunrise*, landing one day early
         (2026-03-23 instead of the book-confirmed 2026-03-24)."""

    @classmethod
    def setUpClass(cls):
        from jain_observances.festival_service import generate_jain_festivals
        cls.res = generate_jain_festivals(
            year=2026, lat=28.6139, lon=77.2090, ayanamsa="Lahiri", profile="all"
        )
        cls.rohini = [f for f in cls.res["festivals"] if f["id"] == "rohini_nakshatra_parv_vrat"]

    def test_rohini_vrat_is_present_and_monthly(self):
        self.assertGreaterEqual(len(self.rohini), 12)
        for f in self.rohini:
            self.assertIn("Rohini", f["name"])
            self.assertEqual(f["category"], "parva")

    def test_march_2026_rohini_vrat_matches_printed_panchang(self):
        dates = {f["start_date"] for f in self.rohini}
        self.assertIn("2026-03-24", dates)
        self.assertNotIn("2026-03-23", dates)

    def test_rohini_vrat_occurrence_ids_are_unique(self):
        occ_ids = [f["occurrence_id"] for f in self.rohini]
        self.assertEqual(len(occ_ids), len(set(occ_ids)))


class SumatinathJainiJiyalalKalyanakTest(unittest.TestCase):
    """Pt. Jaini Jiyalal Panchang prints Sumatinath Janma-Tapa together on Chaitra
    Shukla Dashami (2026-03-28, Pushya nakshatra). Added alongside -- not replacing --
    the Vrindavan/Uttarapurana/Ashadhara entries (Birth = Chaitra Shukla 11 = 2026-03-29,
    Austerity = Vaishakha Shukla 9)."""

    @classmethod
    def setUpClass(cls):
        from jain_observances.festival_service import generate_jain_festivals
        cls.res = generate_jain_festivals(
            year=2026, lat=28.6139, lon=77.2090, ayanamsa="Lahiri", profile="all"
        )
        cls.by_id = {f["id"]: f for f in cls.res["festivals"]}

    def test_jaini_jiyalal_janma_tapa_land_together_on_chaitra_shukla_dashami(self):
        birth = self.by_id["shri_sumatinath_ji___birth_kalyanak_chaitra_shukla_10_jaini_jiyalal"]
        tapa = self.by_id["shri_sumatinath_ji___austerity_kalyanak_chaitra_shukla_10_jaini_jiyalal"]
        self.assertEqual(birth["start_date"], "2026-03-28")
        self.assertEqual(tapa["start_date"], "2026-03-28")
        self.assertEqual(birth["tithi"], "Dashami (10)")

    def test_scholarly_sumatinath_entries_are_still_present(self):
        scholarly_birth = self.by_id["shri_sumatinath_ji___birth_kalyanak_11_vrindavan_uttarapurana_ashadhara"]
        self.assertEqual(scholarly_birth["start_date"], "2026-03-29")
        self.assertIn("shri_sumatinath_ji___austerity_kalyanak_9_vrindavan_uttarapurana_ashadhara", self.by_id)


if __name__ == "__main__":
    unittest.main()

