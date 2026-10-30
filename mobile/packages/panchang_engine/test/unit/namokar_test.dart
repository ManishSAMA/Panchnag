// Namokar Mahamantra 35-Vrat (Python `Namokar35VratFestival`): 35 steps over
// 18 lunar months, one per syllable of the Namokar Mantra.
// Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/namokar.dart';
import 'package:test/test.dart';

const ashadha = LunarMonth(index: 3, isAdhika: false);
const pausha = LunarMonth(index: 9, isAdhika: false);
const agrahayana = LunarMonth(index: 8, isAdhika: false);

/// Consecutive days from [start] in one Amanta month, one per Jain day-start tithi.
List<FestivalDay> month(LunarMonth amanta, List<int> tithis, {CivilDate start = const CivilDate(2026, 7, 1)}) {
  var date = start;
  return [
    for (final (i, t) in tithis.indexed)
      FestivalDay(
        date: i == 0 ? date : (date = date.next()),
        sunrise: 2461222.5 + i,
        sunset: 2461223.0 + i,
        sunriseTithi: t,
        jainTithi: t,
        eveningTithi: t,
        month: amanta,
        purnimantaMonth: amanta,
      ),
  ];
}

const namokar = FestivalEntry(
  id: 'namokar_35_vrat',
  ruleType: 'Namokar35Vrat',
  category: 'mahaparv_vrat',
  name: 'Namokar 35 Vrat',
  nameHindi: 'णमोकार ३५ व्रत',
  profiles: ['all'],
  jainMonth: null,
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

Map<String, String> steps(List<FestivalDay> days, {int year = 2026}) =>
    {for (final o in namokar35Vrat(namokar, days, year: year)) o.id: o.start.iso};

void main() {
  test('step 1 is Ashadha Shukla Saptami, a one-day occurrence with an id of its own', () {
    final o = namokar35Vrat(namokar, month(ashadha, [5, 6, 7, 8]), year: 2026).single;
    expect((o.id, o.occurrenceId, o.ruleId, o.category, o.start.iso, o.end.iso),
        ('namokar_vrat_step_1_2026', 'namokar_vrat_step_1_2026', 'namokar_35_vrat', 'mahaparv_vrat', '2026-07-03', '2026-07-03'));
  });

  test('the steps of one month are its own paksha and tithi: Ashadha holds steps 25, 26 and 1', () {
    final days = month(ashadha, [for (var t = 1; t <= 30; t++) t]);
    expect(steps(days), {
      'namokar_vrat_step_1_2026': '2026-07-07',
      'namokar_vrat_step_25_2026': '2026-07-29',
      'namokar_vrat_step_26_2026': '2026-07-14',
    });
  });

  test('the last step is Agrahayana (Margashirsha) Krishna Navami', () {
    expect(steps(month(agrahayana, [23, 24, 25])), {'namokar_vrat_step_35_2026': '2026-07-02'});
  });

  test('a doubled tithi is observed on its first day', () {
    expect(steps(month(ashadha, [6, 7, 7, 8])), {'namokar_vrat_step_1_2026': '2026-07-02'});
  });

  test('a kshaya tithi falls back to the last day of the step\'s fallback tithi', () {
    expect(steps(month(ashadha, [5, 6, 6, 8])), {'namokar_vrat_step_1_2026': '2026-07-03'});
  });

  test('when a month repeats, only its Adhik days count', () {
    final days = [
      ...month(const LunarMonth(index: 3, isAdhika: true), [5, 6, 8]),
      ...month(ashadha, [6, 7, 8], start: const CivilDate(2026, 8, 1)),
    ];
    expect(steps(days), {'namokar_vrat_step_1_2026': '2026-07-02'});
  });

  test('a month of the same name at both ends of the year is read as one: its first match wins', () {
    final days = [
      ...month(pausha, [19, 20], start: const CivilDate(2026, 1, 1)),
      ...month(pausha, [19, 20], start: const CivilDate(2026, 12, 1)),
    ];
    expect(steps(days), {'namokar_vrat_step_12_2026': '2026-01-02'});
  });

  test('only days of the requested year count', () {
    expect(steps(month(ashadha, [6, 7, 8], start: const CivilDate(2025, 12, 30))), isEmpty);
  });
}
