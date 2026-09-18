"""Bhaktambar Vrat: two discrete days, never a span.

The Vrat is observed on exactly two independent Tithis in each paksha --
Ashtami (8) and Chaturdashi (14). They are separate observances that happen to
share a fortnight, not the endpoints of a continuous fast.

The two Tithis fall back differently, and the asymmetry is the point:

  * Ashtami kshaya      -> observe on Saptami (7) instead
  * Chaturdashi kshaya  -> not observed at all that cycle; no fallback

This replaces an earlier reading that treated the Vrat as a continuous
Ashtami->Chaturdashi span with a seven-day floor, which pulled the start back to
Saptami whenever *any* Tithi in 8..14 was missing -- so a kshaya Chaturdashi
moved the start day. See plans/case-study-bhaktambar-saptami.md.

These tests drive festival_rules.BhaktambarVratFestival, the rule that actually
runs. The previous suite exercised jain_observances/vrats/bhaktambar.py, which
nothing imported.
"""

import unittest
from datetime import date, timedelta

from jain_observances.festival_rules import BhaktambarVratFestival
from jain_observances.festival_service import generate_jain_festivals


LAT, LON = 26.9124, 75.7873


def make_snapshots(start: date, tithis: list[int], paksha: str = "Shukla",
                   month: str = "Vaishakha") -> list[dict]:
    """Snapshots for consecutive days carrying the given paksha-relative Tithis."""
    snaps = []
    for offset, tithi_in_paksha in enumerate(tithis):
        absolute = tithi_in_paksha if paksha == "Shukla" else tithi_in_paksha + 15
        snaps.append({
            "date": start + timedelta(days=offset),
            "paksha": paksha,
            "tithi_in_paksha": tithi_in_paksha,
            "tithi": absolute,
            "jain_tithi": absolute,
            "hindu_month": month,
            "is_adhika": False,
            "purnimanta_month": month,
            "purnimanta_is_adhika": False,
        })
    return snaps


def resolve(snaps: list[dict], year: int = 2026) -> list[dict]:
    rule = BhaktambarVratFestival({"id": "bhaktambar_vrat", "name": "Bhaktambar Vrat",
                                   "category": "vrat", "profiles": ["all"],
                                   "rule_type": "BhaktambarVrat"})
    return rule.resolve(snaps, "all", {"year": year})


class DiscreteDayLogicTest(unittest.TestCase):
    def test_a_normal_paksha_yields_exactly_two_single_day_observances(self):
        snaps = make_snapshots(date(2026, 4, 18), list(range(1, 16)))
        occurrences = resolve(snaps)

        self.assertEqual(len(occurrences), 2)
        for occurrence in occurrences:
            self.assertEqual(occurrence["start_date"], occurrence["end_date"],
                             "Bhaktambar days are discrete, never spans")
            self.assertFalse(occurrence["is_span"])

    def test_the_two_days_land_on_ashtami_and_chaturdashi(self):
        snaps = make_snapshots(date(2026, 4, 18), list(range(1, 16)))
        dates = sorted(o["start_date"] for o in resolve(snaps))

        self.assertEqual(dates, ["2026-04-25", "2026-05-01"])  # 8th and 14th days

    def test_no_span_fields_survive(self):
        """Day-count enforcement is gone; nothing may still advertise a span."""
        snaps = make_snapshots(date(2026, 4, 18), list(range(1, 16)))
        for occurrence in resolve(snaps):
            self.assertNotIn("duration_days", occurrence)
            self.assertNotIn("span_label", occurrence)
            self.assertNotIn("has_vriddhi", occurrence)


class AshtamiKshayaTest(unittest.TestCase):
    def test_a_missing_ashtami_falls_back_to_saptami(self):
        # ... 6, 7, 9, 10 ... -- Ashtami never prevails
        snaps = make_snapshots(date(2026, 4, 18), [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15])
        occurrences = sorted(resolve(snaps), key=lambda o: o["start_date"])

        self.assertEqual(len(occurrences), 2)
        self.assertEqual(occurrences[0]["start_date"], "2026-04-24")  # the Saptami day
        self.assertTrue(occurrences[0]["has_kshaya"])
        self.assertEqual(occurrences[0]["observed_tithi"], 7)

    def test_a_present_ashtami_never_uses_the_saptami_fallback(self):
        snaps = make_snapshots(date(2026, 4, 18), list(range(1, 16)))
        ashtami = min(resolve(snaps), key=lambda o: o["start_date"])

        self.assertEqual(ashtami["observed_tithi"], 8)
        self.assertFalse(ashtami["has_kshaya"])

    def test_a_doubled_ashtami_uses_the_first_day(self):
        snaps = make_snapshots(date(2026, 4, 18), [1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11, 12, 13, 14])
        ashtami = min(resolve(snaps), key=lambda o: o["start_date"])

        self.assertEqual(ashtami["start_date"], "2026-04-25")  # first of the two


