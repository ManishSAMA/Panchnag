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
}
