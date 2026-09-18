"""
Reference verification tests for YOGA_RULES in dainika_muhurta_service.py.

Ground truth is the traditional panchang source table (photograph of printed reference).
Every cell in the reference table is encoded here and asserted against detect_yogas().

Nakshatra index mapping (1-based, sidereal):
  1  Ashvini       8  Pushya         15 Swati          22 Shravana
  2  Bharani       9  Ashlesha       16 Vishakha        23 Dhanishtha
  3  Krittika      10 Magha          17 Anuradha        24 Shatabhisha
  4  Rohini        11 Purva Phalguni 18 Jyeshtha        25 Purva Bhadrapada
  5  Mrigashira    12 Uttara Phalguni 19 Mula           26 Uttara Bhadrapada
  6  Ardra         13 Hasta          20 Purva Ashadha   27 Revati
  7  Punarvasu     14 Chitra         21 Uttara Ashadha  28 Abhijit

Vara: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
"""

import unittest

from yoga_engine import detect_yogas

# --------------------------------------------------------------------------
# Helper: neutral tithi/nakshatra values that don't appear in the rules table,
# used when we only care about the other axis.
# --------------------------------------------------------------------------
# Tithi 20 does not appear in any tithi-based yoga row.
_NEUTRAL_TITHI = 20
# Nakshatra 23 (Dhanishtha) only appears for Shubh(Mon) and Mitra(Wed)/Dagdha(Wed).
# We use it for Sunday tests where it triggers nothing, or pick per-test.
_NEUTRAL_NAK = 23


def _yoga_names(vara: int, tithi: int, nakshatra: int) -> set[str]:
    """Return the set of yoga names active for the given triple."""
    return {y["name"] for y in detect_yogas(vara=vara, tithi=tithi, nakshatra=nakshatra)["yogas"]}


# ==========================================================================
# SECTION 1: TITHI-BASED YOGAS
# ==========================================================================


class TestSiddhiYogaTithiReference(unittest.TestCase):
    """Siddhi Yoga Tithi: Sun=none, Mon=none, Tue=3/8/13, Wed=2/7/12,
    Thu=5/10/15, Fri=1/6/11, Sat=4/9/14."""

    def test_sunday_has_no_siddhi_yoga_tithi(self):
        # Reference: Sunday column is "-"
        for t in range(1, 16):
            with self.subTest(tithi=t):
                self.assertNotIn("Siddhi Yoga Tithi", _yoga_names(0, t, _NEUTRAL_NAK))

    def test_monday_has_no_siddhi_yoga_tithi(self):
        for t in range(1, 16):
            with self.subTest(tithi=t):
                self.assertNotIn("Siddhi Yoga Tithi", _yoga_names(1, t, _NEUTRAL_NAK))

    def test_tuesday(self):
        for t in [3, 8, 13]:
            with self.subTest(tithi=t):
                self.assertIn("Siddhi Yoga Tithi", _yoga_names(2, t, _NEUTRAL_NAK))

    def test_wednesday(self):
        for t in [2, 7, 12]:
            with self.subTest(tithi=t):
                self.assertIn("Siddhi Yoga Tithi", _yoga_names(3, t, _NEUTRAL_NAK))

    def test_thursday(self):
        for t in [5, 10, 15]:
            with self.subTest(tithi=t):
                self.assertIn("Siddhi Yoga Tithi", _yoga_names(4, t, _NEUTRAL_NAK))

    def test_friday(self):
        for t in [1, 6, 11]:
            with self.subTest(tithi=t):
                self.assertIn("Siddhi Yoga Tithi", _yoga_names(5, t, _NEUTRAL_NAK))

    def test_saturday(self):
        for t in [4, 9, 14]:
            with self.subTest(tithi=t):
                self.assertIn("Siddhi Yoga Tithi", _yoga_names(6, t, _NEUTRAL_NAK))