class ChaturdashiKshayaTest(unittest.TestCase):
    def test_a_missing_chaturdashi_is_simply_not_observed(self):
        """The key asymmetry: Chaturdashi has no fallback."""
        snaps = make_snapshots(date(2026, 4, 18), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15])
        occurrences = resolve(snaps)

        self.assertEqual(len(occurrences), 1, "only the Ashtami observance remains")
        self.assertEqual(occurrences[0]["observed_tithi"], 8)

    def test_a_missing_chaturdashi_does_not_move_the_ashtami_day(self):
        """The regression this rewrite exists to prevent."""
        full = make_snapshots(date(2026, 4, 18), list(range(1, 16)))
        without_14 = make_snapshots(
            date(2026, 4, 18), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15]
        )

        ashtami_full = min(resolve(full), key=lambda o: o["start_date"])["start_date"]
        ashtami_short = min(resolve(without_14), key=lambda o: o["start_date"])["start_date"]

        self.assertEqual(ashtami_full, ashtami_short)
        self.assertEqual(ashtami_short, "2026-04-25")

    def test_a_missing_chaturdashi_never_produces_a_trayodashi_observance(self):
        snaps = make_snapshots(date(2026, 4, 18), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15])
        self.assertNotIn(13, [o["observed_tithi"] for o in resolve(snaps)])


class BothTithisMissingTest(unittest.TestCase):
    def test_ashtami_kshaya_and_chaturdashi_kshaya_together(self):
        snaps = make_snapshots(date(2026, 4, 18), [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 15])
        occurrences = resolve(snaps)

        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0]["observed_tithi"], 7)


class IdentityTest(unittest.TestCase):
    def test_the_two_days_have_distinct_occurrence_ids(self):
        snaps = make_snapshots(date(2026, 4, 18), list(range(1, 16)))
        ids = {o["occurrence_id"] for o in resolve(snaps)}
        self.assertEqual(len(ids), 2)

    def test_shukla_and_krishna_pakshas_do_not_collide(self):
        shukla = resolve(make_snapshots(date(2026, 4, 18), list(range(1, 16)), "Shukla"))
        krishna = resolve(make_snapshots(date(2026, 5, 3), list(range(1, 16)), "Krishna"))
        self.assertFalse({o["occurrence_id"] for o in shukla}
                         & {o["occurrence_id"] for o in krishna})


class RealYearIntegrationTest(unittest.TestCase):
    def setUp(self):
        generate_jain_festivals.cache_clear()
        result = generate_jain_festivals(2026, LAT, LON, "Lahiri", "all")
        self.events = [f for f in result["festivals"] if f.get("name") == "Bhaktambar Vrat"]

    def test_every_occurrence_is_a_single_day(self):
        self.assertTrue(self.events)
        for event in self.events:
            self.assertEqual(event["start_date"], event["end_date"])
            self.assertFalse(event["is_span"])

    def test_roughly_two_per_paksha_across_the_year(self):
        """~24 pakshas, up to 2 days each, minus Chaturdashi-kshaya cycles."""
        self.assertGreater(len(self.events), 35)
        self.assertLessEqual(len(self.events), 52)

    def test_every_occurrence_sits_on_seven_eight_or_fourteen(self):
        self.assertTrue(set(e["observed_tithi"] for e in self.events) <= {7, 8, 14})

    def test_a_seven_only_appears_when_that_cycle_lost_its_ashtami(self):
        for event in self.events:
            if event["observed_tithi"] == 7:
                self.assertTrue(event["has_kshaya"])

    def test_the_may_2026_case_now_starts_on_ashtami(self):
        """The reported anomaly: 9 May was Saptami with Ashtami present on the 10th."""
        may = sorted(e["start_date"] for e in self.events
                     if e["start_date"].startswith("2026-05"))
        self.assertIn("2026-05-10", may)
        self.assertNotIn("2026-05-09", may)


if __name__ == "__main__":
    unittest.main()
