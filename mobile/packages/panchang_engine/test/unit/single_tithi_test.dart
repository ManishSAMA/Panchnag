// The SingleTithi rule (Python `SingleTithiFestival.resolve`) on hand-built days.
// Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/single_tithi.dart';
import 'package:test/test.dart';

const chaitra = LunarMonth(index: 0, isAdhika: false);
const vaishakha = LunarMonth(index: 1, isAdhika: false);
const adhikVaishakha = LunarMonth(index: 1, isAdhika: true);

/// One reading per day from [start]: (sunrise tithi, Jain day-start tithi, evening tithi).
List<FestivalDay> days(
  List<(int, int, int)> tithis, {
  CivilDate start = const CivilDate(2026, 3, 1),
  LunarMonth purnimanta = chaitra,
  LunarMonth? amanta,
}) {
  var date = start;
  return [
    for (final (i, (sunrise, jain, evening)) in tithis.indexed)
      FestivalDay(
        date: i == 0 ? date : (date = date.next()),
        sunrise: 2461100.5 + i,
        sunset: 2461101.0 + i,
        sunriseTithi: sunrise,
        jainTithi: jain,
        eveningTithi: evening,
        month: amanta ?? purnimanta,
        purnimantaMonth: purnimanta,
        standardOffset: Duration.zero,
      ),
  ];
}

/// Each tithi held all day: at sunrise, the Jain day-start and sunset.
List<FestivalDay> plain(List<int> tithis, {CivilDate start = const CivilDate(2026, 3, 1), LunarMonth purnimanta = chaitra}) =>
    days([for (final t in tithis) (t, t, t)], start: start, purnimanta: purnimanta);

FestivalEntry entry({
  String category = 'kalyanak',
  String? month = 'Chaitra',
  String paksha = 'Shukla',
  int tithi = 13,
  DayRule dayRule = DayRule.udaya,
  String? vriddhiRule,
  bool originPullback = false,
}) => FestivalEntry(
  id: 'test_rule',
  ruleType: 'SingleTithi',
  category: category,
  name: 'Test',
  nameHindi: 'परीक्षण',
  profiles: const ['all'],
  jainMonth: month,
  paksha: paksha,
  tithi: tithi,
  dayRule: dayRule,
  vriddhiRule: vriddhiRule,
  originPullback: originPullback,
);

List<String> datesOf(FestivalEntry e, List<FestivalDay> d, {int year = 2026}) =>
    [for (final o in singleTithi(e, d, year: year)) o.start.iso];