class TestDagdhaTithiReference(unittest.TestCase):
    """Dagdha Tithi: Sun=12, Mon=11, Tue=5, Wed=3, Thu=6, Fri=8, Sat=9."""

    _REF = {0: 12, 1: 11, 2: 5, 3: 3, 4: 6, 5: 8, 6: 9}

    def test_fires_for_reference_values(self):
        for vara, tithi in self._REF.items():
            with self.subTest(vara=vara, tithi=tithi):
                self.assertIn("Dagdha Tithi", _yoga_names(vara, tithi, _NEUTRAL_NAK))

    def test_does_not_fire_for_wrong_tithi(self):
        # Use a tithi not in ANY dagdha slot
        for vara in range(7):
            with self.subTest(vara=vara):
                self.assertNotIn("Dagdha Tithi", _yoga_names(vara, 20, _NEUTRAL_NAK))


class TestHutashanTithiReference(unittest.TestCase):
    """Hutashan Tithi: Sun=12, Mon=6, Tue=7, Wed=8, Thu=9, Fri=10, Sat=11."""

    _REF = {0: 12, 1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}

    def test_fires_for_reference_values(self):
        for vara, tithi in self._REF.items():
            with self.subTest(vara=vara, tithi=tithi):
                self.assertIn("Hutashan Tithi", _yoga_names(vara, tithi, _NEUTRAL_NAK))


class TestVishakhyaTithiReference(unittest.TestCase):
    """Vishakhya Tithi: Sun=4, Mon=6, Tue=7, Wed=2, Thu=8, Fri=9, Sat=7."""

    _REF = {0: 4, 1: 6, 2: 7, 3: 2, 4: 8, 5: 9, 6: 7}

    def test_fires_for_reference_values(self):
        for vara, tithi in self._REF.items():
            with self.subTest(vara=vara, tithi=tithi):
                self.assertIn("Vishakhya Tithi", _yoga_names(vara, tithi, _NEUTRAL_NAK))


class TestAdhamTithiReference(unittest.TestCase):
    """Adham Tithi: Sun=7,12, Mon=11, Tue=10, Wed=1,9, Thu=8, Fri=7, Sat=6."""

    _REF = {0: [7, 12], 1: [11], 2: [10], 3: [1, 9], 4: [8], 5: [7], 6: [6]}

    def test_fires_for_reference_values(self):
        for vara, tithis in self._REF.items():
            for tithi in tithis:
                with self.subTest(vara=vara, tithi=tithi):
                    self.assertIn("Adham Tithi", _yoga_names(vara, tithi, _NEUTRAL_NAK))


class TestMrityuYogaTithiReference(unittest.TestCase):
    """Mrityu Yoga Tithi: Sun=1/6/11, Mon=2/7/12, Tue=1/6/11, Wed=3/8/13,
    Thu=4/9/14, Fri=2/7/12, Sat=5/10/15."""

    _REF = {
        0: [1, 6, 11],
        1: [2, 7, 12],
        2: [1, 6, 11],
        3: [3, 8, 13],
        4: [4, 9, 14],
        5: [2, 7, 12],
        6: [5, 10, 15],
    }

    def test_fires_for_reference_values(self):
        for vara, tithis in self._REF.items():
            for tithi in tithis:
                with self.subTest(vara=vara, tithi=tithi):
                    self.assertIn("Mrityu Yoga Tithi", _yoga_names(vara, tithi, _NEUTRAL_NAK))


class TestKrakachTithiReference(unittest.TestCase):
    """Krakach Tithi: Sun=12, Mon=11, Tue=10, Wed=9, Thu=8, Fri=7, Sat=6."""

    _REF = {0: 12, 1: 11, 2: 10, 3: 9, 4: 8, 5: 7, 6: 6}

    def test_fires_for_reference_values(self):
        for vara, tithi in self._REF.items():
            with self.subTest(vara=vara, tithi=tithi):
                self.assertIn("Krakach Tithi", _yoga_names(vara, tithi, _NEUTRAL_NAK))


