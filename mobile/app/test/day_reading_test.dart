import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:panchang_engine/src/panchang/pachchakkhan.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:panchang_engine/src/time/julian_day.dart';

DayReading delhi(int year, int month, int day) =>
    readDay(DayRequest(date: CivilDate(year, month, day), lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'));

double jd(DateTime t) => julianDayFromUtc(t);
const second = Duration(seconds: 1);

void main() {
  group('a day (Delhi, 22 Oct 2026)', () {
    final day = delhi(2026, 10, 22);

    test('runs sunrise, reference instant, sunset, next sunrise in order', () {
      expect(day.reference.difference(day.sunrise), const Duration(hours: 2, minutes: 24));
      expect(day.sunset.isAfter(day.reference), isTrue);
      expect(day.nextSunrise.isAfter(day.sunset), isTrue);
      expect(day.nextSunrise.difference(day.sunrise).inHours, inInclusiveRange(23, 24));
    });

    test('sunrise falls on its own civil date in the city', () {
      final local = day.sunrise.add(const Duration(hours: 5, minutes: 30));
      expect((local.year, local.month, local.day), (2026, 10, 22));
    });

    test('the Jain tithi is the one holding at the reference instant, ending where the next begins', () {
      expect(day.jainTithi, tithiAt(jd(day.reference)));
      expect(day.jainTithiEnds.isAfter(day.reference), isTrue);
      expect(tithiAt(jd(day.jainTithiEnds.subtract(second))), day.jainTithi);
      expect(tithiAt(jd(day.jainTithiEnds.add(second))), day.jainTithi % 30 + 1);
    });

    test('the month is the Purnimanta month at the reference instant', () {
      expect(day.month, purnimantaMonth(jd(day.reference)));
    });

    test('the samvats match the Python engine (fixture core/delhi, 2026-10-22)', () {
      expect((day.vikramSamvat, day.viraNirvanaSamvat), (2083, 2552));
    });

    test('the nakshatra and its pada are read at sunrise', () {
      expect(day.nakshatra, nakshatraAt(jd(day.sunrise)));
      expect(day.nakshatraPada, nakshatraPadaAt(jd(day.sunrise)));
      expect(nakshatraAt(jd(day.nakshatraEnds.add(second))), day.nakshatra % 27 + 1);
    });

    test('pachchakkhan times come from the same sunrise, sunset and next sunrise', () {
      final times = pachchakkhanTimes(
        sunrise: jd(day.sunrise),
        sunset: jd(day.sunset),
        nextSunrise: jd(day.nextSunrise),
      );

      expect(day.pachchakkhan.map((p) => p.kind), TimedPachchakkhan.values);
      for (final (i, p) in day.pachchakkhan.indexed) {
        expect(jd(p.at), closeTo(times.completions[i].at, 1e-8));
      }
      expect(day.pachchakkhanEvening, day.sunset);
      expect(day.nextPachchakkhan(day.sunrise), TimedPachchakkhan.navkarsi);
      expect(day.nextPachchakkhan(day.sunset), isNull);
    });
  });

  group('the pachchakkhan phase through a day (Delhi, 22 Oct 2026)', () {
    final day = delhi(2026, 10, 22);
    DateTime at(TimedPachchakkhan kind) => day.pachchakkhan.firstWhere((p) => p.kind == kind).at;

    test('the parana is the next day\'s Navkarsi', () {
      expect(day.pachchakkhanParana, delhi(2026, 10, 23).pachchakkhan.first.at);
    });

    test('before sunrise, Navkarsi is next', () {
      expect(
        day.pachchakkhanPhase(day.sunrise.subtract(const Duration(hours: 2))),
        NextCompletion(.navkarsi, at(.navkarsi)),
      );
    });

    test('each completion is next until its instant, then the one after it', () {
      for (final (i, p) in day.pachchakkhan.indexed.skip(1)) {
        final previous = day.pachchakkhan[i - 1].at;
        expect(day.pachchakkhanPhase(previous), NextCompletion(p.kind, p.at), reason: '${p.kind}');
        expect(day.pachchakkhanPhase(p.at.subtract(second)), NextCompletion(p.kind, p.at), reason: '${p.kind}');
      }
    });

    test('after Avaddh, the evening pachchakkhan is due before sunset', () {
      expect(day.pachchakkhanPhase(at(.avaddh)), EveningDeadline(day.pachchakkhanEvening));
      expect(day.pachchakkhanPhase(day.sunset.subtract(second)), EveningDeadline(day.pachchakkhanEvening));
    });

    test('from sunset, everything is done until the parana', () {
      expect(day.pachchakkhanPhase(day.sunset), AllDone(day.pachchakkhanParana));
      expect(day.pachchakkhanPhase(day.nextSunrise), AllDone(day.pachchakkhanParana));
    });
  });

  // The Python engine's Jain tithis for Delhi, October 2026 (generate_location_panchang,
  // modern sunrise): 2 Oct 21 → 3 Oct 23, 18 and 19 Oct both 8, 26 Oct 15 → 27 Oct 17.
  // mobile-ui-design.md §3.2 names this month as the test month.
  group('vriddhi and kshaya in October 2026 (Delhi)', () {
    final october = {for (var d = 1; d <= 31; d++) d: delhi(2026, 10, d)};

    test('vriddhi is the 18th (first day) and 19th (second day) only', () {
      final vriddhi = {
        for (final MapEntry(:key, :value) in october.entries)
          if (value.vriddhi != null) key: value.vriddhi,
      };

      expect(vriddhi, {18: Vriddhi.firstDay, 19: Vriddhi.secondDay});
    });

    test('kshaya falls on the 3rd (Krishna Saptami lost) and 27th (Krishna Pratipada lost) only', () {
      final kshaya = {
        for (final MapEntry(:key, :value) in october.entries)
          if (value.kshaya != null) key: value.kshaya!.lost,
      };

      expect(kshaya, {3: 22, 27: 16});
    });

    test('a lost Amavasya wraps to Shukla Pratipada (30 Sep 2027, found by scanning the engine)', () {
      final day = delhi(2027, 9, 30);

      expect(day.kshaya!.lost, 30);
      expect(day.jainTithi, 1);
    });

    test('a lost tithi starts after the previous reference instant and ends before this one', () {
      for (final d in [3, 27]) {
        final lost = october[d]!.kshaya!;
        final middle = lost.starts.add(lost.ends.difference(lost.starts) ~/ 2);

        expect(lost.starts.isAfter(october[d - 1]!.reference), isTrue);
        expect(lost.ends.isBefore(october[d]!.reference), isTrue);
        expect(tithiAt(jd(middle)), lost.lost);
      }
    });

    test('vriddhi and kshaya agree with the neighbouring days', () {
      for (var d = 2; d <= 30; d++) {
        final (before, today, after) = (october[d - 1]!, october[d]!, october[d + 1]!);

        expect(today.vriddhi == Vriddhi.secondDay, before.jainTithi == today.jainTithi, reason: 'Oct $d');
        expect(today.vriddhi == Vriddhi.firstDay, after.jainTithi == today.jainTithi, reason: 'Oct $d');
        expect(today.kshaya != null, today.jainTithi == (before.jainTithi + 1) % 30 + 1, reason: 'Oct $d');
      }
    });
  });

  group('tithi boundary near the reference instant', () {
    const window = Duration(minutes: 45);

    test('is flagged exactly when a tithi changes within 45 minutes of it', () {
      for (var d = 1; d <= 30; d++) {
        final day = delhi(2026, 11, d);
        final ref = day.reference;
        final changesSoon = day.jainTithiEnds.difference(ref) <= window;
        final changedJustBefore = tithiAt(jd(ref.subtract(window))) != day.jainTithi;

        expect(day.boundary != null, changesSoon || changedJustBefore, reason: 'Nov $d');
      }
    });

    test('27 Nov 2026: Krishna Tritiya ends 32 minutes after the reference (mockup board 1b)', () {
      final boundary = delhi(2026, 11, 27).boundary!;

      expect(boundary.isStart, isFalse);
      expect(boundary.gap.inMinutes, inInclusiveRange(31, 32));
    });

    // Found by scanning the engine (Delhi, modern sunrise); the Dart Jain tithi
    // matches Python exactly on every core/delhi day 2016-2040.
    test('23 Feb 2026: the Jain tithi began 7 minutes before the reference', () {
      final boundary = delhi(2026, 2, 23).boundary!;

      expect(boundary.isStart, isTrue);
      expect(boundary.gap.inMinutes, inInclusiveRange(6, 7));
    });

    test('a boundary before the reference is the start of the Jain tithi', () {
      for (var d = 1; d <= 30; d++) {
        final day = delhi(2026, 11, d);
        final boundary = day.boundary;
        if (boundary == null || !boundary.isStart) continue;

        expect(boundary.at.isBefore(day.reference), isTrue);
        expect(tithiAt(jd(boundary.at.add(second))), day.jainTithi);
      }
    });
  });
}
