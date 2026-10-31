// Rohini Nakshatra Vrat (Python `RohiniVratFestival`, `vrats/rohini.py`): the
// day Rohini holds at sunrise, or the day after a Rohini that touches neither
// sunrise. Python reads the sunrise's local clock time as UTC (a bug kept for
// parity, plans/mobile-phase5-festivals.md §6.1), so the tests place sunrises
// around a real Rohini span and say which clock reading falls where.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/rohini.dart';
import 'package:panchang_engine/src/panchang/elements.dart' show nakshatraAt, nakshatraEnd;
import 'package:test/test.dart';

import '../support/reference_rohini.dart';

const shravana = LunarMonth(index: 4, isAdhika: false);
const rohini = 4;

/// The first Rohini to begin after 1 Jan 2026, as (start, end) UT Julian Days.
final (double, double) rohiniSpan = () {
  var instant = nakshatraEnd(2461041.5) + 1e-4;
  while (nakshatraAt(instant) != rohini) {
    instant = nakshatraEnd(instant) + 1e-4;
  }
  final end = nakshatraEnd(instant);
  return (instant, end);
}();

final double inRohini = (rohiniSpan.$1 + rohiniSpan.$2) / 2;
/// Far enough before Rohini to stay outside it when read 5 h 30 min later.
final double beforeRohini = rohiniSpan.$1 - 0.5;

/// Consecutive days from 1 Dec 2025, the first day of a 2026 festival window,
/// with the given sunrises; days not listed get a sunrise outside Rohini.
List<FestivalDay> days(Map<int, double> sunrises, {Duration offset = Duration.zero, int count = 420}) {
  var date = const CivilDate(2025, 12, 1);
  return [
    for (var i = 0; i < count; i++)
      FestivalDay(
        date: i == 0 ? date : (date = date.next()),
        sunrise: sunrises[i] ?? beforeRohini,
        sunset: (sunrises[i] ?? beforeRohini) + 0.5,
        sunriseTithi: 1,
        jainTithi: 1,
        eveningTithi: 1,
        month: shravana,
        purnimantaMonth: shravana,
        standardOffset: offset,
      ),
  ];
}

FestivalEntry rohiniEntry() => const FestivalEntry(
  id: 'rohini_nakshatra_parv_vrat',
  ruleType: 'RohiniVrat',
  category: 'parva',
  name: 'Rohini Nakshatra Vrat',
  nameHindi: 'रोहिणी नक्षत्र व्रत',
  profiles: ['all'],
  jainMonth: null,
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

/// 1 Dec 2025 is day 0, so 15 Dec 2025 is day 14, 1 Jan 2026 day 31 and 31 Dec 2026 day 395.
List<String> dates(List<FestivalDay> days) =>
    [for (final o in rohiniVrat(rohiniEntry(), days, year: 2026)) o.start.iso];

void main() {
  test('the day Rohini holds at sunrise, named and dated as a one-day parva', () {
    final o = rohiniVrat(rohiniEntry(), days({40: inRohini}), year: 2026);
    expect([for (final x in o) (x.id, x.occurrenceId, x.start.iso, x.end.iso, x.ruleId, x.category, x.name)], [
      ('rohini_nakshatra_parv_vrat', 'rohini_nakshatra_parv_vrat:2026-01-10', '2026-01-10', '2026-01-10',
          'rohini_nakshatra_parv_vrat', 'parva', 'Rohini Nakshatra Vrat'),
    ]);
  });

  test('a Rohini that begins after one sunrise and ends before the next gives the next day', () {
    expect(dates(days({40: beforeRohini, 41: rohiniSpan.$2 + 0.05})), ['2026-01-11']);
  });

  // The search skips a day whose Rohini the Moon cannot finish by the next
  // sunrise; two days before Rohini, with the next sunrise past its end, it can.
  test('a whole Rohini between sunrises three days apart gives the later day', () {
    expect(dates(days({40: rohiniSpan.$1 - 2, 41: rohiniSpan.$2 + 0.05})), ['2026-01-11']);
  });

  test('a Rohini that begins after a sunrise and lasts to the next gives that next day only', () {
    expect(dates(days({40: beforeRohini, 41: rohiniSpan.$2 - 0.05})), ['2026-01-11']);
  });

  test('the sunrise is read on its local clock taken as UTC: 5 h 30 min later in India', () {
    final sunrise = rohiniSpan.$1 - 0.1;
    expect(dates(days({40: sunrise})), isEmpty);
    expect(dates(days({40: sunrise}, offset: const Duration(hours: 5, minutes: 30))), ['2026-01-10']);
  });

  test('after a vrat the search skips ahead 20 days from the day Rohini was found', () {
    final rohiniDays = {for (final i in [40, 45, 59, 60]) i: inRohini};
    expect(dates(days(rohiniDays)), ['2026-01-10', '2026-01-30']);
  });

  test('the search starts on 15 Dec of the year before, so a Rohini on 14 Dec does not shift it', () {
    expect(dates(days({13: inRohini, 15: inRohini, 36: inRohini})), ['2025-12-16', '2026-01-06']);
    expect(dates(days({14: inRohini})), ['2025-12-15']);
  });

  test('the search ends on 31 Dec: a Rohini at a later sunrise is not looked for', () {
    expect(dates(days({395: inRohini, 396: inRohini})), ['2026-12-31']);
    expect(dates(days({396: inRohini})), isEmpty);
  });

  // The search skips days Rohini cannot reach by the next sunrise; on real
  // readings it must find what the full search finds.
  test('finds the same days as the full nakshatra search, on real windows', () {
    for (final (location, year) in [
      (const Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'), 2026),
      (const Location(lat: 51.5074, lon: -0.1278, timezone: 'Europe/London'), 2030),
      (const Location(lat: 40.7128, lon: -74.0060, timezone: 'America/New_York'), 2035),
    ]) {
      final window = festivalDays(location: location, year: year, sunriseRule: SunriseRule.modern);
      final ours = [for (final o in rohiniVrat(rohiniEntry(), window, year: year)) o.start.iso];
      final full = [for (final o in referenceRohiniVrat(rohiniEntry(), window, year: year)) o.start.iso];

      expect(ours, full, reason: '${location.timezone} $year');
      expect(full, hasLength(greaterThan(10)));
    }
  });
}