class TestDushtTithiReference(unittest.TestCase):
    """Dusht Tithi: Sun=1,3,7; Mon=2-11; Tue=3,9,12; Wed=7,9,11;
    Thu=special(nakshatra-based); Fri=none; Sat=11,12,13."""

    def test_sunday(self):
        for t in [1, 3, 7]:
            with self.subTest(tithi=t):
                self.assertIn("Dusht Tithi", _yoga_names(0, t, _NEUTRAL_NAK))

    def test_monday_tithis_2_to_11(self):
        for t in range(2, 12):
            with self.subTest(tithi=t):
                self.assertIn("Dusht Tithi", _yoga_names(1, t, _NEUTRAL_NAK))

    def test_tuesday(self):
        for t in [3, 9, 12]:
            with self.subTest(tithi=t):
                self.assertIn("Dusht Tithi", _yoga_names(2, t, _NEUTRAL_NAK))

    def test_wednesday(self):
        for t in [7, 9, 11]:
            with self.subTest(tithi=t):
                self.assertIn("Dusht Tithi", _yoga_names(3, t, _NEUTRAL_NAK))

    def test_friday_has_no_dusht_tithi(self):
        # Reference shows "-" for Friday
        for t in range(1, 16):
            with self.subTest(tithi=t):
                self.assertNotIn("Dusht Tithi", _yoga_names(5, t, _NEUTRAL_NAK))

    def test_saturday(self):
        for t in [11, 12, 13]:
            with self.subTest(tithi=t):
                self.assertIn("Dusht Tithi", _yoga_names(6, t, _NEUTRAL_NAK))


# ==========================================================================
# SECTION 2: NAKSHATRA-BASED YOGAS (all 7 varas)
# For nakshatra tests we use _NEUTRAL_TITHI=20 so no tithi yoga interferes.
# ==========================================================================

# Reference table for each nakshatra yoga (vara → nakshatra_index)
_REF_VARJIT = {0: 13, 1: 5, 2: 1, 3: 22, 4: 8, 5: 27, 6: 4}   # Wed should be Shravana=22
_REF_UTPAT  = {0: 16, 1: 20, 2: 23, 3: 27, 4: 4, 5: 8, 6: 12}  # Mon should be Purva Ashadha=20
_REF_MRITYU_NAK = {0: 17, 1: 21, 2: 24, 3: 1, 4: 5, 5: 9, 6: 13}
_REF_KAAN   = {0: 18, 1: 28, 2: 25, 3: 2, 4: 6, 5: 10, 6: 14}
_REF_DAGDHA_YOG = {0: 2, 1: 14, 2: 21, 3: 23, 4: 12, 5: 18, 6: 27}
_REF_YAM_GHANT  = {0: 10, 1: 16, 2: 6, 3: 19, 4: 3, 5: 4, 6: 13}
_REF_MUSAL  = {0: 28, 1: 25, 2: 2, 3: 6, 4: 10, 5: 14, 6: 18}
_REF_KAAL_DAND = {0: 2, 1: 6, 2: 10, 3: 14, 4: 18, 5: 28, 6: 25}
_REF_VAJRA  = {0: 9, 1: 13, 2: 17, 3: 21, 4: 24, 5: 1, 6: 5}
_REF_RAKSHAS = {0: 24, 1: 1, 2: 5, 3: 9, 4: 13, 5: 17, 6: 21}  # Sat should be Uttara Ashadha=21
_REF_DHWANKSH = {0: 6, 1: 10, 2: 14, 3: 18, 4: 28, 5: 25, 6: 2}
_REF_DHUMRA = {0: 3, 1: 7, 2: 11, 3: 15, 4: 19, 5: 22, 6: 26}
_REF_GAD    = {0: 22, 1: 26, 2: 3, 3: 7, 4: 11, 5: 15, 6: 19}
_REF_ANAND  = {0: 1, 1: 5, 2: 9, 3: 13, 4: 17, 5: 21, 6: 24}
_REF_SHRIVATSA = {0: 8, 1: 12, 2: 16, 3: 20, 4: 23, 5: 27, 6: 4}
_REF_SAUMYA = {0: 5, 1: 9, 2: 13, 3: 17, 4: 21, 5: 24, 6: 1}
_REF_CHATRA = {0: 11, 1: 15, 2: 19, 3: 22, 4: 26, 5: 3, 6: 7}
_REF_SHUBH  = {0: 20, 1: 23, 2: 27, 3: 4, 4: 8, 5: 12, 6: 16}
_REF_AMRIT  = {0: 21, 1: 24, 2: 1, 3: 5, 4: 9, 5: 13, 6: 17}
_REF_MITRA  = {0: 12, 1: 16, 2: 20, 3: 23, 4: 27, 5: 4, 6: 8}  # Tue should be Purva Ashadha=20
_REF_SIDDHA = {0: 19, 1: 22, 2: 26, 3: 3, 4: 7, 5: 11, 6: 15}
_REF_AMRIT_SIDDHI = {0: 13, 1: 22, 2: 1, 3: 17, 4: 8, 5: 27, 6: 4}

