// The Muhurat section's readings for a day: the daylight windows (Rahu Kaal,
// Yamaganda, Gulika, Abhijit), Panchak, Bhadra, Gandmool, Chandra Bal and
// Agni Vaas. Invariants over Delhi days; the parity test holds the times to
// the Python engine. Design: python_engine/python_engine/plans/muhurat-section.md.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/astro/sidereal.dart' show siderealSunLongitude;
import 'package:panchang_engine/src/panchang/day_elements.dart' show karanaAt;
import 'package:panchang_engine/src/panchang/day_yogas.dart' show aanandadiIndex;
import 'package:panchang_engine/src/panchang/elements.dart' show nakshatraAt, siderealMoonLongitude, tithiAt;
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

PanchangDay delhi(CivilDate date) => const PanchangEngine().day(location: delhiCity, date: date);
PanchangMuhurat muhurat(CivilDate date) => const PanchangEngine().muhurat(location: delhiCity, date: date);

double jd(DateTime t) => julianDayFromUtc(t);
const second = 1 / 86400;
const minute = 1 / 1440;

int moonRashiAt(double jdUt) => siderealMoonLongitude(jdUt) ~/ 30;
bool inPanchak(double jdUt) => siderealMoonLongitude(jdUt) >= 300;

/// One date every 11 days through 2026: every weekday, and a sample of
/// Panchak, Bhadra and Gandmool days.
final sampleDates = [for (var k = 0; k < 365; k += 11) const CivilDate(2026, 1, 1).plusDays(k)];

/// Thirty days in a row: a whole lunar month, so every recurring muhurat shows up.
final month = [for (var k = 0; k < 30; k++) const CivilDate(2026, 10, 1).plusDays(k)];

/// Part (1-8) of the daylight by weekday (0 = Sunday), as Drik Panchang's
/// Rahu Kalam, Yamaganda and Gulika Kalam tables give them.
const rahuPart = [8, 2, 7, 5, 6, 4, 3];
const yamagandaPart = [5, 4, 3, 2, 1, 7, 6];
const gulikaPart = [7, 6, 5, 4, 3, 2, 1];

/// Births with Chandra Bal: the Moon's Rashi is the 1st, 3rd, 6th, 7th, 10th
/// or 11th counted from the birth Rashi.
List<int> goodBirths(int moonRashi) => [
  for (var birth = 0; birth < 12; birth++)
    if (const {1, 3, 6, 7, 10, 11}.contains((moonRashi - birth) % 12 + 1)) birth,
];

void expectNear(DateTime ours, double expected) => expect((jd(ours) - expected).abs(), lessThan(second / 100));

bool insideDay(PanchangDay day, DateTime start, DateTime end) =>
    !start.isBefore(day.sunrise) && start.isBefore(end) && !end.isAfter(day.nextSunrise);

