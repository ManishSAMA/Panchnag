import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

const second = 1 / 86400;

void main() {
  const start = 2461334.5; // 2026-10-21 0h UT

  group('tithi', () {
    test('index is always 1-30', () {
      for (var i = 0; i < 60; i++) {
        expect(tithiAt(start + i * 0.37), inInclusiveRange(1, 30));
      }
    });

    test('ends where the next tithi begins', () {
      final index = tithiAt(start);
      final end = tithiEnd(start);

      expect(end, greaterThan(start));
      expect(end - start, lessThan(1.1)); // a tithi never lasts much over a day
      expect(tithiAt(end - second), index);
      expect(tithiAt(end + second), index % 30 + 1);
    });

    test('a tithi ending exactly at the query instant is not reported again', () {
      final end = tithiEnd(start);

      expect(tithiEnd(end + second), greaterThan(end + 0.5));
    });
  });

  group('nakshatra', () {
    test('index is always 1-27', () {
      for (var i = 0; i < 60; i++) {
        expect(nakshatraAt(start + i * 0.37), inInclusiveRange(1, 27));
      }
    });

    test('ends where the next nakshatra begins', () {
      final index = nakshatraAt(start);
      final end = nakshatraEnd(start);

      expect(end, greaterThan(start));
      expect(nakshatraAt(end - second), index);
      expect(nakshatraAt(end + second), index % 27 + 1);
    });

    test('pada is always 1-4', () {
      for (var i = 0; i < 60; i++) {
        expect(nakshatraPadaAt(start + i * 0.37), inInclusiveRange(1, 4));
      }
    });

    test('a nakshatra starts in pada 1, ends in pada 4, and passes through each pada in turn', () {
      final begin = nakshatraEnd(start), end = nakshatraEnd(begin + second);
      final padas = [for (var jd = begin + second; jd < end; jd += 0.01) nakshatraPadaAt(jd)];

      expect(padas.first, 1);
      expect(nakshatraPadaAt(end - second), 4);
      expect(padas.toSet().toList(), [1, 2, 3, 4]);
      for (var i = 1; i < padas.length; i++) {
        expect(padas[i] - padas[i - 1], anyOf(0, 1));
      }
    });
  });

  group('tithis of a day', () {
    test('cover sunrise to the next sunrise and chain without gaps', () {
      const sunrise = 2461334.538, nextSunrise = 2461335.539;
      final tithis = dayTithis(sunrise, nextSunrise);

      expect(tithis.first.index, tithiAt(sunrise));
      expect(tithis.last.endsAt, isNull);
      for (final (a, b) in [for (var i = 1; i < tithis.length; i++) (tithis[i - 1], tithis[i])]) {
        expect(a.endsAt, inExclusiveRange(sunrise, nextSunrise));
        expect(b.index, a.index % 30 + 1);
      }
    });
  });

  // The festival window reads three tithis a day; the later two can often be
  // told from the elongations at the sunrises around them.
  group('tithi between two elongation readings', () {
    ElongationReading reading(double jd) => (jd: jd, elongation: elongation(jd));
    final from2016 = [for (var i = 0; i < 300; i++) 2457388.5 + i * 30.43];

    test('the elongation grows within the rates the readings rely on, 2016-2040', () {
      for (final jd in from2016) {
        for (final span in [0.1, 0.45, 1.0]) {
          final growth = (elongation(jd + span) - elongation(jd)) % 360;
          expect(growth / span, inExclusiveRange(10.0, 15.0), reason: 'JD $jd over $span d');
        }
      }
    });

    test('equals the tithi read at the instant, also a second either side of each tithi end', () {
      final instants = [
        for (final jd in from2016) ...[jd, tithiEnd(jd) - second, tithiEnd(jd) + second],
      ];
      for (final instant in instants) {
        for (final before in [0.1, 0.45, 0.9]) {
          final after = 1.0 - before;
          expect(tithiBetween(instant, reading(instant - before), reading(instant + after)), tithiAt(instant),
              reason: 'JD $instant, $before d after a reading');
          expect(tithiBetween(instant, reading(instant - before), null), tithiAt(instant),
              reason: 'JD $instant, $before d after the last reading');
        }
      }
    });

    // Made-up readings show where the answer comes from: an instant whose sky
    // holds a mid-month tithi is named from the readings when they settle it.
    group('when the readings alone settle the tithi', () {
      final instant = from2016.firstWhere((jd) => tithiAt(jd) == 15);

      test('reads it from both sides, though the earlier reading alone would not', () {
        // 5° + [4.75°, 8°] spans the 12° boundary; 16.5° − [4.75°, 8°] keeps below it.
        final before = (jd: instant - 0.5, elongation: 5.0);
        final after = (jd: instant + 0.5, elongation: 16.5);
        expect(tithiBetween(instant, before, after), 1);
      });

      test('takes the lower bound from the later reading when it is the tighter one', () {
        // 0° + [8.55°, 14.4°] spans 12°; 14.5° − [0.95°, 1.6°] lies above it.
        final before = (jd: instant - 0.9, elongation: 0.0);
        final after = (jd: instant + 0.1, elongation: 14.5);
        expect(tithiBetween(instant, before, after), 2);
      });

      test('reads it across 360°, the later reading having wrapped round to Shukla 1', () {
        final before = (jd: instant - 0.5, elongation: 350.0);
        final after = (jd: instant + 0.5, elongation: 1.5);
        expect(tithiBetween(instant, before, after), 30);
      });
    });

    test('names the tithi of an elongation as tithiAt does', () {
      for (final jd in from2016) {
        expect(tithiOf(elongation(jd)), tithiAt(jd));
      }
    });
  });
}
