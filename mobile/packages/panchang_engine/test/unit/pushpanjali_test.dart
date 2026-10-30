// Pushpanjali Vrat (Python `PushpanjaliVratFestival`): Shukla Panchami to
// Navami of Chaitra, Bhadrapada and Magha, one occurrence per civil day.
// Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/pushpanjali.dart';
import 'package:test/test.dart';

const chaitra = LunarMonth(index: 0, isAdhika: false);
const bhadrapada = LunarMonth(index: 5, isAdhika: false);
const magha = LunarMonth(index: 10, isAdhika: false);
const shravana = LunarMonth(index: 4, isAdhika: false);

/// Consecutive days from [start] in one Amanta month, one per Jain day-start tithi.
List<FestivalDay> month(LunarMonth amanta, List<int> tithis, {CivilDate start = const CivilDate(2026, 3, 1)}) {
  var date = start;
  return [
    for (final (i, t) in tithis.indexed)
      FestivalDay(
        date: i == 0 ? date : (date = date.next()),
        sunrise: 2461100.5 + i,
        sunset: 2461101.0 + i,
        sunriseTithi: t,
        jainTithi: t,
        eveningTithi: t,
        month: amanta,
        purnimantaMonth: amanta,
      ),
  ];
}

FestivalEntry pushpanjali({String? month}) => FestivalEntry(
  id: 'pushpanjali_vrat',
  ruleType: 'PushpanjaliVrat',
  category: 'vrat',
  name: 'Pushpanjali Vrat',
  nameHindi: 'पुष्पांजलि व्रत',
  profiles: const ['all'],
  jainMonth: month,
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

const fullShukla = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];

List<String> ids(List<FestivalDay> days, {String? jainMonth}) =>
    [for (final o in pushpanjaliVrat(pushpanjali(month: jainMonth), days, year: 2026)) o.id];

void main() {
  test('Shukla 5 to 9 gives one occurrence a day, named by season and date', () {
    final o = pushpanjaliVrat(pushpanjali(), month(chaitra, fullShukla), year: 2026);
    expect([for (final x in o) (x.id, x.occurrenceId, x.start.iso, x.end.iso, x.ruleId, x.category)], [
      for (var day = 3; day <= 7; day++)
        ('pushpanjali_vrat_spring_2026-03-0$day', 'pushpanjali_vrat_spring_2026-03-0$day', '2026-03-0$day',
            '2026-03-0$day', 'pushpanjali_vrat', 'vrat'),
    ]);
  });

  test('Bhadrapada is the monsoon season and Magha the winter one; other months hold none', () {
    expect(ids(month(bhadrapada, fullShukla)).first, 'pushpanjali_vrat_monsoon_2026-03-03');
    expect(ids(month(magha, fullShukla)).first, 'pushpanjali_vrat_winter_2026-03-03');
    expect(ids(month(shravana, fullShukla)), isEmpty);
  });

  test('a kshaya in Shukla 5-14 with no tithi doubled starts the vrat a day early, on Chaturthi', () {
    expect(ids(month(chaitra, [3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15])).first, 'pushpanjali_vrat_spring_2026-03-02');
  });

  // Only Shukla 5-14 decide whether the start moves, so a doubled Chaturthi
  // still allows it; the vrat then starts on the first of the two days.
  test('a doubled Chaturthi with a kshaya after it starts the vrat on its first day', () {
    expect(ids(month(chaitra, [3, 4, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15])).first, 'pushpanjali_vrat_spring_2026-03-02');
  });

  test('with no Chaturthi day either, the early start is the day before Panchami', () {
    expect(ids(month(chaitra, [3, 5, 6, 7, 8, 9, 10, 12, 13, 14])).first, 'pushpanjali_vrat_spring_2026-03-01');
  });

  test('a doubled tithi cancels the early start, kshaya or not', () {
    final days = month(chaitra, [3, 4, 5, 6, 7, 8, 9, 10, 11, 11, 13, 14, 15]);
    expect(ids(days).first, 'pushpanjali_vrat_spring_2026-03-03');
  });

  test('the span covers every civil day from its start to the last of Shukla 5-9', () {
    expect(ids(month(chaitra, [4, 5, 6, 7, 7, 8, 9, 10, 11, 12, 13, 14])),
        [for (var day = 2; day <= 7; day++) 'pushpanjali_vrat_spring_2026-03-0$day']);
  });

  test('when the month repeats, only its Adhik days count', () {
    final days = [
      ...month(const LunarMonth(index: 0, isAdhika: true), [4, 5, 6]),
      ...month(chaitra, fullShukla, start: const CivilDate(2026, 4, 1)),
    ];
    expect(ids(days), [for (var day = 1; day <= 3; day++) 'pushpanjali_vrat_spring_2026-03-0$day']);
  });

  test('a registry month narrows the vrat to that season, and a month outside the seasons holds none', () {
    final days = [...month(chaitra, fullShukla), ...month(magha, fullShukla, start: const CivilDate(2026, 4, 1))];
    expect(ids(days, jainMonth: 'Magha').first, 'pushpanjali_vrat_winter_2026-04-03');
    expect(ids(days, jainMonth: 'Magha'), hasLength(5));
    expect(ids(days, jainMonth: 'Shravana'), isEmpty);
  });
}
