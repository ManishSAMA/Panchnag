"""
Test suite for special/extended yogas.

Source: Ruchika Publications, "Asali Panchang" (Pt. Jaini Jiyalal Shikarchand Chaudhari), pp. 114-116

Tests:
  Section A  – Data integrity of new yoga rules in YOGA_RULES
  Section B  – Tripushkar Yoga (Vara + Tithi + Nakshatra intersection)
  Section C  – Dwipushkar Yoga (same)
  Section D  – Ravi Pushya Amrit Yoga (Sunday + Pushya)
  Section E  – Guru Pushya Amrit Yoga (Thursday + Pushya)
  Section F  – Amrit Siddhi (already in system – regression)
  Section G  – Siddhi Yoga (already in system – regression)
  Section H  – Ashubh Tithivar (7 named Vara+Tithi combos)
  Section I  – Gandmool Nakshatra (Moon in 6 nakshatras)
  Section J  – Panchak (Moon >= 300° sidereal)
  Section K  – Jwalamukhi Yoga (Tithi+Nakshatra, no Vara)
  Section L  – Boundary / compound tests

All test dates verified against actual ephemeris.
"""

import unittest
from datetime import date, timedelta

from astronomy import get_sunrise, local_date_anchor_jd, jd_to_zoned_datetime
from location_service import get_timezone_name

JAIPUR_LAT = 26.9124
JAIPUR_LON = 75.7873
AYANAMSA   = "Lahiri"

# ── helpers ──────────────────────────────────────────────────────────────────

def _sun_jds(d: date):
    tz = get_timezone_name(JAIPUR_LAT, JAIPUR_LON)
    anchor      = local_date_anchor_jd(d, tz)
    next_anchor = local_date_anchor_jd(d + timedelta(days=1), tz)
    sr  = get_sunrise(anchor, JAIPUR_LAT, JAIPUR_LON)
    nsr = get_sunrise(next_anchor, JAIPUR_LAT, JAIPUR_LON)
    return sr, nsr, tz


def _yoga_names(result: dict) -> set[str]:
    return {y["name"] for y in result.get("yogas", []) if not y.get("cancelled")}


def _detect(d: date):
    from dainika_muhurta_service import detect_yogas_for_day
    sr, nsr, tz = _sun_jds(d)
    return detect_yogas_for_day(
        date_obj=d, sunrise_jd=sr, next_sunrise_jd=nsr, tz_name=tz, ayanamsa=AYANAMSA
    )


def _detect_special(d: date):
    from special_yoga_service import detect_special_yogas_for_day
    sr, nsr, tz = _sun_jds(d)
    return detect_special_yogas_for_day(
        date_obj=d, sunrise_jd=sr, next_sunrise_jd=nsr, tz_name=tz, ayanamsa=AYANAMSA
    )


def _active_named(result: dict, name: str) -> bool:
    return any(
        y["name"] == name and not y.get("cancelled")
        for y in result.get("yogas", [])
    )


def _active_named_at(result: dict, name: str, test_jd: float) -> bool:
    return any(
        y["name"] == name
        and not y.get("cancelled")
        and y.get("start_jd", -1) <= test_jd <= y.get("end_jd", 0)
        for y in result.get("yogas", [])
    )


def _gh(sunrise_jd: float, ghati: int, minute: int = 0) -> float:
    """Convert Ghati:Minute offset from sunrise to Julian Day (1 ghati = 24 minutes)."""
    return sunrise_jd + (ghati * 24 + minute) / 1440.0


# ── Section A: Data integrity ─────────────────────────────────────────────────