# Sarvartha Siddhi — multi-nakshatra per vara; reading from reference image:
# Sun: Hasta(13), Mula(19), Punarvasu(7), Ashvini(1)
# Mon: Shravana(22), Rohini(4), Mrigashira(5), Pushya(8), Anuradha(17)
# Tue: Ashvini(1), Uttara Bhadrapada(26), Krittika(3), Ashlesha(9)
# Wed: Rohini(4), Krittika(3), Mrigashira(5)
# Thu: Revati(27), Anuradha(17), Ashvini(1), Punarvasu(7), Pushya(8)
# Fri: Revati(27), Anuradha(17), Ashvini(1), Punarvasu(7), Shravana(22)
# Sat: Shravana(22), Rohini(4), Swati(15)
_REF_SARVARTHA: dict[int, list[int]] = {
    0: [13, 19, 7, 1],
    1: [22, 4, 5, 8, 17],
    2: [1, 26, 3, 9],
    3: [4, 3, 5],
    4: [27, 17, 1, 7, 8],
    5: [27, 17, 1, 7, 22],
    6: [4, 22, 15],
}


def _make_nakshatra_reference_tests(yoga_name: str, ref: dict[int, int]) -> type:
    """Factory that creates a TestCase class verifying a single-nakshatra yoga."""

    class _Test(unittest.TestCase):
        def test_fires_for_all_vara_nakshatra_pairs(self):
            for vara, nak in ref.items():
                with self.subTest(vara=vara, nakshatra=nak):
                    names = _yoga_names(vara, _NEUTRAL_TITHI, nak)
                    self.assertIn(
                        yoga_name, names,
                        f"{yoga_name} should fire for vara={vara} nakshatra={nak}",
                    )

        def test_does_not_fire_for_wrong_nakshatra(self):
            # Rotate the mapping by 1 vara to get "wrong" nakshatras
            varas = list(ref.keys())
            naks = list(ref.values())
            for i, vara in enumerate(varas):
                wrong_nak = naks[(i + 1) % len(naks)]
                if wrong_nak == ref[vara]:
                    continue  # skip if accidentally same
                with self.subTest(vara=vara, wrong_nakshatra=wrong_nak):
                    names = _yoga_names(vara, _NEUTRAL_TITHI, wrong_nak)
                    self.assertNotIn(
                        yoga_name, names,
                        f"{yoga_name} must NOT fire for vara={vara} nakshatra={wrong_nak}",
                    )

    _Test.__name__ = f"Test{yoga_name.replace(' ', '')}Reference"
    _Test.__qualname__ = _Test.__name__
    return _Test


