"""Ashtahnika Mahaparv: a strict span that kshaya cannot shorten.

Three times a year -- Ashadha, Kartika, Phalguna -- the festival runs
continuously from Ashtami (8) to Purnima (15) of the Shukla paksha. Where
Bhaktambar is two discrete days, this is one unbroken period, and its boundaries
expand rather than contract:

  * Ashtami kshaya   -> commence early, on Saptami (7)
  * Ashtami vriddhi  -> commence on the FIRST Ashtami
  * Purnima vriddhi  -> conclude on the SECOND Purnima

The span therefore never drops below its natural length; a missing Tithi pushes
the start outward, it does not pull the end in.
"""

import unittest
from datetime import date, timedelta

from jain_observances.festival_rules import AshtahnikaVratFestival
from jain_observances.festival_service import generate_jain_festivals


LAT, LON = 26.9124, 75.7873


def make_shukla_snapshots(start: date, tithis: list[int], month: str = "Kartika") -> list[dict]:
    return [
        {
            "date": start + timedelta(days=offset),
            "paksha": "Shukla",
            "tithi_in_paksha": tithi,
            "tithi": tithi,
            "jain_tithi": tithi,
            "hindu_month": month,
            "is_adhika": False,
            "purnimanta_month": month,
            "purnimanta_is_adhika": False,
        }
        for offset, tithi in enumerate(tithis)
    ]


def resolve(snaps: list[dict], month: str = "KARTIKA", year: int = 2026) -> list[dict]:
    rule = AshtahnikaVratFestival({
        "id": f"ashtahnika_{month.lower()}", "name": "Ashtahnika Mahaparv",
        "category": "mahaparv", "profiles": ["all"],
        "rule_type": "AshtahnikaVrat", "jain_month": month,
    })
    return rule.resolve(snaps, "all", {"year": year})


class NaturalSpanTest(unittest.TestCase):
    def test_a_clean_paksha_runs_ashtami_to_purnima(self):
        snaps = make_shukla_snapshots(date(2026, 11, 17), list(range(1, 16)))
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["start_date"], "2026-11-24")  # Ashtami
        self.assertEqual(occurrence["end_date"], "2026-12-01")    # Purnima
        self.assertTrue(occurrence["is_span"])

    def test_the_span_is_eight_days_when_nothing_is_lost(self):
        snaps = make_shukla_snapshots(date(2026, 11, 17), list(range(1, 16)))
        occurrence = resolve(snaps)[0]

        start = date.fromisoformat(occurrence["start_date"])
        end = date.fromisoformat(occurrence["end_date"])
        self.assertEqual((end - start).days + 1, 8)


class AshtamiBoundaryTest(unittest.TestCase):
    def test_a_missing_ashtami_commences_early_on_saptami(self):
        snaps = make_shukla_snapshots(
            date(2026, 11, 17), [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
        )
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["start_date"], "2026-11-23")  # the Saptami day
        self.assertTrue(occurrence["has_kshaya"])

    def test_a_doubled_ashtami_commences_on_the_first(self):
        snaps = make_shukla_snapshots(
            date(2026, 11, 17), [1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11, 12, 13, 14, 15]
        )
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["start_date"], "2026-11-24")  # first Ashtami
        self.assertTrue(occurrence["has_vriddhi"])

    def test_the_span_never_shortens_when_a_middle_tithi_is_lost(self):
        """A kshaya inside the span must not pull either boundary in."""
        snaps = make_shukla_snapshots(
            date(2026, 11, 17), [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15]
        )
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["start_date"], "2026-11-24")  # still Ashtami
        self.assertTrue(occurrence["end_date"].endswith("-11-30"))  # still Purnima


class PurnimaBoundaryTest(unittest.TestCase):
    def test_a_doubled_purnima_concludes_on_the_second(self):
        snaps = make_shukla_snapshots(
            date(2026, 11, 17), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15]
        )
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["end_date"], "2026-12-02")  # second Purnima
        self.assertTrue(occurrence["has_vriddhi"])

    def test_both_boundaries_can_expand_at_once(self):
        snaps = make_shukla_snapshots(
            date(2026, 11, 17), [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 15]
        )
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["start_date"], "2026-11-23")  # Saptami
        self.assertEqual(occurrence["end_date"], "2026-12-01")    # second Purnima


class LabellingTest(unittest.TestCase):
    def test_the_occurrence_names_its_start_and_end(self):
        snaps = make_shukla_snapshots(date(2026, 11, 17), list(range(1, 16)))
        occurrence = resolve(snaps)[0]

        self.assertEqual(occurrence["start_label"], "प्रारंभ")
        self.assertEqual(occurrence["end_label"], "पारणा")


class RealYearIntegrationTest(unittest.TestCase):
    def setUp(self):
        generate_jain_festivals.cache_clear()
        result = generate_jain_festivals(2026, LAT, LON, "Lahiri", "all")
        # By id prefix, not name: "Ashtahnika Purna" and "Nandishwar Ashtami"
        # are separate single-day observances that also carry the word.
        self.events = [f for f in result["festivals"]
                       if (f.get("occurrence_id") or "").startswith("ashtahnika_")]

    def test_it_occurs_three_times_a_year(self):
        self.assertEqual(len(self.events), 3)

    def test_each_occurrence_is_a_continuous_span_of_at_least_eight_days(self):
        for event in self.events:
            start = date.fromisoformat(event["start_date"])
            end = date.fromisoformat(event["end_date"])
            self.assertTrue(event["is_span"])
            self.assertGreaterEqual((end - start).days + 1, 8)

    def test_each_occurrence_ends_on_a_purnima(self):
        from jain_observances.festival_service import _build_snapshots

        snaps = {s["date"]: s for s in _build_snapshots(2026, LAT, LON, "Lahiri", "Asia/Kolkata")}
        for event in self.events:
            end = snaps[date.fromisoformat(event["end_date"])]
            self.assertEqual(end["tithi_in_paksha"], 15, f"{event['name']} must end on Purnima")

    def test_it_covers_the_three_canonical_months(self):
        ids = " ".join(e["occurrence_id"] for e in self.events)
        for month in ("ashadha", "kartika", "phalguna"):
            self.assertIn(month, ids)

    def test_the_span_agrees_with_the_separate_purna_observance(self):
        """The standalone "Ashtahnika Purna" day must land on the span's end.

        Independent corroboration: those festivals are resolved by different
        rule classes, so agreement is a real cross-check on the boundary.
        """
        generate_jain_festivals.cache_clear()
        everything = generate_jain_festivals(2026, LAT, LON, "Lahiri", "all")["festivals"]
        purna = {f["occurrence_id"]: f["start_date"] for f in everything
                 if "ashtahnika_purna" in (f.get("occurrence_id") or "")}
        ends = {e["occurrence_id"]: e["end_date"] for e in self.events}

        for occ_id, purna_date in purna.items():
            month = occ_id.split("_")[0]
            self.assertEqual(ends[f"ashtahnika_{month}_2026"], purna_date)


if __name__ == "__main__":
    unittest.main()
