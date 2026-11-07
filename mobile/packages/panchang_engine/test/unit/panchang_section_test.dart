// The Panchang section's readings on PanchangDay: the Jain tithi, nakshatra,
// yoga and Moon Rashi each with the one after it, every Karana of the day,
// the Sun's Rashi, the gata and Shaka Samvat.
// Design: python_engine/python_engine/plans/panchang-section-and-pothi.md.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/astro/sidereal.dart' show siderealSunLongitude;
import 'package:panchang_engine/src/panchang/elements.dart'
    show elongation, nakshatraAt, siderealMoonLongitude, tithiAt;
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');
const makara = 9;

PanchangDay delhi(CivilDate date) => const PanchangEngine().day(location: delhiCity, date: date);
PanchangSection section(CivilDate date) => const PanchangEngine().section(location: delhiCity, date: date);

double jd(DateTime t) => julianDayFromUtc(t);
const minute = 1 / 1440;

int yogaAt(double jdUt) => ((siderealSunLongitude(jdUt) + siderealMoonLongitude(jdUt)) % 360) ~/ (360 / 27) + 1;
int karanaAt(double jdUt) => elongation(jdUt) ~/ 6 + 1;
int moonRashiAt(double jdUt) => siderealMoonLongitude(jdUt) ~/ 30;
int sunRashiAt(double jdUt) => siderealSunLongitude(jdUt) ~/ 30;

/// One date every 23 days through 2026.
final sampleDates = [for (var k = 0; k < 365; k += 23) const CivilDate(2026, 1, 1).plusDays(k)];

void expectHandover(List<ElementSpan> pair, int Function(double) at, int cycle) {
  final [current, following] = pair;
  expect(following.index, current.index % cycle + 1);
  expect(following.endsAt.isAfter(current.endsAt), isTrue);
  expect(at(jd(current.endsAt) - minute), current.index);
  expect(at(jd(current.endsAt) + minute), following.index);
  expect(at(jd(following.endsAt) - minute), following.index);
  expect(at(jd(following.endsAt) + minute), following.index % cycle + 1);
}

void main() {
  test('the tithi lines are the Jain tithi, then the next, each until its end', () {
    for (final date in sampleDates) {
      final day = delhi(date);
      final pair = [(index: day.jainTithi.index, endsAt: day.jainTithi.endsAt), section(date).nextTithi];
      expectHandover(pair, tithiAt, 30);
    }
  });

  test('the nakshatra lines are the one at sunrise, then the next', () {
    for (final date in sampleDates) {
      final day = delhi(date);
      final pair = [(index: day.nakshatra.index, endsAt: day.nakshatra.endsAt), section(date).nextNakshatra];
      expectHandover(pair, nakshatraAt, 27);
    }
  });

  test('the yoga lines are the one at sunrise, then the next', () {
    for (final date in sampleDates) {
      final day = delhi(date);
      final reading = section(date);
      expect(reading.yogas.first.index, yogaAt(jd(day.sunrise)));
      expectHandover(reading.yogas, yogaAt, 27);
    }
  });

  test('the Moon Rashi lines are the sign at sunrise (0 = Mesha), then the next', () {
    for (final date in sampleDates) {
      final day = delhi(date);
      final [current, following] = section(date).moonRashis;
      expect(current.index, moonRashiAt(jd(day.sunrise)));
      expect(following.index, (current.index + 1) % 12);
      expect(moonRashiAt(jd(current.endsAt) - minute), current.index);
      expect(moonRashiAt(jd(current.endsAt) + minute), following.index);
      expect(following.endsAt.difference(current.endsAt).inHours, greaterThan(43)); // 30° at under 16° a day
    }
  });

  test('every Karana of the day is listed in order, the last one holding at the next sunrise', () {
    for (final date in sampleDates) {
      final day = delhi(date);
      final karanas = section(date).karanas;
      expect(karanas.length, inInclusiveRange(2, 4));
      expect(karanas.first.index, karanaAt(jd(day.sunrise)));
      for (var k = 0; k + 1 < karanas.length; k++) {
        expect(karanas[k + 1].index, karanas[k].index % 60 + 1);
        expect(karanas[k].endsAt.isBefore(day.nextSunrise), isTrue);
        expect(karanaAt(jd(karanas[k].endsAt) + minute), karanas[k + 1].index);
      }
      expect(karanas.last.endsAt.isBefore(day.nextSunrise), isFalse);
    }
  });

  test('on an ordinary day the Sun holds one Rashi past the next sunrise', () {
    expect(section(const CivilDate(2025, 2, 1)).sunRashis, [(index: makara, endsAt: null)]);
  });

  test('Makar Sankranti 2025 (14 Jan, 09:03 IST, Drik Panchang) hands Dhanu over to Makara', () {
    final day = delhi(const CivilDate(2025, 1, 14));
    final [dhanu, makaraSpan] = section(day.date).sunRashis;
    expect((dhanu.index, makaraSpan.index), (makara - 1, makara));
    expect(dhanu.endsAt!.isAfter(day.sunrise) && dhanu.endsAt!.isBefore(day.nextSunrise), isTrue);
    expect(sunRashiAt(jd(dhanu.endsAt!) + minute), makara);
    expect(makaraSpan.endsAt, isNull);
  });

  test('the Sankranti day is gata day 1, and the count rises a day at a time', () {
    expect(section(const CivilDate(2025, 1, 13)).gata.rashi, makara - 1);
    expect(section(const CivilDate(2025, 1, 14)).gata, (rashi: makara, day: 1));
    expect(section(const CivilDate(2025, 1, 15)).gata, (rashi: makara, day: 2));
    expect(section(const CivilDate(2025, 2, 1)).gata, (rashi: makara, day: 19));
  });

  test('gata counts up by one each day and restarts at 1 in the next Rashi', () {
    final readings = [for (var k = 0; k < 70; k++) section(const CivilDate(2026, 3, 1).plusDays(k)).gata];
    for (var k = 0; k + 1 < readings.length; k++) {
      final (before, after) = (readings[k], readings[k + 1]);
      if (after.rashi == before.rashi) {
        expect(after.day, before.day + 1);
      } else {
        expect(after, (rashi: (before.rashi + 1) % 12, day: 1));
      }
    }
    expect(readings.every((r) => r.day >= 1 && r.day <= 32), isTrue);
  });

  test('Shaka Samvat is Vikram Samvat less 135: both turn over on Chaitra Shukla Pratipada', () {
    for (final date in sampleDates) {
      final day = delhi(date);
      expect(day.shakaSamvat, day.vikramSamvat - 135);
    }
    expect(delhi(const CivilDate(2026, 11, 7)).shakaSamvat, 1948);
  });
}
