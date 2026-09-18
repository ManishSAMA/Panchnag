"""Phase 2 of the tithi unification (plans/tithi_unification/design.md).

The snapshot's public ``tithi``/``paksha``/``tithi_in_paksha`` become the 6-ghati
(Jain day-start) values, so the festival layer's reported tithi agrees with the
daily API's. The plain-sunrise values survive as private ``_sunrise_*`` fields
used only where an udaya day is a genuine precondition: Kalyanak candidate
selection and the weak/strong comparison in ``_sixghati_pullback``. Because those
call sites keep their udaya input, no festival date may move.
"""
import unittest


def _res(year=2026):
    from jain_observances.festival_service import generate_jain_festivals
    return generate_jain_festivals(year=year, lat=28.6139, lon=77.2090,
                                   ayanamsa="Lahiri", profile="all")


def _snaps(year=2026):
    from jain_observances.festival_service import _build_snapshots
    return _build_snapshots(year, 28.6139, 77.2090, "Lahiri", "Asia/Kolkata")


class SnapshotFieldsAreSixGhatiTest(unittest.TestCase):
    def test_public_tithi_equals_the_six_ghati_tithi(self):
        for s in _snaps():
            self.assertEqual(s["jain_tithi"], s["tithi"], s["date"])
            self.assertEqual(s["jain_paksha"], s["paksha"], s["date"])
            self.assertEqual(s["jain_tithi_in_paksha"], s["tithi_in_paksha"], s["date"])

    def test_sunrise_values_survive_privately(self):
        from datetime import date
        by = {s["date"]: s for s in _snaps()}
        s = by[date(2026, 3, 29)]
        self.assertEqual(11, s["_sunrise_tithi_in_paksha"])   # udaya: Ekadashi
        self.assertEqual(12, s["tithi_in_paksha"])            # 6-ghati: Dwadashi
        self.assertEqual("Shukla", s["_sunrise_paksha"])


class ReportedTithiMapMatchesDailyApiTest(unittest.TestCase):
    def test_map_uses_the_six_ghati_tithi(self):
        m = _res()["panchang_tithi_map"]
        self.assertEqual("Chaitra Shukla Dwadashi (12)", m["2026-03-29"])
        self.assertEqual("Chaitra Shukla Purnima (15)", m["2026-04-01"])


class NoFestivalDateMovesTest(unittest.TestCase):
    """The whole point of keeping _sunrise_* private: these verified dates hold."""

    @classmethod
    def setUpClass(cls):
        cls.f = _res()["festivals"]

    def _one(self, fid):
        hits = [x for x in self.f if x["id"] == fid]
        self.assertEqual(1, len(hits), fid)
        return hits[0]

    def test_mahavir_janma_kalyanak_stays_on_31_march(self):
        self.assertEqual("2026-03-31", self._one("mahavir_janma_kalyanak")["start_date"])

    def test_sumatinath_ekadashi_kalyanaks_stay_pulled_back_to_28_march(self):
        hits = [x for x in self.f if "sumatinath" in x["id"] and x.get("tithi") == "Ekadashi (11)"]
        self.assertEqual(3, len(hits))
        for h in hits:
            self.assertEqual("2026-03-28", h["start_date"])


if __name__ == "__main__":
    unittest.main()