void main() {
  yogaTests();

  group('daylight windows', () {
    test('Rahu Kaal, Yamaganda and Gulika are each the weekday\'s eighth of the daylight', () {
      for (final date in sampleDates) {
        final day = delhi(date);
        final reading = muhurat(date);
        final eighth = (jd(day.sunset) - jd(day.sunrise)) / 8;
        for (final (window, parts) in [
          (reading.rahuKaal, rahuPart),
          (reading.yamaganda, yamagandaPart),
          (reading.gulika, gulikaPart),
        ]) {
          expectNear(window.start, jd(day.sunrise) + (parts[day.vara] - 1) * eighth);
          expectNear(window.end, jd(window.start) + eighth);
        }
      }
    });

    test('Rahu Kaal, Yamaganda and Gulika never share a part', () {
      for (var vara = 0; vara < 7; vara++) {
        expect({rahuPart[vara], yamagandaPart[vara], gulikaPart[vara]}, hasLength(3));
      }
      for (final date in sampleDates.take(7)) {
        final reading = muhurat(date);
        expect({reading.rahuKaal.start, reading.yamaganda.start, reading.gulika.start}, hasLength(3));
      }
    });

    test('Abhijit is the 8th of the 15 daylight muhurtas, centred on midday', () {
      for (final date in sampleDates) {
        final day = delhi(date);
        final abhijit = muhurat(date).abhijit;
        final fifteenth = (jd(day.sunset) - jd(day.sunrise)) / 15;
        expectNear(abhijit.start, jd(day.sunrise) + 7 * fifteenth);
        expectNear(abhijit.end, jd(abhijit.start) + fifteenth);
        expect(((jd(abhijit.start) + jd(abhijit.end)) / 2 - (jd(day.sunrise) + jd(day.sunset)) / 2).abs(), lessThan(second));
      }
    });
  });

  group('Chandra Bal', () {
    test('the Moon\'s Rashi at sunrise, and the six births with Chandra Bal in it', () {
      for (final date in sampleDates) {
        final first = muhurat(date).chandraBal.first;
        expect(first.moonRashi, moonRashiAt(jd(delhi(date).sunrise)));
        expect(first.rashis, goodBirths(first.moonRashi));
        expect(first.rashis, hasLength(6));
      }
    });

    test('a Moon Rashi change in the day gives a second span from its instant', () {
      final changes = <CivilDate>[];
      for (final date in month) {
        final day = delhi(date);
        final spans = muhurat(date).chandraBal;
        expect(spans.last.endsAt, isNull);
        expect(spans.length, lessThanOrEqualTo(2));
        if (spans.length == 1) {
          expect(moonRashiAt(jd(day.nextSunrise)), spans.single.moonRashi);
          continue;
        }
        changes.add(date);
        final [first, second] = spans;
        expect(second.moonRashi, (first.moonRashi + 1) % 12);
        expect(second.rashis, goodBirths(second.moonRashi));
        expect(insideDay(day, day.sunrise, first.endsAt!), isTrue);
        expect(moonRashiAt(jd(first.endsAt!) - minute), first.moonRashi);
        expect(moonRashiAt(jd(first.endsAt!) + minute), second.moonRashi);
      }
      expect(changes, isNotEmpty);
    });
  });

  group('Agni Vaas', () {
    test('(tithi at sunrise + weekday + 2) mod 4: 0 or 3 is Prithvi, 1 Aakash, 2 Patal', () {
      const residences = [AgniVaas.prithvi, AgniVaas.aakash, AgniVaas.patal, AgniVaas.prithvi];
      for (final date in sampleDates) {
        final day = delhi(date);
        expect(muhurat(date).agniVaas, residences[(tithiAt(jd(day.sunrise)) + day.vara + 2) % 4]);
      }
    });

    test('only Prithvi is good for a havan', () {
      expect([for (final a in AgniVaas.values) a.isAuspicious], [true, false, false]);
    });
  });

  group('Panchak', () {
    test('today\'s window lies in its period, which is the Moon in its last 60°', () {
      for (final date in month) {
        final day = delhi(date);
        final panchak = muhurat(date).panchak;
        if (panchak.window == null) {
          expect(panchak.period, isNull);
          expect(panchak.nextPeriod!.start.isAfter(day.nextSunrise), isTrue);
          continue;
        }
        final window = panchak.window!, period = panchak.period!;
        expect(panchak.nextPeriod, isNull);
        expect(insideDay(day, window.start, window.end), isTrue);
        expect(window.start, period.start.isBefore(day.sunrise) ? day.sunrise : period.start);
        expect(window.end, period.end.isAfter(day.nextSunrise) ? day.nextSunrise : period.end);
      }
      expect(month.where((d) => muhurat(d).panchak.window != null), isNotEmpty);
    });

    test('a day has a window only when the Moon is in Panchak at one of its sunrises', () {
      for (final date in month) {
        final day = delhi(date);
        final inside = inPanchak(jd(day.sunrise)) || inPanchak(jd(day.nextSunrise));
        expect(muhurat(date).panchak.window != null, inside, reason: '$date');
      }
    });

    test('a period starts and ends at the Moon\'s crossings of 300° and 360°', () {
      for (final date in month) {
        final panchak = muhurat(date).panchak;
        final period = panchak.period ?? panchak.nextPeriod!;
        expect(inPanchak(jd(period.start) - second), isFalse);
        expect(inPanchak(jd(period.start) + second), isTrue);
        expect(inPanchak(jd(period.end) - second), isTrue);
        expect(inPanchak(jd(period.end) + second), isFalse);
      }
    });
  });

  group('Bhadra', () {
    test('each window is in the day, and its residence follows the Moon\'s Rashi', () {
      const residence = {
        3: BhadraResidence.earth, 4: BhadraResidence.earth, 10: BhadraResidence.earth, 11: BhadraResidence.earth, //
        0: BhadraResidence.heaven, 1: BhadraResidence.heaven, 2: BhadraResidence.heaven, 7: BhadraResidence.heaven,
        5: BhadraResidence.underworld, 6: BhadraResidence.underworld, 8: BhadraResidence.underworld,
        9: BhadraResidence.underworld,
      };
      final windows = [
        for (final date in month)
          for (final w in muhurat(date).bhadra) (day: delhi(date), window: w),
      ];
      expect(windows, isNotEmpty);
      for (final (:day, :window) in windows) {
        expect(insideDay(day, window.start, window.end), isTrue);
        expect(moonRashiAt((jd(window.start) + jd(window.end)) / 2), window.moonRashi);
        expect(window.residence, residence[window.moonRashi]);
      }
    });

    test('a window is Vishti, the 8th karana of each seven, from its start to its end', () {
      for (final date in month) {
        final day = delhi(date);
        for (final w in muhurat(date).bhadra) {
          expect(const {8, 15, 22, 29, 36, 43, 50, 57}, contains(karanaAt((jd(w.start) + jd(w.end)) / 2)));
          final startsAtSunrise = w.start == day.sunrise;
          final endsAtNextSunrise = w.end == day.nextSunrise;
          final rashiSplit = moonRashiAt(jd(w.start) - minute) != moonRashiAt(jd(w.start) + minute);
          if (!startsAtSunrise && !rashiSplit) expect((karanaAt(jd(w.start) - minute) - 1) % 7, isNot(0));
          final rashiSplitEnd = moonRashiAt(jd(w.end) - minute) != moonRashiAt(jd(w.end) + minute);
          if (!endsAtNextSunrise && !rashiSplitEnd) expect((karanaAt(jd(w.end) + minute) - 1) % 7, isNot(0));
        }
      }
    });
  });

  group('Gandmool', () {
    test('each window is the Moon in a junction nakshatra, from its entry to its exit', () {
      final windows = [
        for (final date in month)
          for (final w in muhurat(date).gandmool) (day: delhi(date), window: w),
      ];
      expect(windows, isNotEmpty);
      for (final (:day, :window) in windows) {
        expect(const {1, 9, 10, 18, 19, 27}, contains(window.nakshatra));
        expect(insideDay(day, window.start, window.end), isTrue);
        expect(nakshatraAt((jd(window.start) + jd(window.end)) / 2), window.nakshatra);
        if (window.start != day.sunrise) expect(nakshatraAt(jd(window.start) - minute), isNot(window.nakshatra));
        if (window.end != day.nextSunrise) expect(nakshatraAt(jd(window.end) + minute), isNot(window.nakshatra));
      }
      // The Moon passes every nakshatra in a month, so every Gandmool one shows up.
      expect({for (final w in windows) w.window.nakshatra}, const {1, 9, 10, 18, 19, 27});
    });
  });
}