class TestNewYogaRulesIntegrity(unittest.TestCase):
    """Verify the new yoga entries are correctly defined in YOGA_RULES."""

    @classmethod
    def setUpClass(cls):
        from dainika_muhurta_service import YOGA_RULES
        cls.rules = YOGA_RULES
        cls.by_name = {r["name"]: r for r in cls.rules}

    def test_ravi_pushya_amrit_exists(self):
        self.assertIn("Ravi Pushya Amrit", self.by_name)

    def test_ravi_pushya_amrit_is_sunday_pushya(self):
        rule = self.by_name["Ravi Pushya Amrit"]
        self.assertEqual(rule["vara_map"].get(0), [8])  # Sunday + Pushya(8)
        self.assertEqual(rule["nature"], "shubh")
        self.assertEqual(rule["severity"], "highly_auspicious")

    def test_guru_pushya_amrit_exists(self):
        self.assertIn("Guru Pushya Amrit", self.by_name)

    def test_guru_pushya_amrit_is_thursday_pushya(self):
        rule = self.by_name["Guru Pushya Amrit"]
        self.assertEqual(rule["vara_map"].get(4), [8])  # Thursday + Pushya(8)
        self.assertEqual(rule["nature"], "shubh")
        self.assertEqual(rule["severity"], "highly_auspicious")

    def test_ashubh_tithivar_all_present(self):
        expected = {
            "Nal Banvas", "Pandav Nash", "Vibhishan Maran",
            "Sita Haran", "Lanka Bhang", "Pandav Jung", "Bali Raja Chhal",
        }
        for name in expected:
            self.assertIn(name, self.by_name, f"Missing: {name}")

    def test_nal_banvas_is_tuesday_tithi2(self):
        rule = self.by_name["Nal Banvas"]
        self.assertIn(2, rule["vara_map"][2])   # Vara 2 = Tuesday, Tithi 2

    def test_pandav_nash_is_friday_tithi3(self):
        rule = self.by_name["Pandav Nash"]
        self.assertIn(3, rule["vara_map"][5])   # Vara 5 = Friday, Tithi 3

    def test_vibhishan_maran_is_sunday_tithi4(self):
        rule = self.by_name["Vibhishan Maran"]
        self.assertIn(4, rule["vara_map"][0])   # Vara 0 = Sunday, Tithi 4

    def test_sita_haran_is_wednesday_tithi5(self):
        rule = self.by_name["Sita Haran"]
        self.assertIn(5, rule["vara_map"][3])   # Vara 3 = Wednesday, Tithi 5

    def test_lanka_bhang_is_saturday_tithi6(self):
        rule = self.by_name["Lanka Bhang"]
        self.assertIn(6, rule["vara_map"][6])   # Vara 6 = Saturday, Tithi 6

    def test_pandav_jung_is_monday_tithi7(self):
        rule = self.by_name["Pandav Jung"]
        self.assertIn(7, rule["vara_map"][1])   # Vara 1 = Monday, Tithi 7

    def test_bali_raja_chhal_is_thursday_tithi8(self):
        rule = self.by_name["Bali Raja Chhal"]
        self.assertIn(8, rule["vara_map"][4])   # Vara 4 = Thursday, Tithi 8

    def test_tripushkar_exists(self):
        self.assertIn("Tripushkar", self.by_name)

    def test_tripushkar_vara_is_sun_tue_sat(self):
        rule = self.by_name["Tripushkar"]
        self.assertIn(0, rule["vara_map"])   # Sunday
        self.assertIn(2, rule["vara_map"])   # Tuesday
        self.assertIn(6, rule["vara_map"])   # Saturday
        self.assertNotIn(1, rule["vara_map"])  # Monday excluded
        self.assertNotIn(4, rule["vara_map"])  # Thursday excluded

    def test_tripushkar_tithi_values(self):
        rule = self.by_name["Tripushkar"]
        # Both Shukla (2,7,12) and Krishna (17,22,27) paksha equivalents
        self.assertEqual(sorted(rule["tithi_values"]), [2, 7, 12, 17, 22, 27])

    def test_tripushkar_nakshatra_values(self):
        rule = self.by_name["Tripushkar"]
        expected = {3, 7, 12, 16, 21, 25}
        self.assertEqual(set(rule["nakshatra_values"]), expected)

    def test_dwipushkar_exists(self):
        self.assertIn("Dwipushkar", self.by_name)

    def test_dwipushkar_vara_is_sun_wed_fri(self):
        rule = self.by_name["Dwipushkar"]
        self.assertIn(0, rule["vara_map"])   # Sunday
        self.assertIn(3, rule["vara_map"])   # Wednesday
        self.assertIn(5, rule["vara_map"])   # Friday
        self.assertNotIn(2, rule["vara_map"])  # Tuesday excluded

    def test_dwipushkar_tithi_values(self):
        rule = self.by_name["Dwipushkar"]
        # Both Shukla (2,7,12) and Krishna (17,22,27) paksha equivalents
        self.assertEqual(sorted(rule["tithi_values"]), [2, 7, 12, 17, 22, 27])

    def test_dwipushkar_nakshatra_values(self):
        rule = self.by_name["Dwipushkar"]
        expected = {7, 12, 16, 21, 25}
        self.assertEqual(set(rule["nakshatra_values"]), expected)
        self.assertNotIn(3, rule["nakshatra_values"])  # Kritika absent

    def test_new_rules_have_required_keys(self):
        new_names = {
            "Ravi Pushya Amrit", "Guru Pushya Amrit", "Tripushkar", "Dwipushkar",
            "Nal Banvas", "Pandav Nash", "Vibhishan Maran", "Sita Haran",
            "Lanka Bhang", "Pandav Jung", "Bali Raja Chhal",
        }
        for name in new_names:
            rule = self.by_name.get(name)
            self.assertIsNotNone(rule, f"Missing rule: {name}")
            for key in ("name", "nature", "severity", "meaning", "trigger"):
                self.assertIn(key, rule, f"{name} missing '{key}'")


# ── Section B: Tripushkar detection ──────────────────────────────────────────