# Generate test classes for all single-nakshatra yogas
TestVarjitTithiNakshatraReference = _make_nakshatra_reference_tests(
    "Varjit Tithi Nakshatra", _REF_VARJIT
)
TestUtpatNakshatraReference = _make_nakshatra_reference_tests(
    "Utpat Nakshatra", _REF_UTPAT
)
TestMrityuYogaNakshatraReference = _make_nakshatra_reference_tests(
    "Mrityu Yoga Nakshatra", _REF_MRITYU_NAK
)
TestKaanYogaReference = _make_nakshatra_reference_tests("Kaan Yoga", _REF_KAAN)
TestDagdhaYogaReference = _make_nakshatra_reference_tests("Dagdha Yoga", _REF_DAGDHA_YOG)
TestYamGhantReference = _make_nakshatra_reference_tests("Yam Ghant", _REF_YAM_GHANT)
TestMusalYogaReference = _make_nakshatra_reference_tests("Musal Yoga", _REF_MUSAL)
TestKaalDandReference = _make_nakshatra_reference_tests("Kaal Dand", _REF_KAAL_DAND)
TestVajraReference = _make_nakshatra_reference_tests("Vajra", _REF_VAJRA)
TestRakshasYogaReference = _make_nakshatra_reference_tests("Rakshas Yoga", _REF_RAKSHAS)
TestDhwankshReference = _make_nakshatra_reference_tests("Dhwanksh", _REF_DHWANKSH)
TestDhumraReference = _make_nakshatra_reference_tests("Dhumra", _REF_DHUMRA)
TestGadReference = _make_nakshatra_reference_tests("Gad", _REF_GAD)
TestAnandReference = _make_nakshatra_reference_tests("Anand", _REF_ANAND)
TestShrivatsaReference = _make_nakshatra_reference_tests("Shrivatsa", _REF_SHRIVATSA)
TestSaumyaReference = _make_nakshatra_reference_tests("Saumya", _REF_SAUMYA)
TestChatraReference = _make_nakshatra_reference_tests("Chatra", _REF_CHATRA)
TestShubhReference = _make_nakshatra_reference_tests("Shubh", _REF_SHUBH)
TestAmritReference = _make_nakshatra_reference_tests("Amrit", _REF_AMRIT)
TestMitraReference = _make_nakshatra_reference_tests("Mitra", _REF_MITRA)
TestSiddhaYogaReference = _make_nakshatra_reference_tests("Siddhi Yoga", _REF_SIDDHA)
TestAmritSiddhiReference = _make_nakshatra_reference_tests(
    "Amrit Siddhi", _REF_AMRIT_SIDDHI
)


class TestSarvarthaSiddhiReference(unittest.TestCase):
    """Sarvartha Siddhi has multiple nakshatras per vara — tested separately."""

    def test_fires_for_all_reference_pairs(self):
        for vara, naks in _REF_SARVARTHA.items():
            for nak in naks:
                with self.subTest(vara=vara, nakshatra=nak):
                    names = _yoga_names(vara, _NEUTRAL_TITHI, nak)
                    self.assertIn(
                        "Sarvartha Siddhi", names,
                        f"Sarvartha Siddhi should fire for vara={vara} nakshatra={nak}",
                    )

    def test_does_not_fire_for_clearly_wrong_nakshatras(self):
        # Wednesday Sarvartha = Rohini(4), Krittika(3), Mrigashira(5)
        # Clearly wrong for Wed: Hasta(13), Anuradha(17)
        for wrong_nak in [13, 17]:
            with self.subTest(nakshatra=wrong_nak):
                names = _yoga_names(3, _NEUTRAL_TITHI, wrong_nak)
                self.assertNotIn(
                    "Sarvartha Siddhi", names,
                    f"Sarvartha Siddhi must NOT fire for Wed nakshatra={wrong_nak}",
                )

    def test_tuesday_wrong_nakshatras_do_not_fire(self):
        # Tuesday Sarvartha = Ashvini(1), UB(26), Krittika(3), Ashlesha(9)
        # Code incorrectly has Pushya(8) and Anuradha(17)
        for wrong_nak in [8, 17]:
            with self.subTest(nakshatra=wrong_nak):
                names = _yoga_names(2, _NEUTRAL_TITHI, wrong_nak)
                self.assertNotIn(
                    "Sarvartha Siddhi", names,
                    f"Sarvartha Siddhi must NOT fire for Tue nakshatra={wrong_nak}",
                )


# ==========================================================================
# SECTION 3: Specific regression tests for the most impactful known bugs
# ==========================================================================


