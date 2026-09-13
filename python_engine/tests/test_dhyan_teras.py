"""Kartik Krishna Teras (13) is Dhyan Teras in the Jain tradition.

Not "Dhanteras" -- the Hindu festival of wealth. The Jain observance is Dhyan
Teras, a day of focus, meditation and detachment FROM material wealth, and it
carries the Janam (birth) and Tap (penance) Kalyanak of Shri Padam Prabhu
Bhagwan, the 6th Tirthankara.

Unlike Diwali/Amavasya there is no day/night split here: the ordinary Jain
anchor decides it. Whichever Gregorian date holds Tithi 13 at sunrise + 2h24m
is the single date, and every associated observance maps onto it.
"""
import unittest


def _res(year):
    from jain_observances.festival_service import generate_jain_festivals
    return generate_jain_festivals(year=year, lat=28.6139, lon=77.2090,
                                   ayanamsa="Lahiri", profile="all")


class DhyanTerasNomenclatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = _res(2026)["festivals"]

    def test_the_day_is_labelled_dhyan_teras(self):
        names = {x["name"] for x in self.f if x["id"] == "dhan_teras_2026"}
        self.assertEqual({"Dhyan Teras"}, names)

    def test_no_occurrence_is_labelled_dhanteras(self):
        offenders = [x["name"] for x in self.f
                     if "dhanteras" in x["name"].lower() or "dhan trayodashi" in x["name"].lower()]
        self.assertEqual([], offenders)

    def test_wealth_framing_is_gone_from_the_observance(self):
        evt = next(x for x in self.f if x["id"] == "dhan_teras_2026")
        blob = " ".join(str(evt.get(k, "")) for k in ("meaning", "observance", "description")).lower()
        for word in ("lakshmi", "dhanteras", "festival of wealth"):
            self.assertNotIn(word, blob)


class DhyanTerasKalyanakAssociationTest(unittest.TestCase):
    """Padam Prabhu's Janam and Tap Kalyanak share this tithi, and therefore its date."""

    def _dhyan_teras_and_kalyanaks(self, year):
        f = _res(year)["festivals"]
        teras = next(x for x in f if x["id"] == f"dhan_teras_{year}")
        kalyanaks = [x for x in f
                     if "padmaprabha" in x["id"]
                     and ("birth_kalyanak_13" in x["id"] or "austerity_kalyanak_13" in x["id"])]
        return teras, kalyanaks

    def test_janam_and_tap_kalyanak_map_to_the_same_single_date(self):
        for year in (2026, 2027):
            teras, kalyanaks = self._dhyan_teras_and_kalyanaks(year)
            self.assertEqual(2, len(kalyanaks), year)
            for k in kalyanaks:
                self.assertEqual(teras["start_date"], k["start_date"], f"{year} {k['id']}")
                self.assertEqual(k["start_date"], k["end_date"], k["id"])

    def test_it_is_kartika_krishna_trayodashi_at_the_jain_anchor(self):
        for year in (2026, 2027):
            res = _res(year)
            teras = next(x for x in res["festivals"] if x["id"] == f"dhan_teras_{year}")
            self.assertEqual((teras["jain_month"], teras["paksha"]), ("Kartika", "Krishna"), year)
            self.assertEqual("Trayodashi (13)", teras["tithi"], year)
            self.assertTrue(res["panchang_tithi_map"][teras["start_date"]].endswith("Trayodashi (13)"))

    def test_2026_resolves_to_7_november(self):
        teras, kalyanaks = self._dhyan_teras_and_kalyanaks(2026)
        self.assertEqual("2026-11-07", teras["start_date"])
        for k in kalyanaks:
            self.assertEqual("2026-11-07", k["start_date"])


if __name__ == "__main__":
    unittest.main()