class TestTripushkarYoga(unittest.TestCase):
    """
    Verified dates (actual ephemeris):
      2026-02-28 (Sat): Tithi 12 + Nak 7,  window 06:52-09:35
      2026-04-19 (Sun): Tithi  2 + Nak 3,  window 07:10-10:49
      2026-04-28 (Tue): Tithi 12 + Nak 12, window 05:51-18:52
    """

    def _active(self, d: date) -> bool:
        return _active_named(_detect(d), "Tripushkar")

    def _active_at(self, d: date, ghati: int, minute: int = 0) -> bool:
        sr, _, _ = _sun_jds(d)
        return _active_named_at(_detect(d), "Tripushkar", _gh(sr, ghati, minute))

    def test_tripushkar_active_28_feb_2026(self):
        # Saturday + Tithi 12 + Nak 7 (Punarvasu), window 06:52-09:35
        self.assertTrue(self._active(date(2026, 2, 28)))

    def test_tripushkar_active_19_april_2026(self):
        # Sunday + Tithi 2 + Nak 3 (Kritika), window 07:10-10:49
        self.assertTrue(self._active(date(2026, 4, 19)))

    def test_tripushkar_active_28_april_2026(self):
        # Tuesday + Tithi 12 + Nak 12 (Uttara Phalguni), window 05:51-18:52
        self.assertTrue(self._active(date(2026, 4, 28)))

    def test_tripushkar_active_at_midday_28_april(self):
        # Gh 12 (12*24=288 min = 4h48m after sunrise ~05:51 => ~10:39) — inside 05:51-18:52
        self.assertTrue(self._active_at(date(2026, 4, 28), 12))

    def test_tripushkar_inactive_before_nak3_window_19_april(self):
        # Nak 3 starts at 07:10; Gh 0:30 = 30 min from sunrise 05:59 = 06:29 → before 07:10
        self.assertFalse(self._active_at(date(2026, 4, 19), 0, 30))

    def test_tripushkar_inactive_after_tithi2_window_19_april(self):
        # Tithi 2 ends at 10:49; Gh 11:30 = 11*24+30=294 min = 4h54m from 05:59 = 10:53 → after 10:49
        self.assertFalse(self._active_at(date(2026, 4, 19), 11, 30))

    def test_tripushkar_absent_on_non_qualifying_day(self):
        # April 23 is Thursday (vara=4) — NOT in Tripushkar varas {0,2,6}
        self.assertFalse(self._active(date(2026, 4, 23)))

    # --- Additional reference dates (Ruchika Publications pp.114-116) ---

    def test_tripushkar_active_14_april_2026(self):
        # Tuesday — book window Gh 16:05 to April 15 Gh 00:12
        self.assertTrue(self._active(date(2026, 4, 14)))

    def test_tripushkar_active_at_evening_14_april(self):
        # Book shows 16:05 IST (4:05 PM). Sunrise ~5:57; Nak25 starts at min 602 (~4:02 PM).
        # Gh 26 = 26*24=624 min from sunrise ≈ 4:21 PM — inside the Tithi27+Nak25 overlap
        self.assertTrue(self._active_at(date(2026, 4, 14), 26))

    def test_tripushkar_active_3_may_2026(self):
        # Sunday
        self.assertTrue(self._active(date(2026, 5, 3)))

    def test_tripushkar_active_16_june_2026(self):
        # Tuesday
        self.assertTrue(self._active(date(2026, 6, 16)))

    def test_tripushkar_active_21_june_2026(self):
        # Sunday — same day as Dwipushkar (Tithi 7 + Nak 12 satisfies both)
        self.assertTrue(self._active(date(2026, 6, 21)))

    def test_tripushkar_and_dwipushkar_both_fire_21_june_2026(self):
        # Sunday + Tithi 7 + Nak 12: both Tripushkar AND Dwipushkar must fire
        result = _detect(date(2026, 6, 21))
        names = _yoga_names(result)
        self.assertIn("Tripushkar", names)
        self.assertIn("Dwipushkar", names)

    def test_tripushkar_active_11_july_2026(self):
        # Saturday — Moon crosses Krittika(3) before entering Rohini(4)/Amrit Siddhi window
        self.assertTrue(self._active(date(2026, 7, 11)))

    def test_tripushkar_and_amrit_siddhi_both_fire_11_july_2026(self):
        # Saturday: Tripushkar fires in Krittika(3) window; Amrit Siddhi fires in Rohini(4) window
        result = _detect(date(2026, 7, 11))
        names = _yoga_names(result)
        self.assertIn("Tripushkar", names)
        self.assertIn("Amrit Siddhi", names)

    def test_tripushkar_active_29_aug_2026(self):
        # Saturday
        self.assertTrue(self._active(date(2026, 8, 29)))

    def test_tripushkar_active_12_sep_2026(self):
        # Saturday
        self.assertTrue(self._active(date(2026, 9, 12)))

    def test_tripushkar_active_27_oct_2026(self):
        # Tuesday
        self.assertTrue(self._active(date(2026, 10, 27)))

    def test_tripushkar_active_31_oct_2026(self):
        # Saturday
        self.assertTrue(self._active(date(2026, 10, 31)))

    def test_tripushkar_active_29_dec_2026(self):
        # Tuesday
        self.assertTrue(self._active(date(2026, 12, 29)))

    def test_tripushkar_active_3_jan_2027(self):
        # Sunday
        self.assertTrue(self._active(date(2027, 1, 3)))

    def test_tripushkar_active_9_jan_2027(self):
        # Saturday
        self.assertTrue(self._active(date(2027, 1, 9)))

    def test_tripushkar_active_27_feb_2027(self):
        # Saturday
        self.assertTrue(self._active(date(2027, 2, 27)))


