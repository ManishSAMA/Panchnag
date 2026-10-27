import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/calendar/samvat.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

const delhi = (lat: 28.6139, lon: 77.2090);
const ist = Duration(hours: 5, minutes: 30);

CivilDate newYear(int year) =>
    chaitraShuklaPratipada(year, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);

CivilDate diwaliOf(int year) =>
    diwali(year, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);

CivilDate dayBefore(CivilDate date) {
  final previous = DateTime.utc(date.year, date.month, date.day - 1);
  return CivilDate(previous.year, previous.month, previous.day);
}

int prevailing(CivilDate date) =>
    prevailingTithi(date, lat: delhi.lat, lon: delhi.lon, utcOffset: ist, rule: SunriseRule.modern);

void main() {
  group('Chaitra Shukla Pratipada', () {
    for (final year in [2016, 2026, 2040]) {
      test('$year falls in March or April, the day after the Phalguna Amavasya day', () {
        final day = newYear(year);

        expect(day.compareTo(CivilDate(year, 3, 2)), greaterThanOrEqualTo(0));
        expect(day.compareTo(CivilDate(year, 4, 23)), lessThanOrEqualTo(0));
        expect(prevailing(dayBefore(day)), anyOf(30, 29)); // 29 when Amavasya is kshaya
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
}
