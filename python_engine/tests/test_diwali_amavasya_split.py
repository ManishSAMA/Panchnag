"""Diwali and Mahavir Swami Moksha Kalyanak sit on either side of one Amavasya.

Amavasya is a lunar interval that need not align with the civil day. When it begins
in the afternoon of date A and ends in the morning of date B:

  * the Amavasya NIGHT falls on date A  -> Diwali (a night observance) is date A;
  * the Jain day-start anchor (sunrise + 2h24m / 6 ghati) sees Amavasya on date B
    -> Moksha Kalyanak (a dawn observance, Nirvana Laddu at pratyush) is date B.

2026 at Delhi is exactly this shape: Amavasya runs 08 Nov 11:28 -> 09 Nov 12:32.
The two observances therefore fall on DIFFERENT Gregorian dates, and nothing may
force them onto the same one. Cross-checked against the printed Pt. Jaini Jiyalal
panchang note already recorded in festival_rules.py: Lakshmi Puja (pradosh
Amavasya) 8 Nov, "श्री महावीर स्वामी मोक्ष" 9 Nov.
"""
import unittest


def _fest(year=2026):
    from jain_observances.festival_service import generate_jain_festivals
    return generate_jain_festivals(year=year, lat=28.6139, lon=77.2090,
                                   ayanamsa="Lahiri", profile="all")["festivals"]


class DiwaliAmavasyaSplitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = _fest()

    def _one(self, fid):
        hits = [x for x in self.f if x["id"] == fid]
        self.assertEqual(1, len(hits), fid)
        return hits[0]

    def test_diwali_is_the_amavasya_night(self):
        self.assertEqual("2026-11-08", self._one("diwali_2026")["start_date"])

    def test_moksha_kalyanak_is_the_six_ghati_amavasya_morning(self):
        self.assertEqual("2026-11-09", self._one("mahavira_nirvana_kalyanak_2026")["start_date"])

    def test_the_two_do_not_share_a_gregorian_date(self):
        self.assertNotEqual(self._one("diwali_2026")["start_date"],
                            self._one("mahavira_nirvana_kalyanak_2026")["start_date"])

    def test_every_moksha_kalyanak_occurrence_stays_on_the_morning_day(self):
        for fid in ("mahavir_nirvana_deepavali:2026-11-09", "mahavira_nirvana_kalyanak_2026"):
            hits = [x for x in self.f if x["id"] == fid.split(":")[0]]
            for h in hits:
                if h["start_date"].startswith("2026-11"):
                    self.assertEqual("2026-11-09", h["start_date"], fid)


if __name__ == "__main__":
    unittest.main()