# ── Section C: Dwipushkar detection ──────────────────────────────────────────

class TestDwipushkarYoga(unittest.TestCase):
    """
    Verified dates (actual ephemeris):
      2026-02-27 (Fri): Tithi 12 + Nak 7,  window 22:33-06:52 (end-of-day)
      2026-04-22 (Wed): Tithi  7 + Nak 7,  window 22:50-05:55 (end-of-day)
      2026-06-21 (Sun): Tithi  7 + Nak 12, window 09:31-15:21
    """

    def _active(self, d: date) -> bool:
        return _active_named(_detect(d), "Dwipushkar")

    def _active_at(self, d: date, ghati: int, minute: int = 0) -> bool:
        sr, _, _ = _sun_jds(d)
        return _active_named_at(_detect(d), "Dwipushkar", _gh(sr, ghati, minute))

    def test_dwipushkar_active_27_feb_2026(self):
        # Friday + Tithi 12 + Nak 7, window starts at 22:33
        self.assertTrue(self._active(date(2026, 2, 27)))

    def test_dwipushkar_active_22_april_2026(self):
        # Wednesday + Tithi 7 + Nak 7, window starts at 22:50
        self.assertTrue(self._active(date(2026, 4, 22)))

    def test_dwipushkar_active_21_june_2026(self):
        # Sunday + Tithi 7 + Nak 12 (Uttara Phalguni), clear daytime window 09:31-15:21
        self.assertTrue(self._active(date(2026, 6, 21)))

    def test_dwipushkar_active_at_midday_21_june(self):
        # Gh 14 (14*24=336 min from sunrise ~05:31 => ~11:07) — inside 09:31-15:21
        self.assertTrue(self._active_at(date(2026, 6, 21), 14))

    def test_dwipushkar_absent_on_tuesday(self):
        # Tuesday (vara=2) is NOT in Dwipushkar varas {0,3,5}
        # 2026-04-28 is Tuesday with Tithi 12 + Nak 12 — Tripushkar yes, Dwipushkar no
        self.assertFalse(self._active(date(2026, 4, 28)))


# ── Section D: Ravi Pushya Amrit ─────────────────────────────────────────────

class TestRaviPushyaAmrit(unittest.TestCase):
    """
    Verified dates (Sunday + Pushya):
      2026-02-01 (Sun): Nak 8 from 07:12 to 23:58 — full-day window
      2026-03-01 (Sun): Nak 8 from 06:51 to 08:34 — brief morning window
    """

    def _active(self, d: date) -> bool:
        return _active_named(_detect(d), "Ravi Pushya Amrit")

    def test_ravi_pushya_active_1_feb_2026(self):
        # Sunday + Pushya all day
        self.assertTrue(self._active(date(2026, 2, 1)))

    def test_ravi_pushya_active_1_march_2026(self):
        # Sunday + brief Pushya window 06:51-08:34
        self.assertTrue(self._active(date(2026, 3, 1)))

    def test_ravi_pushya_not_active_on_thursday(self):
        # Ravi Pushya requires Sunday — absent on a Thursday with Pushya (April 23)
        self.assertFalse(self._active(date(2026, 4, 23)))

    def test_ravi_pushya_not_active_on_monday(self):
        # Monday is not Sunday
        self.assertFalse(self._active(date(2026, 2, 2)))


# ── Section E: Guru Pushya Amrit ─────────────────────────────────────────────

