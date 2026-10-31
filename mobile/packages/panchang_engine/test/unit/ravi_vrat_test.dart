// Ravi Vrat (Python `RaviVratFestival`): nine Sundays from the last Sunday of
// the year's non-Adhik Ashadha Shukla paksha. Python titles each day Ravi
// Pushya / Ravi Saptami / Ravi Vrat; titles come with Phase 6, so only the
// dates are ported. Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
// 5 Jul 2026 is a Sunday.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/ravi_vrat.dart';
import 'package:test/test.dart';

const ashadha = LunarMonth(index: 3, isAdhika: false);
const adhikAshadha = LunarMonth(index: 3, isAdhika: true);
const shravana = LunarMonth(index: 4, isAdhika: false);

/// One day per (month, Jain tithi) from [start], day after day.
List<FestivalDay> days(List<(LunarMonth, int)> readings, {CivilDate start = const CivilDate(2026, 7, 1)}) {
  var date = start;
  return [
    for (final (i, (month, tithi)) in readings.indexed)
      FestivalDay(
        date: i == 0 ? date : (date = date.next()),
        sunrise: 2461222.5 + i,
        sunset: 2461223.0 + i,
        sunriseTithi: tithi,
        jainTithi: tithi,
        eveningTithi: tithi,
        month: month,
        purnimantaMonth: month,
        standardOffset: Duration.zero,
      ),
  ];
}

List<(LunarMonth, int)> run(LunarMonth month, Iterable<int> tithis) => [for (final t in tithis) (month, t)];

/// Ashadha Shukla 1-15 from 1 Jul (Sundays 5 and 12 Jul), then Shravana to the end of September.
final List<(LunarMonth, int)> season = [
  ...run(ashadha, [for (var t = 1; t <= 15; t++) t]),
  ...run(shravana, [for (var i = 0; i < 77; i++) i % 30 + 16]),
];

FestivalEntry raviVrat() => const FestivalEntry(
  id: 'ravi_vrat',
  ruleType: 'RaviVrat',
  category: 'parva_vrat',
  name: 'Ravi Vrat',
  nameHindi: 'रवि व्रत',
  profiles: ['shwetambar_sthanakvasi'],
  jainMonth: 'Ashadha',
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

List<String> dates(List<FestivalDay> days, {int year = 2026}) =>
    [for (final o in raviVratSundays(raviVrat(), days, year: year)) o.start.iso];

const fromTwelfthJuly = [
  '2026-07-12', '2026-07-19', '2026-07-26', '2026-08-02', '2026-08-09',
  '2026-08-16', '2026-08-23', '2026-08-30', '2026-09-06',
];

void main() {
  test('nine Sundays from the last Sunday of Ashadha Shukla, named by the entry and dated', () {
    final o = raviVratSundays(raviVrat(), days(season), year: 2026);
    expect([for (final x in o) x.start.iso], fromTwelfthJuly);
    expect((o.first.id, o.first.occurrenceId, o.first.end.iso, o.first.ruleId, o.first.category, o.first.name),
        ('ravi_vrat', 'ravi_vrat_2026-07-12', '2026-07-12', 'ravi_vrat', 'parva_vrat', 'Ravi Vrat'));
  });

  test('a Sunday in Ashadha Krishna does not count', () {
    final readings = [
      ...run(ashadha, [1, 2, 3, 4, 5, 6, 7]),
      ...run(ashadha, [for (var t = 16; t <= 30; t++) t]),
      ...run(shravana, [for (var i = 0; i < 70; i++) i % 30 + 1]),
    ];
    expect(dates(days(readings)).first, '2026-07-05');
  });

  test('the Shukla paksha is read at the Jain day-start', () {
    final readings = [
      ...run(ashadha, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
      (ashadha, 26),
      ...run(shravana, [for (var i = 0; i < 70; i++) i % 30 + 1]),
    ];
    final withSunriseShukla = [
      for (final d in days(readings))
        FestivalDay(
          date: d.date, sunrise: d.sunrise, sunset: d.sunset, sunriseTithi: 11, jainTithi: d.jainTithi,
          eveningTithi: 11, month: d.month, purnimantaMonth: d.month, standardOffset: d.standardOffset,
        ),
    ];
    expect(dates(withSunriseShukla).first, '2026-07-05');
  });

  test('an Adhik Ashadha does not count', () {
    expect(dates(days(run(adhikAshadha, [for (var t = 1; t <= 15; t++) t]) + season.skip(15).toList())), isEmpty);
  });

  test("only the given year's Ashadha counts", () {
    expect(dates(days(season, start: const CivilDate(2025, 7, 1))), isEmpty);
  });

  test('Sundays past the last day read are left out', () {
    expect(dates(days(season.take(51).toList())), fromTwelfthJuly.take(6).toList());
  });
}
