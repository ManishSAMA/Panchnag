import unittest
from unittest.mock import patch, call

from panchang import (
    calculate_panchak_kaal,
    _in_panchak,
    _find_panchak_crossing_jd,
    NAKSHATRA_NAMES,
)
from panchang_service import generate_location_panchang
from export import format_row_data
from export_pdf import generate_pdf_calendar


class PanchakBoundaryTests(unittest.TestCase):

    def test_just_below_300_is_not_panchak(self):
        self.assertFalse(_in_panchak(299.999))

    def test_at_300_is_panchak(self):
        self.assertTrue(_in_panchak(300.0))

    def test_inside_panchak_zone(self):
        for lon in [306.0, 320.0, 333.0, 346.0, 359.99]:
            with self.subTest(lon=lon):
                self.assertTrue(_in_panchak(lon))

    def test_at_360_is_not_panchak(self):
        self.assertFalse(_in_panchak(360.0))

    def test_zero_is_not_panchak(self):
        self.assertFalse(_in_panchak(0.0))

    def test_crossing_finder_entry(self):
        """Binary search finds the JD when Moon crosses into panchak (300°)."""
        # Simulate linear Moon movement: 290° at JD 0.0, 310° at JD 1.0
        def mock_lon(jd, planet, ayanamsa='Lahiri'):
            return 290.0 + 20.0 * jd  # crosses 300° at JD 0.5

        with patch('panchang.get_planetary_longitude', side_effect=mock_lon):
            crossing = _find_panchak_crossing_jd(0.0, 1.0, entering=True, ayanamsa_name='Lahiri')
            self.assertAlmostEqual(crossing, 0.5, places=2)

    def test_crossing_finder_exit(self):
        """Binary search finds the JD when Moon crosses out of panchak (360°→0°)."""
        # Simulate Moon: 350° at JD 0.0, wraps to 10° at JD 1.0
        def mock_lon(jd, planet, ayanamsa='Lahiri'):
            raw = 350.0 + 20.0 * jd
            return raw % 360.0  # crosses 360° at JD 0.5

        with patch('panchang.get_planetary_longitude', side_effect=mock_lon):
            crossing = _find_panchak_crossing_jd(0.0, 1.0, entering=False, ayanamsa_name='Lahiri')
            self.assertAlmostEqual(crossing, 0.5, places=2)


class PanchakOverlapTests(unittest.TestCase):

    def _make_lon_func(self, lon_at_sr, lon_at_nsr):
        """Linear Moon longitude between SR (JD 10.0) and NSR (JD 11.0)."""
        def lon_func(jd, planet, ayanamsa='Lahiri'):
            if planet != 'Moon':
                return 0.0
            frac = (jd - 10.0) / 1.0
            raw = lon_at_sr + (lon_at_nsr - lon_at_sr) * frac
            return raw % 360.0
        return lon_func

    def test_no_panchak_returns_empty_windows(self):
        """Moon stays below 300° all day → no windows."""
        with patch('panchang.get_planetary_longitude', side_effect=self._make_lon_func(285.0, 298.0)):
            result = calculate_panchak_kaal(10.0, 11.0)
        self.assertEqual(result['windows'], [])
        self.assertIsNone(result['period'])
        self.assertIsNotNone(result['next_period'])

    def test_entry_during_day_not_clipped_start(self):
        """Moon crosses 300° during the day → clipped_start=False, entry is within window."""
        with patch('panchang.get_planetary_longitude', side_effect=self._make_lon_func(295.0, 310.0)):
            result = calculate_panchak_kaal(10.0, 11.0)
        self.assertEqual(len(result['windows']), 1)
        w = result['windows'][0]
        self.assertFalse(w['clipped_start'])
        self.assertTrue(w['clipped_end'])
        self.assertGreater(w['start_jd'], 10.0)
        self.assertEqual(w['end_jd'], 11.0)
        self.assertIsNotNone(result['period'])
        self.assertIsNone(result['next_period'])

    def test_exit_during_day_not_clipped_end(self):
        """Moon exits panchak (crosses 360°) during the day → clipped_end=False."""
        with patch('panchang.get_planetary_longitude', side_effect=self._make_lon_func(355.0, 10.0)):
            result = calculate_panchak_kaal(10.0, 11.0)
        self.assertEqual(len(result['windows']), 1)
        w = result['windows'][0]
        self.assertTrue(w['clipped_start'])
        self.assertFalse(w['clipped_end'])
        self.assertEqual(w['start_jd'], 10.0)
        self.assertLess(w['end_jd'], 11.0)

    def test_full_day_overlap_clipped_both(self):
        """Moon is in panchak all day → clipped_start=True, clipped_end=True."""
        with patch('panchang.get_planetary_longitude', side_effect=self._make_lon_func(310.0, 320.0)):
            result = calculate_panchak_kaal(10.0, 11.0)
        self.assertEqual(len(result['windows']), 1)
        w = result['windows'][0]
        self.assertTrue(w['clipped_start'])
        self.assertTrue(w['clipped_end'])
        self.assertEqual(w['start_jd'], 10.0)
        self.assertEqual(w['end_jd'], 11.0)

    def test_nakshatra_at_overlap_start_is_populated(self):
        """window['nakshatra'] is a valid nakshatra name within the panchak zone."""
        PANCHAK_NAKSHATRAS = {
            'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
        }
        with patch('panchang.get_planetary_longitude', side_effect=self._make_lon_func(310.0, 320.0)):
            result = calculate_panchak_kaal(10.0, 11.0)
        nak = result['windows'][0]['nakshatra']
        self.assertIn(nak, PANCHAK_NAKSHATRAS)

    def test_next_period_preview_on_inactive_day(self):
        """next_period has entry_jd and exit_jd when no window today."""
        with patch('panchang.get_planetary_longitude', side_effect=self._make_lon_func(285.0, 298.0)):
            result = calculate_panchak_kaal(10.0, 11.0)
        np_ = result['next_period']
        self.assertIn('entry_jd', np_)
        self.assertIn('exit_jd', np_)
        self.assertGreater(np_['exit_jd'], np_['entry_jd'])