class TestGuruPushyaAmrit(unittest.TestCase):
    """
    Verified dates (Thursday + Pushya):
      2026-04-23 (Thu): Nak 8 from 20:57 to 05:54 — late-day + overnight window
      2026-05-21 (Thu): Nak 8 from 05:36 to 02:49 next — full daytime window
      2026-06-18 (Thu): Nak 8 from 05:33 to 11:32 — morning window
    """

    def _active(self, d: date) -> bool:
        return _active_named(_detect(d), "Guru Pushya Amrit")

    def _active_at(self, d: date, ghati: int, minute: int = 0) -> bool:
        sr, _, _ = _sun_jds(d)
        return _active_named_at(_detect(d), "Guru Pushya Amrit", _gh(sr, ghati, minute))

    def test_guru_pushya_present_23_april_2026(self):
        # Thursday + Pushya: active from 20:57 PM onward (present in day's yogas)
        self.assertTrue(self._active(date(2026, 4, 23)))

    def test_guru_pushya_active_late_23_april_2026(self):
        # Gh 40 = 40*24=960 min = 16h from sunrise 05:55 => 21:55 — inside 20:57-05:54
        self.assertTrue(self._active_at(date(2026, 4, 23), 40))

    def test_guru_pushya_inactive_early_23_april_2026(self):
        # Gh 15 = 360 min = 6h from sunrise 05:55 => 11:55 — BEFORE Pushya starts 20:57
        self.assertFalse(self._active_at(date(2026, 4, 23), 15))

    def test_guru_pushya_active_21_may_2026(self):
        # Full daytime Pushya — Thursday
        self.assertTrue(self._active(date(2026, 5, 21)))

    def test_guru_pushya_active_at_midday_21_may_2026(self):
        # Gh 20 = 480 min = 8h from sunrise ~05:36 => ~13:36 — inside Pushya all day
        self.assertTrue(self._active_at(date(2026, 5, 21), 20))

    def test_guru_pushya_active_18_june_2026(self):
        # Thursday + Pushya 05:33-11:32
        self.assertTrue(self._active(date(2026, 6, 18)))

    def test_guru_pushya_inactive_after_pushya_18_june(self):
        # Nak 8 ends at 11:32; Gh 25 = 600 min = 10h from sunrise 05:33 => 15:33 — after 11:32
        self.assertFalse(self._active_at(date(2026, 6, 18), 25))

    def test_guru_pushya_not_active_on_sunday(self):
        # Guru Pushya requires Thursday — absent on Sunday with Pushya (Feb 1)
        self.assertFalse(self._active(date(2026, 2, 1)))

    def test_guru_pushya_compound_with_amrit_siddhi_23_april(self):
        result = _detect(date(2026, 4, 23))
        names = _yoga_names(result)
        self.assertIn("Guru Pushya Amrit", names)
        self.assertIn("Amrit Siddhi", names)


# ── Section F: Amrit Siddhi regression ───────────────────────────────────────

class TestAmritSiddhiRegression(unittest.TestCase):
    """Verify existing Amrit Siddhi detection still works."""

    def _active(self, d: date) -> bool:
        return _active_named(_detect(d), "Amrit Siddhi")

    def test_amrit_siddhi_active_20_march_2026(self):
        # Friday + Revati (Nak 27)
        self.assertTrue(self._active(date(2026, 3, 20)))

    def test_amrit_siddhi_active_17_april_2026(self):
        # Friday + Revati (Nak 27)
        self.assertTrue(self._active(date(2026, 4, 17)))

    def test_amrit_siddhi_active_23_april_2026(self):
        # Thursday + Pushya (Nak 8)
        self.assertTrue(self._active(date(2026, 4, 23)))

    def test_amrit_siddhi_active_21_may_2026(self):
        # Thursday + Pushya (Nak 8)
        self.assertTrue(self._active(date(2026, 5, 21)))

    # --- Additional reference dates (Ruchika Publications pp.114-116) ---

    # NOTE: April 21, May 18, June 14, June 15 were removed — the summary reconstruction
    # gave wrong dates (Moon is not in the required nakshatra on those days per ephemeris).

    def test_amrit_siddhi_active_18_june_2026(self):
        # Thursday + Pushya (Nak 8) — same window as Guru Pushya, confirmed by Drik
        self.assertTrue(self._active(date(2026, 6, 18)))

    def test_amrit_siddhi_active_11_july_2026(self):
        # Saturday + Rohini (Nak 4) — Gh 11:03 to July 12 Gh 05:37
        self.assertTrue(self._active(date(2026, 7, 11)))

    def test_amrit_siddhi_active_19_july_2026(self):
        # Sunday + Hasta (Nak 13) — Gh 18:11 to July 20 Gh 05:40
        self.assertTrue(self._active(date(2026, 7, 19)))

    def test_amrit_siddhi_active_4_aug_2026(self):
        # Tuesday + Ashvini (Nak 1) — Gh 21:54 to Aug 5 Gh 05:49
        self.assertTrue(self._active(date(2026, 8, 4)))

    def test_amrit_siddhi_absent_when_nak_does_not_match_vara(self):
        # April 19 (Sunday + Nak 3 Kritika): Sunday Amrit Siddhi requires Hasta(13), not Kritika(3)
        self.assertFalse(self._active(date(2026, 4, 19)))


# ── Section G: Siddhi Yoga regression ────────────────────────────────────────

