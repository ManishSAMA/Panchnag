"""Naming and registry-composition rules for festival output.

These describe what a user reads in the calendar: Navpad Oli appears as a
Prarambh/Purna pair rather than nine numbered days, the paksha is not part of
the Bhaktambar Vrat name, the Namokar chain does not carry step counts, and the
four Parva Tithi entries are withheld from output.
"""
import re
import unittest


def _festivals():
    from jain_observances.festival_service import generate_jain_festivals
    res = generate_jain_festivals(
        year=2026, lat=28.6139, lon=77.2090, ayanamsa="Lahiri", profile="all"
    )
    return res["festivals"]


def _registry():
    from jain_observances import festival_rules as rules
    return rules.FESTIVAL_REGISTRY


class NavpadOliTest(unittest.TestCase):
    def test_no_per_day_navpad_oli_occurrences(self):
        offenders = [f["name"] for f in _festivals()
                     if "Oli" in f["name"] or f.get("badge") == "Navpad Oli"]
        self.assertEqual(
            ["Navapad Oli Prarambh (Ayambil Oli Start)",
             "Navapad Oli Purna (Ayambil Oli Nishthapan)"],
            sorted(set(offenders)),
        )

    def test_navpad_oli_rule_is_retired_from_registry(self):
        offenders = [e["id"] for e in _registry() if e.get("rule_type") == "NavpadOli"]
        self.assertEqual([], offenders)

    def test_oli_still_has_a_start_and_an_end(self):
        names = {f["name"] for f in _festivals()}
        self.assertIn("Navapad Oli Prarambh (Ayambil Oli Start)", names)
        self.assertIn("Navapad Oli Purna (Ayambil Oli Nishthapan)", names)


class BhaktambarVratNameTest(unittest.TestCase):
    def test_paksha_is_not_part_of_the_name(self):
        offenders = [f["name"] for f in _festivals() if "Bhaktambar" in f["name"]
                     and f["name"] != "Bhaktambar Vrat"]
        self.assertEqual([], offenders)

    def test_both_pakshas_still_produce_observances(self):
        """Two discrete days per paksha -- Ashtami and Chaturdashi -- not one span.

        A cycle whose Chaturdashi is kshaya contributes only its Ashtami day and
        no fallback, so the total sits just under 2 x the fortnight count.
        """
        bhaktambar = [f for f in _festivals() if f["name"] == "Bhaktambar Vrat"]
        self.assertEqual({"Shukla", "Krishna"}, {f["paksha"] for f in bhaktambar})

        fortnights = {f["occurrence_id"].rsplit("_", 1)[0] for f in bhaktambar}
        self.assertGreaterEqual(len(bhaktambar), len(fortnights))
        self.assertLessEqual(len(bhaktambar), 2 * len(fortnights))
        self.assertTrue(all(f["start_date"] == f["end_date"] for f in bhaktambar))

    def test_adhika_and_nija_months_get_distinct_occurrence_ids(self):
        """An adhika month is a real fortnight of its own: its Bhaktambar Vrat is a
        separate observance from the nija month's and must not share its identity."""
        bhaktambar = [f for f in _festivals() if f["name"] == "Bhaktambar Vrat"]
        ids = [f["occurrence_id"] for f in bhaktambar]
        self.assertEqual(sorted(ids), sorted(set(ids)))

    def test_occurrence_id_adhika_marker_agrees_with_the_month_label(self):
        """jain_month is the PURNIMANTA month name, so for a Krishna paksha it is the
        NEXT month -- and its adhika-ness is purnimanta_is_adhika, not the amanta
        is_adhika of the snapshot. Reading the amanta flag crosses the two for Krishna
        pakshas: a vrat labelled 'Adhika Jyeshtha' gets a non-adhika id and vice versa."""
        for f in _festivals():
            if f["name"] != "Bhaktambar Vrat":
                continue
            label_is_adhika = "Adhika" in (f.get("jain_month") or "")
            id_is_adhika = "adhika" in f["occurrence_id"]
            self.assertEqual(label_is_adhika, id_is_adhika,
                             f'{f["occurrence_id"]} labelled {f.get("jain_month")!r}')

    def test_adhika_fortnights_are_identified_separately(self):
        """2026 has an Adhika Jyeshtha. Each of its two fortnights carries its own
        Bhaktambar days, identified apart from the nija Jyeshtha ones."""
        jyeshtha = [f for f in _festivals()
                    if f["name"] == "Bhaktambar Vrat" and "yeshtha" in (f.get("jain_month") or "")]
        ids = [f["occurrence_id"] for f in jyeshtha]
        self.assertEqual(sorted(ids), sorted(set(ids)))

        fortnights = {i.rsplit("_", 1)[0] for i in ids}
        self.assertEqual(4, len(fortnights), "2 adhika + 2 nija Jyeshtha fortnights")
        self.assertEqual(2, sum("adhika" in f for f in fortnights))


class NamokarVratNameTest(unittest.TestCase):
    def test_step_counts_are_absent_from_every_name(self):
        offenders = [f["name"] for f in _festivals()
                     if "Namokar Mahamantra Vrat" in f["name"]
                     and re.search(r"\d+\s*/\s*35", f["name"])]
        self.assertEqual([], offenders)

    def test_chain_start_and_end_remain_distinguishable(self):
        names = {f["name"] for f in _festivals() if "Namokar Mahamantra Vrat" in f["name"]}
        self.assertIn("Namokar Mahamantra Vrat (Prarambh)", names)
        self.assertIn("Namokar Mahamantra Vrat (Udyapan / Purna)", names)

    def test_intermediate_steps_are_plain(self):
        names = {f["name"] for f in _festivals() if "Namokar Mahamantra Vrat" in f["name"]}
        self.assertIn("Namokar Mahamantra Vrat", names)


class ParvaTithiSuppressedTest(unittest.TestCase):
    def test_parva_tithi_entries_are_not_registered(self):
        offenders = [e["id"] for e in _registry() if e["id"].startswith("parva_tithi_")]
        self.assertEqual([], offenders)

    def test_no_parva_tithi_rows_in_output(self):
        offenders = [f["name"] for f in _festivals() if f["name"].startswith("Parva Tithi")]
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
