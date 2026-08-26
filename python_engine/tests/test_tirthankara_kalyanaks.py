import unittest
import json
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), "tirthankara_kalyanaks_data.json")

class TirthankaraKalyanaksDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            cls.data = json.load(f)
        cls.records = cls.data["full_expected_dataset"]
        cls.meta = cls.data["_meta"]
        cls.test_cases = {tc["id"]: tc for tc in cls.data["test_cases"]}

    def test_tc001_vrindavan_aggregate_count(self):
        """TC001: Total Kalyanaka records for Vrindavan == 97."""
        count = sum(1 for r in self.records if r["source"] == "Vrindavan")
        self.assertEqual(count, self.test_cases["TC001"]["expected"]["total_records"])

    def test_tc002_uttarapurana_aggregate_count(self):
        """TC002: Total Kalyanaka records for Uttarapurana == 96."""
        count = sum(1 for r in self.records if r["source"] == "Uttarapurana")
        self.assertEqual(count, self.test_cases["TC002"]["expected"]["total_records"])

    def test_tc003_ashadhara_aggregate_count(self):
        """TC003: Total Kalyanaka records for Sanskrit Jin Kalyanaka Mala by Ashadhara == 95."""
        count = sum(1 for r in self.records if r["source"] == "Sanskrit Jin Kalyanaka Mala by Ashadhara")
        self.assertEqual(count, self.test_cases["TC003"]["expected"]["total_records"])

    def test_tc004_vrindavan_month_coverage(self):
        """TC004: All 12 months present for Vrindavan."""
        months = sorted(list({r["month"] for r in self.records if r["source"] == "Vrindavan"}))
        expected_months = sorted(self.test_cases["TC004"]["expected"]["months_present"])
        self.assertEqual(months, expected_months)
        self.assertEqual(len(months), 12)

    def test_tc005_uttarapurana_month_coverage(self):
        """TC005: All 12 months present for Uttarapurana."""
        months = sorted(list({r["month"] for r in self.records if r["source"] == "Uttarapurana"}))
        expected_months = sorted(self.test_cases["TC005"]["expected"]["months_present"])
        self.assertEqual(months, expected_months)
        self.assertEqual(len(months), 12)

    def test_tc006_ashadhara_month_coverage(self):
        """TC006: All 12 months present for Ashadhara."""
        months = sorted(list({r["month"] for r in self.records if r["source"] == "Sanskrit Jin Kalyanaka Mala by Ashadhara"}))
        expected_months = sorted(self.test_cases["TC006"]["expected"]["months_present"])
        self.assertEqual(months, expected_months)
        self.assertEqual(len(months), 12)

    def _lookup(self, source, month, fortnight, day):
        matches = [
            {"tirthankara": r["tirthankara"], "events": r["events"]}
            for r in self.records
            if r["source"] == source and r["month"] == month and r["fortnight"] == fortnight and r["day"] == day
        ]
        return matches

    def test_tc007_vrindavan_chaitra_krishna_4(self):
        tc = self.test_cases["TC007"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc008_vrindavan_chaitra_krishna_30(self):
        tc = self.test_cases["TC008"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc009_vrindavan_chaitra_shukla_11(self):
        tc = self.test_cases["TC009"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc010_vrindavan_chaitra_shukla_15(self):
        tc = self.test_cases["TC010"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc011_vrindavan_vaishakha_shukla_1(self):
        tc = self.test_cases["TC011"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc012_vrindavan_jyeshtha_krishna_14(self):
        tc = self.test_cases["TC012"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc013_vrindavan_ashadha_krishna_6(self):
        tc = self.test_cases["TC013"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc014_vrindavan_kartika_krishna_30(self):
        tc = self.test_cases["TC014"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc015_uttarapurana_chaitra_krishna_15(self):
        tc = self.test_cases["TC015"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc016_uttarapurana_vaishakha_shukla_13(self):
        tc = self.test_cases["TC016"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc017_ashadhara_ashwin_shukla_9(self):
        tc = self.test_cases["TC017"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc018_ashadhara_margashirsha_shukla_1(self):
        tc = self.test_cases["TC018"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc019_ashadhara_phalguna_krishna_7(self):
        tc = self.test_cases["TC019"]
        res = self._lookup(tc["input"]["source"], tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"])
        self.assertEqual(res, tc["expected"]["kalyanaks"])

    def test_tc020_cross_source_chaitra_shukla_1(self):
        tc = self.test_cases["TC020"]
        m, f, d = tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"]
        for src, expected_kalyanaks in tc["expected"]["per_source"].items():
            actual = self._lookup(src, m, f, d)
            self.assertEqual(actual, expected_kalyanaks, f"Mismatch for source: {src}")

    def test_tc021_cross_source_vaishakha_shukla_1(self):
        tc = self.test_cases["TC021"]
        m, f, d = tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"]
        for src, expected_kalyanaks in tc["expected"]["per_source"].items():
            actual = self._lookup(src, m, f, d)
            self.assertEqual(actual, expected_kalyanaks, f"Mismatch for source: {src}")

    def test_tc022_cross_source_kartika_krishna_30(self):
        tc = self.test_cases["TC022"]
        m, f, d = tc["input"]["month"], tc["input"]["fortnight"], tc["input"]["day"]
        for src, expected_kalyanaks in tc["expected"]["per_source"].items():
            actual = self._lookup(src, m, f, d)
            self.assertEqual(actual, expected_kalyanaks, f"Mismatch for source: {src}")

    def test_tc023_krishna_day_boundary(self):
        max_day = max(r["day"] for r in self.records if r["fortnight"] == "Krishna")
        self.assertLessEqual(max_day, 30)
        self.assertEqual(max_day, self.test_cases["TC023"]["expected"]["max_day"])

    def test_tc024_shukla_day_boundary(self):
        max_day = max(r["day"] for r in self.records if r["fortnight"] == "Shukla")
        self.assertLessEqual(max_day, 15)
        self.assertEqual(max_day, self.test_cases["TC024"]["expected"]["max_day"])

    def test_tc025_positive_day_boundary(self):
        min_day = min(r["day"] for r in self.records)
        self.assertGreaterEqual(min_day, 1)
        self.assertEqual(min_day, self.test_cases["TC025"]["expected"]["min_day"])

    def test_tc026_amavasya_markers(self):
        amavasya_entries = [r for r in self.records if r["special"] == "amavasya"]
        self.assertEqual(len(amavasya_entries), self.test_cases["TC026"]["expected"]["count"])
        for r in amavasya_entries:
            self.assertEqual(r["fortnight"], "Krishna")
            self.assertEqual(r["day"], 30)

    def test_tc027_purnima_markers(self):
        purnima_entries = [r for r in self.records if r["special"] == "purnima"]
        self.assertEqual(len(purnima_entries), self.test_cases["TC027"]["expected"]["count"])
        for r in purnima_entries:
            self.assertEqual(r["day"], 15)
        shukla_cnt = sum(1 for r in purnima_entries if r["fortnight"] == "Shukla")
        krishna_cnt = sum(1 for r in purnima_entries if r["fortnight"] == "Krishna")
        self.assertEqual(shukla_cnt, self.test_cases["TC027"]["expected"]["fortnight_breakdown"]["Shukla"])
        self.assertEqual(krishna_cnt, self.test_cases["TC027"]["expected"]["fortnight_breakdown"]["Krishna"])

    def test_tc028_valid_event_vocabulary(self):
        valid = set(self.test_cases["TC028"]["expected"]["valid_events"])
        for r in self.records:
            for ev in r["events"]:
                self.assertIn(ev, valid, f"Invalid event {ev} in record: {r}")

    def test_tc029_distinct_tirthankara_names(self):
        names = sorted(list({r["tirthankara"] for r in self.records}))
        self.assertEqual(len(names), self.test_cases["TC029"]["expected"]["distinct_name_count"])
        self.assertEqual(names, self.test_cases["TC029"]["expected"]["distinct_names"])

    def test_tc030_multi_tirthankara_days(self):
        from collections import defaultdict
        day_map = defaultdict(set)
        for r in self.records:
            key = (r["source"], r["month"], r["fortnight"], r["day"])
            day_map[key].add(r["tirthankara"])
        multi_tirthankara_days = [k for k, v in day_map.items() if len(v) > 1]
        self.assertEqual(len(multi_tirthankara_days), self.test_cases["TC030"]["expected"]["count_of_such_days"])

    def test_tc031_multi_event_entries(self):
        multi_event_entries = [r for r in self.records if len(r["events"]) > 1]
        self.assertEqual(len(multi_event_entries), self.test_cases["TC031"]["expected"]["count_of_such_entries"])

if __name__ == "__main__":
    unittest.main()