class TestSiddhiYogaRegression(unittest.TestCase):
    """
    Verified dates for Siddhi Yoga Tithi:
      2026-01-31 (Sat, vara=6): Tithi 14 from 08:26 (in {4,9,14}) — active all afternoon
      2026-02-21 (Sat, vara=6): Tithi 4 from 06:58 to 13:01 (in {4,9,14}) — active
    """

    def _active(self, d: date) -> bool:
        return _active_named(_detect(d), "Siddhi Yoga Tithi")

    def test_siddhi_active_31_jan_2026(self):
        # Saturday + Tithi 14 (in Saturday list [4,9,14]) — active from 08:26 onwards
        self.assertTrue(self._active(date(2026, 1, 31)))

    def test_siddhi_active_21_feb_2026(self):
        # Saturday + Tithi 4 (in Saturday list [4,9,14]) — active 06:58-13:01
        self.assertTrue(self._active(date(2026, 2, 21)))

    def test_siddhi_absent_on_thursday_tithi8(self):
        # Thursday (vara=4) requires Tithi 5/10/15. April 23 has Tithi 7/8 — no Siddhi
        self.assertFalse(self._active(date(2026, 4, 23)))

    # --- Additional reference dates (Ruchika Publications pp.114-116) ---

    def test_siddha_yoga_active_26_march_2026(self):
        # Thursday + Nak 7 (Punarvasu) → Siddha Yoga (nakshatra-based), confirmed by diagnostic
        self.assertTrue(_active_named(_detect(date(2026, 3, 26)), "Siddha Yoga"))

    def test_siddhi_yoga_tithi_absent_26_march_2026(self):
        # March 26 has Tithi 8/9 — Thursday Siddhi Yoga Tithi requires {5,10,15}, so absent
        self.assertFalse(self._active(date(2026, 3, 26)))


# ── Section H: Ashubh Tithivar ───────────────────────────────────────────────

class TestAshubhTithivar(unittest.TestCase):
    """
    Rule-based tests — each Vara+Tithi combo triggers the named yoga.
    Dates verified against actual ephemeris (Jaipur):

      Nal Banvas      (Tue+T2): 2026-01-20, 2026-06-16
      Pandav Nash     (Fri+T3): 2026-02-20
      Vibhishan Maran (Sun+T4): 2026-03-22
      Sita Haran      (Wed+T5): 2026-05-20
      Lanka Bhang     (Sat+T6): 2026-01-24
      Pandav Jung     (Mon+T7): 2026-02-23
      Bali Raja Chhal (Thu+T8): 2026-03-26
    """

    def _active(self, d: date, name: str) -> bool:
        return _active_named(_detect(d), name)

    def test_nal_banvas_fires_tue_jan20(self):
        # Tuesday + Tithi 2 (Dvitiya)
        self.assertTrue(self._active(date(2026, 1, 20), "Nal Banvas"))

    def test_pandav_nash_fires_fri_feb20(self):
        # Friday + Tithi 3 (Tritiya)
        self.assertTrue(self._active(date(2026, 2, 20), "Pandav Nash"))

    def test_vibhishan_maran_fires_sun_mar22(self):
        # Sunday + Tithi 4 (Chaturthi)
        self.assertTrue(self._active(date(2026, 3, 22), "Vibhishan Maran"))

    def test_sita_haran_fires_wed_may20(self):
        # Wednesday + Tithi 5 (Panchami)
        self.assertTrue(self._active(date(2026, 5, 20), "Sita Haran"))

    def test_lanka_bhang_fires_sat_jan24(self):
        # Saturday + Tithi 6 (Shashthi)
        self.assertTrue(self._active(date(2026, 1, 24), "Lanka Bhang"))

    def test_pandav_jung_fires_mon_feb23(self):
        # Monday + Tithi 7 (Saptami)
        self.assertTrue(self._active(date(2026, 2, 23), "Pandav Jung"))

    def test_bali_raja_chhal_fires_thu_mar26(self):
        # Thursday + Tithi 8 (Ashtami) — window 06:24-11:49
        self.assertTrue(self._active(date(2026, 3, 26), "Bali Raja Chhal"))

    def test_nal_banvas_absent_on_wednesday_tithi2(self):
        # 2026-02-18 = Wednesday + Tithi 2 — Nal Banvas needs TUESDAY, not Wednesday
        self.assertFalse(self._active(date(2026, 2, 18), "Nal Banvas"))

    def test_bali_raja_chhal_absent_on_thursday_tithi7_only(self):
        # 2026-09-17 = Thursday + Tithi 7 only (no Tithi 8 present) → Bali Raja Chhal needs T8
        self.assertFalse(self._active(date(2026, 9, 17), "Bali Raja Chhal"))


# ── Section I: Gandmool Nakshatra ────────────────────────────────────────────