void main() {
  test('an occurrence carries the rule id, an id:date occurrence id, one day and the registry names', () {
    final o = singleTithi(entry(), plain([12, 13, 14]), year: 2026).single;
    expect(
      (o.id, o.occurrenceId, o.ruleId, o.category, o.name, o.nameHindi, o.start, o.end, o.status),
      ('test_rule', 'test_rule:2026-03-02', 'test_rule', 'kalyanak', 'Test', 'परीक्षण',
          const CivilDate(2026, 3, 2), const CivilDate(2026, 3, 2), 'confirmed'),
    );
  });

  group('the target fortnight', () {
    test('a Shukla entry is read in the Purnimanta month of its name', () {
      expect(datesOf(entry(), plain([12, 13, 14], purnimanta: vaishakha)), isEmpty);
    });

    test('a Krishna entry (stored Amanta) is read in the next Purnimanta month', () {
      final e = entry(paksha: 'Krishna', tithi: 5);
      expect(datesOf(e, plain([19, 20, 21], purnimanta: vaishakha)), ['2026-03-02']);
      expect(datesOf(e, plain([19, 20, 21])), isEmpty);
    });

    test('an Adhik fortnight never holds the observance', () {
      expect(datesOf(entry(paksha: 'Krishna', tithi: 5), plain([19, 20, 21], purnimanta: adhikVaishakha)), isEmpty);
    });

    test('registry spellings of the month are understood (Margashirsha is Agrahayana)', () {
      const agrahayana = LunarMonth(index: 8, isAdhika: false);
      expect(datesOf(entry(month: 'Margashirsha'), plain([12, 13, 14], purnimanta: agrahayana)), ['2026-03-02']);
      expect(datesOf(entry(month: 'Kartik'), plain([12, 13, 14], purnimanta: const LunarMonth(index: 7, isAdhika: false))),
          ['2026-03-02']);
    });

    test('only days of the requested year count', () {
      final d = plain([12, 13, 16], start: const CivilDate(2025, 12, 30));
      expect(datesOf(entry(), d, year: 2026), isEmpty);
      expect(datesOf(entry(), d, year: 2025), ['2025-12-31']);
    });
  });

  group('a Kalyanak', () {
    test('holding the Jain day-start on two days is fixed to the first, not the sunrise day', () {
      // Sunrise tithi 13 only on the 3rd, but 13 holds both Jain day-starts.
      expect(datesOf(entry(), days([(12, 12, 12), (12, 13, 13), (13, 13, 14), (14, 14, 14)])), ['2026-03-02']);
    });

    test('a weak sunrise day moves back to a previous day still building toward it (6-ghati pull-back)', () {
      // 3rd: 13 at sunrise but 14 by the Jain day-start; 2nd: strong 12.
      expect(datesOf(entry(), days([(11, 11, 11), (12, 12, 13), (13, 14, 14), (14, 14, 15)])), ['2026-03-02']);
    });

    test('a weak sunrise day stays when the day before is weak too', () {
      expect(datesOf(entry(), days([(11, 11, 12), (12, 13, 13), (13, 14, 14), (14, 15, 15)])), ['2026-03-03']);
    });

    test('a weak Purnima moves back when the day before already reached it at its Jain day-start', () {
      final e = entry(tithi: 15);
      expect(datesOf(e, days([(13, 14, 14), (14, 15, 15), (15, 16, 16), (16, 16, 17)])), ['2026-03-02']);
    });

    test('the same shape for an ordinary tithi does not move back (Mahavir Janma Kalyanak 2026)', () {
      expect(datesOf(entry(), days([(11, 12, 12), (12, 13, 13), (13, 14, 14), (14, 15, 15)])), ['2026-03-03']);
    });

    test('a kshaya tithi falls back to the last day of the tithi before it', () {
      expect(datesOf(entry(), plain([11, 12, 12, 14, 15])), ['2026-03-03']);
    });

    test('a kshaya Pratipada falls on the eve of the first later tithi', () {
      expect(datesOf(entry(tithi: 1), plain([2, 3, 4])), ['2026-02-28']);
    });

    test('with origin pull-back, moves to the day before when the tithi began by its sunset', () {
      final d = days([(11, 11, 11), (12, 12, 13), (13, 13, 13), (14, 14, 14)]);
      expect(datesOf(entry(originPullback: true), d), ['2026-03-02']);
      expect(datesOf(entry(), d), ['2026-03-03']);
    });
  });

  group('a festival', () {
    test('a second_day vriddhi rule takes the second sunrise day', () {
      final d = plain([3, 4, 4, 5]);
      expect(datesOf(entry(category: 'festival', tithi: 4, vriddhiRule: 'second_day'), d), ['2026-03-03']);
      expect(datesOf(entry(category: 'festival', tithi: 4), d), ['2026-03-02']);
    });

    test('a pradosh rule takes the first day the tithi holds at sunset, whatever the sunrise paksha', () {
      final e = entry(category: 'festival', paksha: 'Krishna', tithi: 15, dayRule: DayRule.pradosh);
      final d = days([(28, 28, 29), (29, 29, 30), (30, 30, 1)], purnimanta: vaishakha);
      expect(datesOf(e, d), ['2026-03-02']);
    });
  });

  group('a parva tithi', () {
    test('shows on both days of a Jain day-start vriddhi', () {
      expect(datesOf(entry(category: 'parva', tithi: 8), days([(7, 7, 8), (7, 8, 8), (8, 8, 9), (9, 9, 9)])),
          ['2026-03-02', '2026-03-03']);
    });

    test('without a month, recurs once per Amanta month', () {
      final e = entry(category: 'parva', month: null, tithi: 14);
      final d = [
        ...plain([13, 14, 15]),
        ...days([(13, 13, 13), (14, 14, 14)], start: const CivilDate(2026, 4, 1), purnimanta: vaishakha),
      ];
      expect(datesOf(e, d), ['2026-03-02', '2026-04-02']);
    });
  });
}
