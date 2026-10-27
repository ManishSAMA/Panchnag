import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/calendar/month.dart' show purnimantaMonth;
import 'package:panchang_engine/src/panchang/elements.dart' show nakshatraAt, nakshatraPadaAt, tithiAt;
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

PanchangDay delhi(int year, int month, int day, {SunriseRule rule = SunriseRule.modern}) =>
    const PanchangEngine().day(location: delhiCity, date: CivilDate(year, month, day), sunriseRule: rule);

double jd(DateTime t) => julianDayFromUtc(t);
const second = Duration(seconds: 1);

void main() {
  group('a day (Delhi, 22 Oct 2026)', () {
    final day = delhi(2026, 10, 22);

    test('runs sunrise, reference instant, sunset, next sunrise in order, all in UTC', () {
      expect(day.jainTithi.reference.difference(day.sunrise), const Duration(hours: 2, minutes: 24));
      expect(day.sunset.isAfter(day.jainTithi.reference), isTrue);
      expect(day.nextSunrise.isAfter(day.sunset), isTrue);
      expect(day.nextSunrise.difference(day.sunrise).inHours, inInclusiveRange(23, 24));
      expect([day.sunrise, day.sunset, day.nextSunrise].every((t) => t.isUtc), isTrue);
    });

    test('sunrise falls on its own civil date in the city', () {
      final local = day.sunrise.add(const Duration(hours: 5, minutes: 30));
      expect((local.year, local.month, local.day), (2026, 10, 22));
    });

    test('the day\'s tithis run in order from sunrise, the last one still holding at the next sunrise', () {
      expect(day.tithis.first.index, tithiAt(jd(day.sunrise)));
      expect(day.tithis.last.endsAt, isNull);
      for (final t in day.tithis.take(day.tithis.length - 1)) {
        expect(t.endsAt!.isAfter(day.sunrise) && t.endsAt!.isBefore(day.nextSunrise), isTrue);
      }
    });

    test('the Jain tithi holds at the reference instant, from where it begins to where the next begins', () {
      final jain = day.jainTithi;
      expect(jain.index, tithiAt(jd(jain.reference)));
      expect(jain.startsAt.isBefore(jain.reference) && jain.endsAt.isAfter(jain.reference), isTrue);
      expect(tithiAt(jd(jain.startsAt.add(second))), jain.index);
      expect(tithiAt(jd(jain.startsAt.subtract(second))), (jain.index + 28) % 30 + 1);
      expect(tithiAt(jd(jain.endsAt.subtract(second))), jain.index);
      expect(tithiAt(jd(jain.endsAt.add(second))), jain.index % 30 + 1);
    });

    test('the month is the Purnimanta month at the reference instant', () {
      expect(day.month, purnimantaMonth(jd(day.jainTithi.reference)));
    });

    test('the vara and samvats match the Python engine (fixture core/delhi, 2026-10-22)', () {
      expect((day.vara, day.vikramSamvat, day.viraNirvanaSamvat), (4, 2083, 2552));
    });

    test('the nakshatra and its pada are read at sunrise', () {
      expect(day.nakshatra.index, nakshatraAt(jd(day.sunrise)));
      expect(day.nakshatra.pada, nakshatraPadaAt(jd(day.sunrise)));
      expect(nakshatraAt(jd(day.nakshatra.endsAt.add(second))), day.nakshatra.index % 27 + 1);
    });

    test('the choghadiya runs sunrise to the next sunrise in 16 slots', () {
      expect(day.choghadiya, hasLength(16));
      expect(day.choghadiya.first.start, day.sunrise);
      expect(day.choghadiya[8].start.difference(day.sunset).abs(), lessThan(const Duration(milliseconds: 1)));
      expect(day.choghadiya.last.end.difference(day.nextSunrise).abs(), lessThan(const Duration(milliseconds: 1)));
      expect(day.choghadiya.first.name, Choghadiya.shubh);
      expect(day.choghadiya.map((c) => c.isNight), [...List.filled(8, false), ...List.filled(8, true)]);
    });
  });

  group('the pachchakkhan through a day (Delhi, 22 Oct 2026)', () {
    final day = delhi(2026, 10, 22);
    final p = day.pachchakkhan;
    DateTime at(TimedPachchakkhan kind) => p.completions.firstWhere((c) => c.kind == kind).at;

    test('Navkarsi is 48 minutes after sunrise and Purimaddh is midday; the evening time is sunset', () {
      expect(p.completions.map((c) => c.kind), TimedPachchakkhan.values);
      expect(at(.navkarsi).difference(day.sunrise), const Duration(minutes: 48));
      final midday = day.sunrise.add(day.sunset.difference(day.sunrise) ~/ 2);
      expect(at(.purimaddh).difference(midday).abs(), lessThan(const Duration(milliseconds: 1)));
      expect(p.evening, day.sunset);
    });

    test('the parana is the next day\'s Navkarsi', () {
      expect(p.parana, delhi(2026, 10, 23).pachchakkhan.completions.first.at);
    });

    test('before sunrise, Navkarsi is next', () {
      expect(p.phaseAt(day.sunrise.subtract(const Duration(hours: 2))), NextCompletion(.navkarsi, at(.navkarsi)));
    });

    test('each completion is next until its instant, then the one after it', () {
      for (final (i, c) in p.completions.indexed.skip(1)) {
        expect(p.phaseAt(p.completions[i - 1].at), NextCompletion(c.kind, c.at), reason: '${c.kind}');
        expect(p.phaseAt(c.at.subtract(second)), NextCompletion(c.kind, c.at), reason: '${c.kind}');
      }
    });

    test('after Avaddh, the evening pachchakkhan is due before sunset', () {
      expect(p.phaseAt(at(.avaddh)), EveningDeadline(p.evening));
      expect(p.phaseAt(day.sunset.subtract(second)), EveningDeadline(p.evening));
    });

    test('from sunset, everything is done until the parana', () {
      expect(p.phaseAt(day.sunset), AllDone(p.parana));
      expect(p.phaseAt(day.nextSunrise), AllDone(p.parana));
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
      expect(day.jainTithi.index, 1);
    });

    test('a lost tithi starts after the previous reference instant and ends before this one', () {
      for (final d in [3, 27]) {
        final lost = october[d]!.kshaya!;
        final middle = lost.startsAt.add(lost.endsAt.difference(lost.startsAt) ~/ 2);

        expect(lost.startsAt.isAfter(october[d - 1]!.jainTithi.reference), isTrue);
        expect(lost.endsAt.isBefore(october[d]!.jainTithi.reference), isTrue);
        expect(tithiAt(jd(middle)), lost.lost);
      }
    });

    test('vriddhi and kshaya agree with the neighbouring days', () {
      for (var d = 2; d <= 30; d++) {
        final (before, today, after) = (october[d - 1]!, october[d]!, october[d + 1]!);
        final (b, t, a) = (before.jainTithi.index, today.jainTithi.index, after.jainTithi.index);

        expect(today.vriddhi == Vriddhi.secondDay, b == t, reason: 'Oct $d');
        expect(today.vriddhi == Vriddhi.firstDay, a == t, reason: 'Oct $d');
        expect(today.kshaya != null, t == (b + 1) % 30 + 1, reason: 'Oct $d');
      }
    });
  });

  test('the sunrise rule reaches every reading: traditional sunrise (disc centre, no refraction) is later', () {
    final modern = delhi(2026, 10, 22), traditional = delhi(2026, 10, 22, rule: SunriseRule.traditional);

    expect(traditional.sunrise.isAfter(modern.sunrise), isTrue);
    expect(traditional.jainTithi.reference.difference(traditional.sunrise), const Duration(hours: 2, minutes: 24));
    expect(traditional.choghadiya.first.start, traditional.sunrise);
    expect(traditional.pachchakkhan.completions.first.at.isAfter(modern.pachchakkhan.completions.first.at), isTrue);
  });

  test('a day is a plain value: reading it twice gives equal parts', () {
    final (a, b) = (delhi(2026, 10, 22), delhi(2026, 10, 22));

    expect((a.sunrise, a.jainTithi, a.nakshatra, a.kshaya), (b.sunrise, b.jainTithi, b.nakshatra, b.kshaya));
  });
}