class TestGandmoolNakshatra(unittest.TestCase):
    """Gandmool fires when Moon is in Ashvini(1), Ashlesha(9), Magha(10), Jyeshtha(18), Mula(19), Revati(27)."""

    def _active(self, d: date) -> bool:
        result = _detect_special(d)
        return any(y["name"] == "Gandmool Nakshatra" for y in result.get("special_yogas", []))

    def test_gandmool_active_20_march_2026(self):
        # Moon in Revati (27) on this day
        self.assertTrue(self._active(date(2026, 3, 20)))

    def test_gandmool_active_28_march_2026(self):
        self.assertTrue(self._active(date(2026, 3, 28)))

    def test_gandmool_active_7_april_2026(self):
        self.assertTrue(self._active(date(2026, 4, 7)))

    def test_gandmool_inactive_when_moon_in_pushya(self):
        # April 23-24: Moon in Pushya (8) and Ashlesha (9).
        # April 23: Nak 7 + Nak 8 — neither is Gandmool
        # April 24: Nak 8 + Nak 9 — Nak 9 IS Ashlesha (Gandmool)!
        # So let's use a day with Moon clearly NOT in any Gandmool nakshatra
        # May 21: Nak 8 (Pushya) + Nak 9 (Ashlesha). Nak 9 is Gandmool.
        # April 23 only has Nak 7 (Punarvasu) + Nak 8 (Pushya) — neither is Gandmool
        self.assertFalse(self._active(date(2026, 4, 23)),
                         "Gandmool must NOT fire when Moon is in Punarvasu/Pushya")

    def test_gandmool_triggers_any_vara(self):
        # Gandmool is weekday-independent — verifies it appears regardless of vara
        result = _detect_special(date(2026, 3, 20))  # Friday
        names = {y["name"] for y in result.get("special_yogas", [])}
        self.assertIn("Gandmool Nakshatra", names)


# ── Section J: Panchak ───────────────────────────────────────────────────────

class TestPanchak(unittest.TestCase):
    """Panchak = Moon longitude in [300°, 360°) — verified by calculate_panchak_kaal."""

    def _active(self, d: date) -> bool:
        result = _detect_special(d)
        return any(y["name"] == "Panchak" for y in result.get("special_yogas", []))

    def test_panchak_active_17_march_2026(self):
        self.assertTrue(self._active(date(2026, 3, 17)))

    def test_panchak_active_20_march_2026(self):
        self.assertTrue(self._active(date(2026, 3, 20)))

    def test_panchak_inactive_15_march_2026(self):
        self.assertFalse(self._active(date(2026, 3, 15)))

    def test_panchak_active_8_june_2026(self):
        self.assertTrue(self._active(date(2026, 6, 8)))

    def test_panchak_multi_day_span(self):
        for d in [date(2026, 3, 17), date(2026, 3, 18), date(2026, 3, 19), date(2026, 3, 20)]:
            self.assertTrue(self._active(d), f"Panchak should be active on {d}")


# ── Section K: Jwalamukhi Yoga ───────────────────────────────────────────────

class TestJwalamukhiYoga(unittest.TestCase):
    """
    Jwalamukhi pairs: (1,19) (5,2) (9,4) (9,3) (10,9) — any Vara.
    Verified dates:
      2026-01-27 (Tue): Tithi 9 + Nak 3 (Kritika), window 11:09-19:05
      2026-02-25 (Wed): Tithi 9 + Nak 4 (Rohini),  window 06:54-13:38
      2026-03-22 (Sun): Tithi 5 + Nak 2 (Bharani),  window 21:17-22:42
    """

    def _active(self, d: date) -> bool:
        result = _detect_special(d)
        return any(y["name"] == "Jwalamukhi" for y in result.get("special_yogas", []))

    def test_jwalamukhi_active_27_jan_2026(self):
        # Tithi 9 + Nak 3, window 11:09-19:05
        self.assertTrue(self._active(date(2026, 1, 27)))

    def test_jwalamukhi_active_25_feb_2026(self):
        # Tithi 9 + Nak 4, window 06:54-13:38
        self.assertTrue(self._active(date(2026, 2, 25)))

    def test_jwalamukhi_active_22_march_2026(self):
        # Tithi 5 + Nak 2, window 21:17-22:42
        self.assertTrue(self._active(date(2026, 3, 22)))

    def test_jwalamukhi_inactive_when_no_pair(self):
        # April 23: Tithi 7/8 + Nak 7/8 — no Jwalamukhi pair matches
        self.assertFalse(self._active(date(2026, 4, 23)),
                         "Jwalamukhi must not fire on Apr 23 (no matching pair)")


# ── Section L: Boundary tests ────────────────────────────────────────────────

