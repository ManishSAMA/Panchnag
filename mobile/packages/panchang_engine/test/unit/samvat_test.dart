import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/calendar/samvat.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

const delhi = (lat: 28.6139, lon: 77.2090);
const ist = Duration(hours: 5, minutes: 30);

CivilDate newYear(int year) =>
    chaitraShuklaPratipada(year, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);

CivilDate diwaliOf(int year) => diwali(year, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);

CivilDate dayBefore(CivilDate date) {
  final previous = DateTime.utc(date.year, date.month, date.day - 1);
  return CivilDate(previous.year, previous.month, previous.day);
}

/// The Amanta month at [date]'s 6-ghati reference instant.
LunarMonth referenceMonth(CivilDate date) {
  final midnight = DateTime.utc(date.year, date.month, date.day).subtract(ist);
  return amantaMonth(
    sunrise(julianDayFromUtc(midnight), delhi.lat, delhi.lon, SunriseRule.modern) + jainTithiOffsetDays,
  );
}

int prevailing(CivilDate date) =>
    prevailingTithi(date, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);

void main() {
  // The new year is the first day from 1 March whose 6-ghati reference instant
  // falls in Amanta Chaitra (Adhika Chaitra in an Adhik year), as in Python's
  // find_chaitra_shukla_1.
  group('Chaitra Shukla Pratipada', () {
    test('2024: 9 April, not 11 March: the Amavasya of 10 March ends Magha, not Phalguna', () {
      expect(newYear(2024), const CivilDate(2024, 4, 9));
    });

    test('2028: 27 March, after an Amavasya that prevails on two days', () {
      expect(newYear(2028), const CivilDate(2028, 3, 27));
    });

    test('2029: 16 March, Adhika Chaitra begins the year', () {
      expect(newYear(2029), const CivilDate(2029, 3, 16));
      expect(referenceMonth(const CivilDate(2029, 3, 16)), const LunarMonth(index: 0, isAdhika: true));
    });

    test('2025 and 2026 are unchanged: 30 March and 19 March', () {
      expect(newYear(2025), const CivilDate(2025, 3, 30));
      expect(newYear(2026), const CivilDate(2026, 3, 19));
    });

    for (var year = 2016; year <= 2040; year++) {
      test('$year: the first day in Chaitra, after a day in Phalguna', () {
        final day = newYear(year);

        expect(referenceMonth(day).index, 0);
        expect(referenceMonth(dayBefore(day)), const LunarMonth(index: 11, isAdhika: false));
      });
    }
  });

  group('Diwali', () {
    for (final year in [2016, 2026, 2040]) {
      test('$year falls between 10 Oct and 24 Nov on an Amavasya day', () {
        final day = diwaliOf(year);

        expect(day.compareTo(CivilDate(year, 10, 10)), greaterThanOrEqualTo(0));
        expect(day.compareTo(CivilDate(year, 11, 24)), lessThanOrEqualTo(0));
        expect(prevailing(day), anyOf(30, 29)); // 29 when Amavasya is kshaya
      });
    }
  });

  group('Vikram Samvat', () {
    test('turns over on Chaitra Shukla Pratipada: 2083 begins in 2026', () {
      final day = newYear(2026);

      expect(vikramSamvat(dayBefore(day), chaitraShukla1: day), 2082);
      expect(vikramSamvat(day, chaitraShukla1: day), 2083);
    });
  });

  group('Vira Nirvana Samvat', () {
    test('turns over the day after Diwali: 2553 begins in 2026', () {
      final day = diwaliOf(2026);

      expect(viraNirvanaSamvat(day, diwali: day), 2552);
      expect(viraNirvanaSamvat(day.next(), diwali: day), 2553);
    });
  });

  // Python searches fixed windows for the two new years (1 Mar-21 Apr, 10 Oct-24 Nov),
  // so the samvats outside them need no search at all.
  group('the samvats on any day of a year', () {
    for (final year in [2024, 2026, 2027, 2033]) {
      test("$year: equal the samvats from that year's new-year days, on every day", () {
        final (chaitra, diwaliDay) = (newYear(year), diwaliOf(year));
        final mismatches = <String>[];
        for (var d = DateTime.utc(year, 1, 1); d.year == year; d = d.add(const Duration(days: 1))) {
          final date = CivilDate(d.year, d.month, d.day);
          final on = samvatsOn(date, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);
          final expected = (
            vikram: vikramSamvat(date, chaitraShukla1: chaitra),
            viraNirvana: viraNirvanaSamvat(date, diwali: diwaliDay),
          );
          if (on != expected) mismatches.add('$date $on, expected $expected');
        }

        expect(mismatches, isEmpty);
      });
    }
  });
}