class PanchakApiTests(unittest.TestCase):

    def test_daily_api_includes_panchak_kaal_structure(self):
        """generate_location_panchang returns panchak_kaal with required fields."""
        result = generate_location_panchang('2025-01-01', lat=26.9124, lon=75.7873)
        self.assertIn('panchak_kaal', result)
        pk = result['panchak_kaal']
        self.assertIn('has_window', pk)
        self.assertIn('is_active', pk)
        self.assertIn('windows', pk)
        self.assertIn('period', pk)
        self.assertIn('next_period', pk)

    def test_daily_api_window_fields(self):
        """When panchak is active, window objects contain required fields."""
        # Use a date known to have panchak: find one by checking a range
        from panchang import calculate_panchak_kaal
        from astronomy import get_sunrise, local_time_to_jd

        # Scan forward from a reference date to find a day with panchak
        from datetime import date, timedelta
        d = date(2025, 1, 1)
        found_date = None
        for _ in range(30):
            jd_start = local_time_to_jd(d.year, d.month, d.day, 0.0, 5.5)
            jd_sr = get_sunrise(jd_start, 26.9124, 75.7873)
            jd_nsr = get_sunrise(jd_sr + 0.5, 26.9124, 75.7873)
            res = calculate_panchak_kaal(jd_sr, jd_nsr)
            if res['windows']:
                found_date = d.isoformat()
                break
            d += timedelta(days=1)

        if found_date is None:
            self.skipTest('Could not find a panchak day in scan range')

        result = generate_location_panchang(found_date, lat=26.9124, lon=75.7873)
        pk = result['panchak_kaal']
        self.assertTrue(pk['has_window'])
        for w in pk['windows']:
            self.assertIn('start', w)
            self.assertIn('end', w)
            self.assertIn('nakshatra', w)
            self.assertIn('clipped_start', w)
            self.assertIn('clipped_end', w)


class PanchakExportTests(unittest.TestCase):

    def _base_panchang(self):
        return {
            'Vara_Name': 'Ravivara (Sunday)',
            'Tithi_Index': 1,
            'Tithi_Name': 'Shukla Pratipada',
            'Nakshatra_Index': 1,
            'Nakshatra_Name': 'Ashwini',
            'Nakshatra_Pada': 1,
            'Yoga_Index': 1,
            'Yoga_Name': 'Vishkumbha',
            'Karana_Index': 1,
            'Karana_Name': 'Kimstughna',
            'Karana_Start_JD': 2460676.5,
            'Karana_End_JD': 2460677.0,
        }

    def test_has_panchak_true_when_window_present(self):
        panchak_segments = [{'start_jd': 2460676.6, 'end_jd': 2460676.9, 'nakshatra': 'Shatabhisha'}]
        row = format_row_data(
            date_str='2025-01-01',
            julian_date=2460676.5,
            planets={'Sun': 250.0, 'Moon': 315.0},
            panchang=self._base_panchang(),
            jain_tithi={'Jain_Tithi_Index': 1, 'Jain_Tithi_Name': 'Shukla Pratipada', 'Jain_Tithi_End_JD': 2460676.9},
            sunrise_str='07:18:00',
            sunset_str='17:40:00',
            moonrise_str='08:00:00',
            moonset_str='19:00:00',
            ayanamsa_dec=24.0,
            panchak_segments=panchak_segments,
        )
        self.assertIn('Has_Panchak', row)
        self.assertTrue(row['Has_Panchak'])
        self.assertIn('Panchak_Window', row)
        self.assertIn('Shatabhisha', row['Panchak_Window'])

    def test_has_panchak_false_when_no_window(self):
        row = format_row_data(
            date_str='2025-01-01',
            julian_date=2460676.5,
            planets={'Sun': 250.0, 'Moon': 95.0},
            panchang=self._base_panchang(),
            jain_tithi={'Jain_Tithi_Index': 1, 'Jain_Tithi_Name': 'Shukla Pratipada', 'Jain_Tithi_End_JD': 2460676.9},
            sunrise_str='07:18:00',
            sunset_str='17:40:00',
            moonrise_str='08:00:00',
            moonset_str='19:00:00',
            ayanamsa_dec=24.0,
            panchak_segments=[],
        )
        self.assertFalse(row['Has_Panchak'])
        self.assertEqual(row['Panchak_Window'], 'None')

    def test_pdf_generation_includes_panchak_column(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test_panchak.pdf')
            generate_pdf_calendar(2025, pdf_path, lat=26.9124, lon=75.7873)
            self.assertTrue(os.path.exists(pdf_path))


class MonthOverviewPanchakTests(unittest.TestCase):

    def test_month_overview_includes_has_panchak(self):
        """Each day in /month-overview includes has_panchak boolean."""
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app import create_app
        app = create_app()
        client = app.test_client()
        resp = client.get('/month-overview?year=2025&month=1&lat=26.9124&lon=75.7873')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        for day in data['days']:
            self.assertIn('has_panchak', day, f"Missing has_panchak for {day.get('date')}")
            self.assertIsInstance(day['has_panchak'], bool)


if __name__ == '__main__':
    unittest.main()