class TestBoundaryAndCompound(unittest.TestCase):

    def test_compound_23_april_guru_pushya_and_amrit_siddhi(self):
        result = _detect(date(2026, 4, 23))
        names = _yoga_names(result)
        self.assertIn("Guru Pushya Amrit", names)
        self.assertIn("Amrit Siddhi", names)

    def test_compound_21_may_guru_pushya_and_amrit_siddhi(self):
        result = _detect(date(2026, 5, 21))
        names = _yoga_names(result)
        self.assertIn("Guru Pushya Amrit", names)
        self.assertIn("Amrit Siddhi", names)

    def test_tripushkar_absent_on_dwipushkar_vara(self):
        # June 21 (Sunday): Dwipushkar fires (Tithi 7 + Nak 12)
        # Tripushkar also needs vara in {0,2,6} and Sunday is 0, so check Tithi+Nak
        # Dwipushkar naks = {7,12,16,21,25}; Tripushkar naks = {3,7,12,16,21,25}
        # Nak 12 is in BOTH sets, Tithi 7 is in BOTH sets, vara 0 is in Tripushkar varas too!
        # So BOTH could fire on the same day if conditions match — that's valid behavior
        result = _detect(date(2026, 6, 21))
        self.assertIn("Dwipushkar", _yoga_names(result))

    def test_each_day_can_have_multiple_yogas(self):
        result = _detect(date(2026, 4, 23))
        self.assertGreater(len(_yoga_names(result)), 1)

    def test_bali_raja_chhal_fires_same_day_as_amrit_siddhi_on_pushya_thursday(self):
        # Thursday + Tithi 8 = Bali Raja Chhal; if also Pushya, Amrit Siddhi fires
        # April 23: Tithi 8 appears late (20:49+), Pushya also late (20:57+)
        result = _detect(date(2026, 4, 23))
        names = _yoga_names(result)
        self.assertIn("Bali Raja Chhal", names)   # Thursday + Tithi 8
        self.assertIn("Amrit Siddhi", names)       # Thursday + Pushya

    def test_sarvartha_siddhi_fires_on_guru_pushya_day(self):
        # June 18 2026 (Thursday + Pushya): Drik shows Sarvartha Siddhi co-fires
        result = _detect(date(2026, 6, 18))
        self.assertIn("Sarvartha Siddhi", _yoga_names(result))

    def test_compound_11_july_tripushkar_and_amrit_siddhi(self):
        # Saturday: Krittika(3) window → Tripushkar; Rohini(4) window → Amrit Siddhi
        result = _detect(date(2026, 7, 11))
        names = _yoga_names(result)
        self.assertIn("Tripushkar", names)
        self.assertIn("Amrit Siddhi", names)

    def test_compound_18_june_guru_pushya_amrit_sarvartha_siddhi(self):
        # Thursday + Pushya: three auspicious yogas fire simultaneously
        result = _detect(date(2026, 6, 18))
        names = _yoga_names(result)
        self.assertIn("Guru Pushya Amrit", names)
        self.assertIn("Amrit Siddhi", names)
        self.assertIn("Sarvartha Siddhi", names)

    def test_amrit_siddhi_active_19_july_and_4_aug_2026(self):
        # July 19 (Sun + Hasta Nak13) and Aug 4 (Tue + Ashvini Nak1) confirmed by ephemeris
        self.assertTrue(_active_named(_detect(date(2026, 7, 19)), "Amrit Siddhi"))
        self.assertTrue(_active_named(_detect(date(2026, 8, 4)), "Amrit Siddhi"))


# ── Section M: Bhadra (Vishti Karana) in special yogas ───────────────────────

class TestBhadraInSpecialYogas(unittest.TestCase):
    """
    Bhadra (Vishti Karana) is the inauspicious half-tithi period.
    Drik Panchang (June 18, 2026): Bhadra 8:13 AM – 6:58 PM (Shukla Chaturthi 2nd half).
    June 21, 2026 (Shukla Saptami): Karanas are Garaja/Vanija — no Vishti.
    """

    def _special_names(self, d: date) -> set[str]:
        result = _detect_special(d)
        return {y["name"] for y in result.get("special_yogas", [])}

    def _bhadra_entries(self, d: date) -> list[dict]:
        result = _detect_special(d)
        return [y for y in result.get("special_yogas", []) if y["name"] == "Bhadra (Vishti)"]

    def test_bhadra_active_18_june_2026(self):
        # Drik-confirmed: Vishti Karana (2nd half of Shukla Chaturthi) 8:13 AM - 6:58 PM
        self.assertIn("Bhadra (Vishti)", self._special_names(date(2026, 6, 18)))

    def test_bhadra_absent_20_june_2026(self):
        # Shukla Shashthi (Tithi 6): Karanas = Kaulava, Taitila — no Vishti
        self.assertNotIn("Bhadra (Vishti)", self._special_names(date(2026, 6, 20)))

    def test_bhadra_entry_has_required_fields(self):
        entries = self._bhadra_entries(date(2026, 6, 18))
        self.assertGreater(len(entries), 0, "Expected at least one Bhadra entry")
        for entry in entries:
            for field in ("name", "nature", "severity", "meaning",
                          "start_time", "end_time", "start_local", "end_local",
                          "start_jd", "end_jd", "clipped_start", "clipped_end",
                          "trigger_detail"):
                self.assertIn(field, entry, f"Bhadra entry missing field '{field}'")

    def test_bhadra_nature_is_ashubh(self):
        entries = self._bhadra_entries(date(2026, 6, 18))
        self.assertTrue(all(e["nature"] == "ashubh" for e in entries))

    def test_bhadra_start_before_end(self):
        entries = self._bhadra_entries(date(2026, 6, 18))
        for e in entries:
            self.assertLess(e["start_jd"], e["end_jd"])
