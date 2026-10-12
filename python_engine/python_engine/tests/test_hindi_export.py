"""Hindi range export: the same table as the English export, with Hindi headers
and Hindi text values (plans/hindi-excel-export.md)."""
from __future__ import annotations

import json
import re
import tempfile
import unittest

from range_generation_service import generate_year_range_exports

TRENTON = {"lat": 40.2203, "lon": -74.7658}

# Machine-readable stamps that legitimately stay in Latin script.
_STAMP = re.compile(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\]")


def _export(language: str) -> tuple[dict, list[dict]]:
    result = generate_year_range_exports(
        start_year=2027, end_year=2027, city=None, ayanamsa_name="Lahiri",
        output_format="json", monthly=False, workers=1,
        output_dir=tempfile.mkdtemp(), language=language, **TRENTON,
    )
    with open(result["files"][0].path, encoding="utf-8") as fh:
        return result, json.load(fh)


def _latin_residue(text: str, tz_label: str) -> str:
    return re.sub(r"[^A-Za-z]", "", _STAMP.sub("", text).replace(tz_label, ""))


class HindiRangeExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.en_result, cls.en_rows = _export("en")
        cls.hi_result, cls.hi_rows = _export("hi")
        cls.tz_label = cls.hi_result["location"]["timezone_export_label"]

    def _paired(self, en_key: str, en_value: str, hi_key: str) -> str:
        """The Hindi value on the first day whose English `en_key` equals `en_value`."""
        index = next(i for i, row in enumerate(self.en_rows) if row[en_key] == en_value)
        return self.hi_rows[index][hi_key]

    def test_file_name_carries_hi_suffix(self):
        self.assertEqual(self.hi_result["files"][0].name, "panchang_2027_2027_hi.json")
        self.assertEqual(self.en_result["files"][0].name, "panchang_2027_2027.json")

    def test_same_shape_as_english(self):
        self.assertEqual(len(self.hi_rows), len(self.en_rows))
        self.assertEqual(len(self.hi_rows[0]), len(self.en_rows[0]))

    def test_english_export_is_unchanged(self):
        self.assertIn("Weekday", self.en_rows[0])
        self.assertIn("Jain_Festivals", self.en_rows[0])

    def test_headers_are_hindi(self):
        for header in self.hi_rows[0]:
            with self.subTest(header=header):
                self.assertEqual(_latin_residue(header, self.tz_label), "")

    def test_no_text_value_left_in_latin_script(self):
        """Catches any name missing from a translation table, all year round."""
        leftovers = {
            (key, value)
            for row in self.hi_rows
            for key, value in row.items()
            if isinstance(value, str) and _latin_residue(value, self.tz_label)
        }
        self.assertEqual(leftovers, set())

    def test_vocabulary(self):
        cases = [
            ("Weekday", "Shukravara (Friday)", "वार", "शुक्रवार"),
            ("Hindu_Month", "Agrahayana", "हिंदू मास", "मार्गशीर्ष"),
            ("Hindu_Month_Common", "Maagsar", "मास (प्रचलित)", "अगहन"),
            ("Bhadra_Max_Risk", "High", "भद्रा अधिकतम जोखिम", "उच्च"),
        ]
        for en_key, en_value, hi_key, hi_value in cases:
            with self.subTest(en_value=en_value):
                self.assertEqual(self._paired(en_key, en_value, hi_key), hi_value)

    def test_tithi_keeps_its_end_stamp(self):
        index = next(i for i, r in enumerate(self.en_rows) if r["Tithi"].startswith("Krishna Dashami ["))
        stamp = self.en_rows[index]["Tithi"].removeprefix("Krishna Dashami ")
        self.assertEqual(self.hi_rows[index]["तिथि"], f"कृष्ण दशमी {stamp}")

    def test_rashi_numbers_become_names(self):
        index = next(i for i, r in enumerate(self.en_rows) if r["Moon_Rashi"] == 1)
        self.assertEqual(self.hi_rows[index]["चंद्र राशि"], "मेष")

    def test_booleans_read_haan_nahin(self):
        self.assertEqual({r["भद्रा"] for r in self.hi_rows}, {"हाँ", "नहीं"})

    def test_festivals_use_registry_hindi_names(self):
        hi = self._paired_contains("Jain_Festivals", "Gautam Swami Janam Divas", "जैन पर्व")
        self.assertIn("गौतम स्वामी जन्म दिवस", hi)

    def _paired_contains(self, en_key: str, needle: str, hi_key: str) -> str:
        index = next(i for i, row in enumerate(self.en_rows) if needle in (row[en_key] or ""))
        return self.hi_rows[index][hi_key]


class HindiCliExportTest(unittest.TestCase):
    def test_language_flag_writes_hindi_file(self):
        from pathlib import Path
        from unittest.mock import patch

        import main

        out_base = Path(tempfile.mkdtemp()) / "panchang"
        argv = [
            "main.py", "--start_year", "2027", "--end_year", "2027",
            "--lat", str(TRENTON["lat"]), "--lon", str(TRENTON["lon"]),
            "--tz_offset", "-5", "--tz_label", "EST",
            "--format", "json", "--output", str(out_base), "--language", "hi",
        ]
        with patch("sys.argv", argv):
            main.main()

        with open(f"{out_base}_2027_2027_hi.json", encoding="utf-8") as fh:
            rows = json.load(fh)
        self.assertEqual(len(rows), 365)
        self.assertIn("दिनांक", rows[0])
        self.assertIn("विक्रम संवत", rows[0])


if __name__ == "__main__":
    unittest.main()
