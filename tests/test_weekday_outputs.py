import unittest
from datetime import date
from unittest.mock import patch

from main import _dates_in_range, run_generation
from panchang_service import generate_location_panchang


VARA_TO_WEEKDAY = {
    "Ravivara (Sunday)": "Sunday",
    "Somavara (Monday)": "Monday",
    "Mangalavara (Tuesday)": "Tuesday",
    "Budhavara (Wednesday)": "Wednesday",
    "Guruvara (Thursday)": "Thursday",
    "Shukravara (Friday)": "Friday",
    "Shanivara (Saturday)": "Saturday",
}

PDF_VARA_NAMES = {
    "Ravivara": "Sunday",
    "Somavara": "Monday",
    "Mangalavara": "Tuesday",
    "Budhavara": "Wednesday",
    "Guruvara": "Thursday",
    "Shukravara": "Friday",
    "Shanivara": "Saturday",
}


class WeekdayOutputTests(unittest.TestCase):
    def test_service_vara_matches_local_civil_date_for_full_week(self):
        start = date(2026, 5, 3)
        end = date(2026, 5, 9)

        current = start
        while current <= end:
            result = generate_location_panchang(
                current.isoformat(),
                lat=26.9124,
                lon=75.7873,
            )
            expected = current.strftime("%A")
            actual = VARA_TO_WEEKDAY[result["panchang"]["vara"]["name"]]
            self.assertEqual(
                actual,
                expected,
                f"weekday mismatch for {current.isoformat()}",
            )
            current = current.fromordinal(current.toordinal() + 1)

    def test_range_generation_rows_use_correct_weekday_labels(self):
        config = {
            "lat": 26.9124,
            "lon": 75.7873,
            "tz_offset": 5.5,
            "tz_label": "IST",
            "ayanamsa": "Lahiri",
        }
        days = list(_dates_in_range(date(2026, 5, 3), date(2026, 5, 9)))

        rows = run_generation(config, days, workers=1)

        self.assertEqual(len(rows), 7)
        for row in rows:
            expected = date.fromisoformat(row["Date"]).strftime("%A")
            actual = VARA_TO_WEEKDAY[row["Weekday"]]
            self.assertEqual(actual, expected, f"row weekday mismatch for {row['Date']}")

    def test_pdf_generator_uses_local_civil_date_for_day_column(self):
        captured_tables: list[list[list[str]]] = []

        class FakeDoc:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def build(self, elements):
                self.elements = elements

        def fake_paragraph(text, _style):
            return text

        class FakeTable:
            def __init__(self, data):
                self.data = data

            def setStyle(self, _style):
                return None

        def fake_table(data, **kwargs):
            captured_tables.append(data)
            return FakeTable(data)

        with (
            patch("export_pdf.SimpleDocTemplate", FakeDoc),
            patch("export_pdf.Paragraph", side_effect=fake_paragraph),
            patch("export_pdf.Spacer", return_value=object()),
            patch("export_pdf.PageBreak", return_value=object()),
            patch("export_pdf.Table", side_effect=fake_table),
            patch("export_pdf.TableStyle", side_effect=lambda spec: spec),
            patch("export_pdf.getSampleStyleSheet", return_value={"Heading1": object(), "Normal": object()}),
            patch("export_pdf.ParagraphStyle", side_effect=lambda **kwargs: object()),
        ):
            from export_pdf import generate_pdf_calendar

            generate_pdf_calendar(
                2026,
                "/tmp/test_weekday_outputs.pdf",
                lat=26.9124,
                lon=75.7873,
                tz_offset=5.5,
                ayanamsa="Lahiri",
            )

        self.assertEqual(len(captured_tables), 12)

        may_table = captured_tables[4]
        may_5_row = may_table[5]
        self.assertEqual(may_5_row[0], "05-05-2026")
        self.assertEqual(may_5_row[1], "Mangalavara")
        self.assertEqual(PDF_VARA_NAMES[may_5_row[1]], "Tuesday")
        self.assertNotIn(, may_5_row[3])
        self.assertFalse(any(ch.isdigit() for ch in may_5_row[3]))


if __name__ == "__main__":
    unittest.main()
