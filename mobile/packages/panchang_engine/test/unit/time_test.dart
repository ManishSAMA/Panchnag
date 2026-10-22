import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

void main() {
  group('Julian Day', () {
    test('J2000.0 is noon UT on 2000-01-01', () {
      expect(julianDayFromUtc(DateTime.utc(2000, 1, 1, 12)), 2451545.0);
    });

    test('a civil midnight UT falls on a half day', () {
      expect(julianDayFromUtc(DateTime.utc(2026, 10, 21)), 2461334.5);
    });

    test('round-trips to the millisecond', () {
      final instant = DateTime.utc(2031, 2, 28, 23, 59, 58, 123);

      expect(utcFromJulianDay(julianDayFromUtc(instant)), instant);
    });

    test('rejects a non-UTC DateTime', () {
      expect(() => julianDayFromUtc(DateTime(2026, 1, 1)), throwsArgumentError);
    });
  });

  group('Civil day anchor (local midnight on the standard clock)', () {
    test('India is UTC+5:30 all year', () {
      expect(
        utcFromJulianDay(civilDayAnchor(const CivilDate(2026, 10, 21), 'Asia/Kolkata')),
        DateTime.utc(2026, 10, 20, 18, 30),
      );
    });

    test('London keeps GMT through the summer, like a standard-time panchang', () {
      expect(
        utcFromJulianDay(civilDayAnchor(const CivilDate(2026, 7, 1), 'Europe/London')),
        DateTime.utc(2026, 7, 1),
      );
    });

    test('New York keeps EST through the summer', () {
      expect(
        utcFromJulianDay(civilDayAnchor(const CivilDate(2026, 7, 1), 'America/New_York')),
        DateTime.utc(2026, 7, 1, 5),
      );
    });

    test('Kathmandu keeps its 45-minute offset', () {
      expect(
        utcFromJulianDay(civilDayAnchor(const CivilDate(2026, 1, 1), 'Asia/Kathmandu')),
        DateTime.utc(2025, 12, 31, 18, 15),
      );
    });
  });

  group('CivilDate', () {
    test('steps across month and leap-year ends', () {
      expect(const CivilDate(2028, 2, 28).next(), const CivilDate(2028, 2, 29));
      expect(const CivilDate(2026, 12, 31).next(), const CivilDate(2027, 1, 1));
    });

    test('formats as ISO for fixture keys', () {
      expect(const CivilDate(2026, 3, 5).iso, '2026-03-05');
      expect(CivilDate.parse('2026-03-05'), const CivilDate(2026, 3, 5));
    });
  });
}