class TestKnownBugsFromReferenceImage(unittest.TestCase):
    """Explicit regression tests for each discrepancy found in the reference image."""

    def test_utpat_monday_is_purva_ashadha_not_purva_phalguni(self):
        # Reference: Mon Utpat = पू.षा. (Purva Ashadha = 20)
        # Bug: code had 11 (Purva Phalguni)
        self.assertIn("Utpat Nakshatra", _yoga_names(1, _NEUTRAL_TITHI, 20))  # should fire
        self.assertNotIn("Utpat Nakshatra", _yoga_names(1, _NEUTRAL_TITHI, 11))  # must not fire

    def test_varjit_wednesday_is_shravana_not_shatabhisha(self):
        # Reference: Wed Varjit = श्रवण (Shravana = 22)
        # Bug: code had 24 (Shatabhisha)
        self.assertIn("Varjit Tithi Nakshatra", _yoga_names(3, _NEUTRAL_TITHI, 22))  # should fire
        self.assertNotIn("Varjit Tithi Nakshatra", _yoga_names(3, _NEUTRAL_TITHI, 24))  # must not

    def test_rakshas_saturday_is_uttara_ashadha_not_uttara_phalguni(self):
        # Reference: Sat Rakshas = उ.षा. (Uttara Ashadha = 21)
        # Bug: code had 12 (Uttara Phalguni) with comment noting the inconsistency
        self.assertIn("Rakshas Yoga", _yoga_names(6, _NEUTRAL_TITHI, 21))  # should fire
        self.assertNotIn("Rakshas Yoga", _yoga_names(6, _NEUTRAL_TITHI, 12))  # must not fire

    def test_mitra_tuesday_is_purva_ashadha_not_purva_phalguni(self):
        # Reference: Tue Mitra = पू.षा. (Purva Ashadha = 20)
        # Bug: code had 11 (Purva Phalguni)
        self.assertIn("Mitra", _yoga_names(2, _NEUTRAL_TITHI, 20))  # should fire
        self.assertNotIn("Mitra", _yoga_names(2, _NEUTRAL_TITHI, 11))  # must not fire

    def test_sarvartha_tuesday_is_krittika_not_pushya(self):
        # Reference: Tue Sarvartha includes Krittika(3) and Ashlesha(9)
        # Bug: code had Pushya(8) and Anuradha(17) instead
        self.assertIn("Sarvartha Siddhi", _yoga_names(2, _NEUTRAL_TITHI, 3))   # Krittika ✓
        self.assertIn("Sarvartha Siddhi", _yoga_names(2, _NEUTRAL_TITHI, 9))   # Ashlesha ✓
        self.assertNotIn("Sarvartha Siddhi", _yoga_names(2, _NEUTRAL_TITHI, 8))  # no Pushya
        self.assertNotIn("Sarvartha Siddhi", _yoga_names(2, _NEUTRAL_TITHI, 17))  # no Anuradha

    def test_sarvartha_wednesday_is_krittika_mrigashira_not_anuradha_hasta(self):
        # Reference: Wed Sarvartha = Rohini(4), Krittika(3), Mrigashira(5)
        # Bug: code had Anuradha(17) and Hasta(13) instead of Krittika+Mrigashira
        self.assertIn("Sarvartha Siddhi", _yoga_names(3, _NEUTRAL_TITHI, 3))   # Krittika ✓
        self.assertIn("Sarvartha Siddhi", _yoga_names(3, _NEUTRAL_TITHI, 5))   # Mrigashira ✓
        self.assertNotIn("Sarvartha Siddhi", _yoga_names(3, _NEUTRAL_TITHI, 17))  # no Anuradha
        self.assertNotIn("Sarvartha Siddhi", _yoga_names(3, _NEUTRAL_TITHI, 13))  # no Hasta

    def test_sarvartha_thursday_includes_pushya(self):
        # Drik Panchang (June 18 2026): Sarvartha Siddhi fires on Thursday+Pushya(8)
        # Guru Pushya is the most celebrated yoga; Sarvartha Siddhi must co-fire.
        self.assertIn("Sarvartha Siddhi", _yoga_names(4, _NEUTRAL_TITHI, 8))   # Pushya ✓
        # Existing Thursday nakshatras must still fire
        for nak in [27, 17, 1, 7]:
            with self.subTest(nakshatra=nak):
                self.assertIn("Sarvartha Siddhi", _yoga_names(4, _NEUTRAL_TITHI, nak))
