import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:test/test.dart';

const shravana = LunarMonth(index: 4, isAdhika: false);
const bhadrapada = LunarMonth(index: 5, isAdhika: false);

/// Consecutive days from 1 Aug 2026 with the given Jain tithis; the sunrise and
/// evening tithis are set apart so a test can see they are left alone.
List<FestivalDay> daysWith(List<int> jainTithis, {List<LunarMonth>? months}) => [
  for (final (i, t) in jainTithis.indexed)
    FestivalDay(
      date: CivilDate(2026, 8, 1 + i),
      sunrise: 2461253.5 + i,
      sunset: 2461254.0 + i,
      sunriseTithi: 99,
      jainTithi: t,
      eveningTithi: 98,
      month: months?[i] ?? shravana,
      purnimantaMonth: months?[i] ?? shravana,
    ),
];

void main() {
  test('days without a vriddhi read as they are', () {
    expect([for (final d in vratView(daysWith([7, 8, 9, 11]))) d.jainTithi], [7, 8, 9, 11]);
  });

  test('the first of two days sharing a Jain tithi reads as the tithi before, so a vrat lands on the second', () {
    expect([for (final d in vratView(daysWith([7, 8, 8, 9]))) d.jainTithi], [7, 7, 8, 9]);
  });

  test('only the tithi identity changes: the sunrise and evening tithis, date and instants stay', () {
    final relabelled = vratView(daysWith([7, 8, 8, 9]))[1];
    expect(
      (relabelled.date, relabelled.sunriseTithi, relabelled.eveningTithi, relabelled.sunrise),
      (const CivilDate(2026, 8, 2), 99, 98, 2461254.5),
    );
  });

  test('a relabelled day takes the months of the day before when that day holds the tithi it now reads as', () {
    final days = daysWith([30, 1, 1, 2], months: [shravana, bhadrapada, bhadrapada, bhadrapada]);
    final relabelled = vratView(days)[1];
    expect((relabelled.jainTithi, relabelled.month, relabelled.purnimantaMonth), (30, shravana, shravana));
  });

  test('otherwise it keeps its own months', () {
    final days = daysWith([29, 1, 1, 2], months: [shravana, bhadrapada, bhadrapada, bhadrapada]);
    final relabelled = vratView(days)[1];
    expect((relabelled.jainTithi, relabelled.month), (30, bhadrapada));
  });

  group('which observances take the second day (plans/vrat-vriddhi-second-day.md)', () {
    for (final category in ['vrat', 'monthly_vrat', 'tap_vrat', 'parva_vrat', 'mahaparv_vrat']) {
      test('a $category does', () => expect(takesSecondDayOfVriddhi('some_vrat', category), isTrue));
    }

    // Kalyanaks keep the book-verified first day; parva tithis show on both days.
    for (final category in ['kalyanak', 'janam_kalyanak', 'parva', 'mahaparv', 'festival', 'jayanti', '']) {
      test('a $category does not', () => expect(takesSecondDayOfVriddhi('some_day', category), isFalse));
    }

    for (final id in [
      'karma_nirjara_vrat', 'kartika_nandishwar_ashtami', 'kartika_purnima_ashtahnika_purna',
      'phalguna_purnima_ashtahnika_purna', 'ravi_vrat', 'ravivara', 'kartika_shukla_panchami',
    ]) {
      test('$id keeps its own rule', () => expect(takesSecondDayOfVriddhi(id, 'mahaparv_vrat'), isFalse));
    }
  });

  test('the last day of the window has no following day to compare and stays', () {
    expect([for (final d in vratView(daysWith([7, 8, 8]))) d.jainTithi], [7, 7, 8]);
    expect(vratView(daysWith([8])).single.jainTithi, 8);
  });
}