void yogaTests() {
  group('yogas', () {
    test('each Moon nakshatra of the day gives one Aanandadi yoga over its stay', () {
      for (final date in month) {
        final day = delhi(date);
        final aanandadi = [for (final y in muhurat(date).yogas) if (y.kind == DayYogaKind.aanandadi) y];
        expect(aanandadi.first.start, day.sunrise);
        expect(aanandadi.last.end, day.nextSunrise);
        for (final y in aanandadi) {
          expect(nakshatraAt((jd(y.start) + jd(y.end)) / 2), nakshatraAt(jd(y.start) + second));
        }
        for (final (a, b) in [for (var k = 1; k < aanandadi.length; k++) (aanandadi[k - 1], aanandadi[k])]) {
          expect(b.start, a.end);
        }
      }
    });

    test('Sunday with the Moon in Ashvini, Monday in Mrigashira, Tuesday in Ashlesha is Anand', () {
      // The Aanandadi table starts each weekday four nakshatras on (Muhurta Chintamani).
      expect([aanandadiIndex(1, 0), aanandadiIndex(5, 1), aanandadiIndex(9, 2)], [1, 1, 1]);
      expect(aanandadiIndex(27, 0), 28); // Revati is the 28th in the count with Abhijit
    });

    test('every yoga lies in its day; good and bad Dainika yogas both come in a month', () {
      final natures = <YogaNature>{};
      for (final date in month) {
        final day = delhi(date);
        for (final y in muhurat(date).yogas) {
          expect(insideDay(day, y.start, y.end), isTrue);
          if (y.kind == DayYogaKind.dainika) natures.add(y.nature);
          if (y.varjya case final v?) {
            expect(v.start, y.start);
            expect(v.end.isAfter(v.start), isTrue);
          }
        }
      }
      expect(natures, YogaNature.values.toSet());
    });

    test('Ravi Yoga is the Moon 4, 6, 9, 10, 13 or 20 nakshatras on from the Sun', () {
      final ravi = [
        for (final date in month)
          for (final y in muhurat(date).yogas)
            if (y.kind == DayYogaKind.ravi) (day: delhi(date), yoga: y),
      ];
      expect(ravi, isNotEmpty);
      for (final (:day, :yoga) in ravi) {
        final sun = siderealSunLongitude(jd(day.sunrise)) ~/ (360 / 27) + 1;
        final moon = nakshatraAt((jd(yoga.start) + jd(yoga.end)) / 2);
        expect(const {4, 6, 9, 10, 13, 20}, contains((moon - sun) % 27 + 1));
      }
    });

    test('Jwalamukhi is one of its tithi + nakshatra pairs', () {
      for (final date in [for (var k = 0; k < 365; k++) const CivilDate(2026, 1, 1).plusDays(k)].take(120)) {
        for (final y in muhurat(date).yogas.where((y) => y.kind == DayYogaKind.jwalamukhi)) {
          final middle = (jd(y.start) + jd(y.end)) / 2;
          expect(const {(1, 19), (5, 2), (8, 3), (9, 4), (10, 9)}, contains((tithiAt(middle), nakshatraAt(middle))));
          expect(y.nature, YogaNature.ashubh);
        }
      }
    });
  });
}
