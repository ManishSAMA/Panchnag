import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/panchang/elements.dart' show jainTithiOffsetDays, tithiAt;
import 'package:test/test.dart';

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

void main() {
  group('the festival window for 2026 (Delhi)', () {
    final days = festivalDays(location: delhiCity, year: 2026, sunriseRule: SunriseRule.modern);

    test('runs day by day from 1 Dec of the year before to 31 Jan of the year after', () {
      expect(days.first.date, const CivilDate(2025, 12, 1));
      expect(days.last.date, const CivilDate(2027, 1, 31));
      for (var i = 1; i < days.length; i++) {
        expect(days[i].date, days[i - 1].date.next());
      }
    });

    test('reads the sunrise tithi at sunrise, the Jain tithi 2 h 24 min later and the evening tithi at sunset', () {
      for (final d in days.take(40)) {
        expect(d.sunset, greaterThan(d.sunrise + jainTithiOffsetDays));
        expect(d.sunriseTithi, tithiAt(d.sunrise));
        expect(d.jainTithi, tithiAt(d.sunrise + jainTithiOffsetDays));
        expect(d.eveningTithi, tithiAt(d.sunset));
      }
    });

    test('a Shukla day is in its own Amanta month in the Purnimanta reckoning too', () {
      for (final d in days.where((d) => d.jainTithi <= 15)) {
        expect(d.purnimantaMonth, d.month);
      }
    });

    test('a Krishna day takes the month of the next Shukla paksha, with its Adhik flag', () {
      for (var i = 0; i < days.length; i++) {
        if (days[i].jainTithi <= 15) continue;
        final nextShukla = days.skip(i).where((d) => d.jainTithi <= 15).firstOrNull;
        if (nextShukla == null) continue;
        expect(days[i].purnimantaMonth, nextShukla.month, reason: '${days[i].date}');
      }
    });

    // 2026 has an Adhik Jyeshtha (17 May - 15 Jun). Its Krishna half reads as the
    // Nija Jyeshtha in the Purnimanta reckoning, and the Krishna half before it as Adhik.
    test('the Adhik tag flips between the Amanta and Purnimanta readings of a Krishna paksha', () {
      final krishnaInAdhik = days.firstWhere((d) => d.month.isAdhika && d.jainTithi > 15);
      expect(krishnaInAdhik.purnimantaMonth.isAdhika, isFalse);
      final krishnaBefore = days.firstWhere((d) => d.purnimantaMonth.isAdhika && d.jainTithi > 15);
      expect(krishnaBefore.month.isAdhika, isFalse);
    });

    test("carries the zone's standard UTC offset, the clock Python's vrat providers read local times on", () {
      expect(days.map((d) => d.standardOffset).toSet(), {const Duration(hours: 5, minutes: 30)});
    });

    test('Krishna days after the last Shukla paksha take the following month name', () {
      final last = days.last;
      if (last.jainTithi <= 15) return;
      expect(last.purnimantaMonth.index, (last.month.index + 1) % 12);
      expect(last.purnimantaMonth.isAdhika, last.month.isAdhika);
    });
  });

  // The window reads its later tithis from the sunrise elongations where it
  // can; every reading must still be the tithi at its instant.
  for (final rule in SunriseRule.values) {
    test('every reading of a whole window is the tithi at its instant (${rule.name})', () {
      const places = [
        delhiCity,
        Location(lat: 51.5074, lon: -0.1278, timezone: 'Europe/London'),
        Location(lat: 40.7128, lon: -74.0060, timezone: 'America/New_York'),
      ];
      final wrong = [
        for (final (place, year) in [(places[0], 2031), (places[1], 2026), (places[2], 2038)])
          for (final d in festivalDays(location: place, year: year, sunriseRule: rule))
            if (d.sunriseTithi != tithiAt(d.sunrise) ||
                d.jainTithi != tithiAt(d.sunrise + jainTithiOffsetDays) ||
                d.eveningTithi != tithiAt(d.sunset))
              '${place.timezone} ${d.date}',
      ];

      expect(wrong, isEmpty);
    });
  }

  test('the standard offset ignores daylight time (London keeps GMT through the summer)', () {
    final london = festivalDays(
      location: const Location(lat: 51.5074, lon: -0.1278, timezone: 'Europe/London'),
      year: 2026,
      sunriseRule: SunriseRule.modern,
    );
    expect(london.map((d) => d.standardOffset).toSet(), {Duration.zero});
  });
}
