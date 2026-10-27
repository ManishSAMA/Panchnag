import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

const second = 1 / 86400;
const synodicMonthMax = 29.9;

/// 2026-05-25 0h UT, inside 2026's Adhik Jyeshtha (17 May - 15 Jun 2026, the
/// year's Adhik Maas in every printed panchang).
const adhikJyeshtha2026 = 2461185.5;
const start = 2461334.5; // 2026-10-21 0h UT

void main() {
  group('new moons', () {
    test('the one before an instant is the last tithi 30 -> 1 change before it', () {
      final newMoon = newMoonBefore(start);

      expect(newMoon, lessThan(start));
      expect(start - newMoon, lessThan(synodicMonthMax));
      expect(tithiAt(newMoon - second), 30);
      expect(tithiAt(newMoon + second), 1);
    });

    test('the one after an instant is the first tithi 30 -> 1 change after it', () {
      final newMoon = newMoonAfter(start);

      expect(newMoon, greaterThan(start));
      expect(newMoon - start, lessThan(synodicMonthMax));
      expect(tithiAt(newMoon - second), 30);
      expect(tithiAt(newMoon + second), 1);
    });

    test('consecutive new moons are one lunar month apart', () {
      final before = newMoonBefore(start);

      expect(newMoonAfter(before + 1) - before, inInclusiveRange(29.2, synodicMonthMax));
    });
  });

  group('sankrantis', () {
    test('a month between new moons holds the Sun sign it enters', () {
      final from = newMoonBefore(start);
      final signs = sankrantisBetween(from, newMoonAfter(from + 1));

      expect(signs, hasLength(1));
      expect(signs.single, inInclusiveRange(0, 11));
    });
  });

  group('amanta month', () {
    test('is named the same from one new moon to the next', () {
      final from = newMoonBefore(start);
      final to = newMoonAfter(from + 1);

      expect(amantaMonth(from + 0.1), amantaMonth(to - 0.1));
    });

    test('advances by one month at each new moon outside an adhik year', () {
      final current = amantaMonth(start);
      final next = amantaMonth(newMoonAfter(start) + 0.1);

      expect(next.index, (current.index + 1) % 12);
      expect(next.isAdhika, isFalse);
    });

    test('2026 has an Adhik Jyeshtha before the regular Jyeshtha', () {
      final adhik = amantaMonth(adhikJyeshtha2026);
      final nija = amantaMonth(newMoonAfter(adhikJyeshtha2026) + 0.1);

      expect(adhik, const LunarMonth(index: 2, isAdhika: true));
      expect(adhik.name, 'Adhika Jyeshtha');
      expect(nija, const LunarMonth(index: 2, isAdhika: false));
      expect(nija.name, 'Jyeshtha');
    });
  });

  group('lunar months across a range', () {
    final spans = lunarMonthsBetween(start, start + 120);

    test('run new moon to new moon without gaps and cover the range', () {
      expect(spans.first.start, lessThanOrEqualTo(start));
      expect(spans.last.end, greaterThan(start + 120));
      for (var i = 1; i < spans.length; i++) {
        expect(spans[i].start, spans[i - 1].end);
      }
    });

    test('name each month as amantaMonth does', () {
      for (final span in spans) {
        expect(span.month, amantaMonth((span.start + span.end) / 2));
      }
    });

    test('answer for any instant inside them', () {
      final lookup = amantaLookup(spans);

      for (var jd = start; jd < start + 120; jd += 7.3) {
        expect(lookup(jd), amantaMonth(jd));
      }
    });
  });

  group('purnimanta month', () {
    test('gives the same answer from a lookup table as from scratch', () {
      final lookup = amantaLookup(lunarMonthsBetween(start - 30, start + 90));

      for (var jd = start; jd < start + 60; jd += 2.9) {
        expect(purnimantaMonth(jd, amanta: lookup), purnimantaMonth(jd));
      }
    });

    test('a Shukla paksha has the same month as amanta', () {
      final shukla = newMoonBefore(start) + 3;

      expect(purnimantaMonth(shukla), amantaMonth(shukla));
    });

    test('a Krishna paksha takes the month that follows it in amanta', () {
      final krishna = newMoonAfter(start) - 3;

      expect(purnimantaMonth(krishna), amantaMonth(newMoonAfter(start) + 0.1));
    });

    test('the first moment of a Krishna paksha also takes the following month', () {
      // The longest wait for the new moon: all 15 Krishna tithis still ahead.
      var purnima = newMoonBefore(start) + 12;
      while (tithiAt(purnima) != 15) {
        purnima = tithiEnd(purnima) + second;
      }
      final shuklaEnds = tithiEnd(purnima);
      expect(tithiAt(shuklaEnds + second), 16);

      expect(purnimantaMonth(shuklaEnds + second), amantaMonth(newMoonAfter(start) + 0.1));
    });
  });
}
