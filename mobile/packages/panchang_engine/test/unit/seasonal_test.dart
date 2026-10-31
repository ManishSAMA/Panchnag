// Step 11 (plans/mobile-phase5-festivals.md §5): Karma Nirjara on Shukla 14 of
// each Chaturmas month, and Ashtahnika from Shukla 8 to Purnima in Ashadha,
// Kartika and Phalguna. Both read the year's days of an Amanta month, only the
// Adhik ones when it repeats, and keep their own vriddhi rule. Tithis are 1-30:
// Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/seasonal.dart';
import 'package:test/test.dart';

const ashadha = LunarMonth(index: 3, isAdhika: false);
const shravana = LunarMonth(index: 4, isAdhika: false);
const bhadrapada = LunarMonth(index: 5, isAdhika: false);
const ashvina = LunarMonth(index: 6, isAdhika: false);
const kartika = LunarMonth(index: 7, isAdhika: false);
const phalguna = LunarMonth(index: 11, isAdhika: false);

LunarMonth adhik(LunarMonth m) => LunarMonth(index: m.index, isAdhika: true);

/// One day per (Amanta month, Jain tithi) from [start].
List<FestivalDay> days(List<(LunarMonth, int)> readings, {CivilDate start = const CivilDate(2026, 7, 1)}) => [
  for (final (i, (month, tithi)) in readings.indexed)
    FestivalDay(
      date: start.plusDays(i),
      sunrise: 2461222.5 + i,
      sunset: 2461223.0 + i,
      sunriseTithi: tithi,
      jainTithi: tithi,
      eveningTithi: tithi,
      month: month,
      purnimantaMonth: tithi <= 15 ? month : LunarMonth(index: (month.index + 1) % 12, isAdhika: month.isAdhika),
      standardOffset: Duration.zero,
    ),
];

List<(LunarMonth, int)> run(LunarMonth month, int from, int to) => [for (var t = from; t <= to; t++) (month, t)];

List<(LunarMonth, int)> whole(LunarMonth month) => run(month, 1, 30);

FestivalEntry entry(String ruleType, String id, String category) => FestivalEntry(
  id: id,
  ruleType: ruleType,
  category: category,
  name: 'Registry name',
  nameHindi: 'नाम',
  profiles: const ['all'],
  jainMonth: null,
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

List<FestivalOccurrence> karmaNirjara(List<FestivalDay> days, {int year = 2026}) =>
    seasonalRules['KarmaNirjaraVrat']!(entry('KarmaNirjaraVrat', 'karma_nirjara_vrat', 'parva_vrat'), days, year: year);

List<FestivalOccurrence> ashtahnika(List<FestivalDay> days, {int year = 2026}) =>
    seasonalRules['AshtahnikaVrat']!(entry('AshtahnikaVrat', 'ashtahnika_mahaparv', 'mahaparv'), days, year: year);

List<(String, String, String)> spans(List<FestivalOccurrence> list) =>
    [for (final o in list) (o.id, o.start.iso, o.end.iso)];

void main() {
  group('Karma Nirjara', () {
    test('Shukla 14, named by month and year, its occurrence by date', () {
      final o = karmaNirjara(days(whole(ashadha)));
      expect([for (final x in o) (x.id, x.occurrenceId, x.ruleId, x.category, x.start.iso, x.end.iso)], [
        ('karma_nirjara_vrat_ashadha_2026', 'karma_nirjara_vrat_2026-07-14', 'karma_nirjara_vrat', 'parva_vrat',
            '2026-07-14', '2026-07-14'),
      ]);
    });

    test('in each of Ashadha, Shravana, Bhadrapada and Ashwin, and no other month', () {
      final readings = [...whole(ashadha), ...whole(shravana), ...whole(bhadrapada), ...whole(ashvina), ...whole(kartika)];
      expect(karmaNirjara(days(readings)).map((o) => o.id), [
        'karma_nirjara_vrat_ashadha_2026',
        'karma_nirjara_vrat_shravana_2026',
        'karma_nirjara_vrat_bhadrapada_2026',
        'karma_nirjara_vrat_ashwin_2026',
      ]);
    });

    test('a vriddhi keeps the first day', () {
      final readings = [...run(ashadha, 1, 14), (ashadha, 14), ...run(ashadha, 15, 30)];
      expect(spans(karmaNirjara(days(readings))).single.$2, '2026-07-14');
    });

    test('a kshaya gives the last Shukla 13; with neither there is none', () {
      final readings = [...run(ashadha, 1, 13), (ashadha, 13), ...run(ashadha, 15, 30)];
      expect(spans(karmaNirjara(days(readings))).single.$2, '2026-07-14');
      expect(karmaNirjara(days([...run(ashadha, 1, 12), ...run(ashadha, 15, 30)])), isEmpty);
    });

    test('when the month repeats only its Adhik days count, and the id says so', () {
      final readings = [...whole(adhik(shravana)), ...whole(shravana)];
      expect(spans(karmaNirjara(days(readings))), [('karma_nirjara_vrat_adhik_shravana_2026', '2026-07-14', '2026-07-14')]);
    });

    test("only the given year's days count", () {
      expect(karmaNirjara(days(whole(ashadha)), year: 2027), isEmpty);
    });
  });

  group('Ashtahnika', () {
    test('Shukla 8 to Purnima, named by season and year', () {
      final o = ashtahnika(days(whole(kartika)));
      expect([for (final x in o) (x.id, x.occurrenceId, x.ruleId, x.category, x.start.iso, x.end.iso)], [
        ('ashtahnika_kartika_2026', 'ashtahnika_kartika_2026', 'ashtahnika_mahaparv', 'mahaparv', '2026-07-08', '2026-07-15'),
      ]);
    });

    test('in each of Ashadha, Kartika and Phalguna, and no other month', () {
      final readings = [...whole(ashadha), ...whole(shravana), ...whole(kartika), ...whole(phalguna)];
      expect(ashtahnika(days(readings)).map((o) => o.id),
          ['ashtahnika_ashadha_2026', 'ashtahnika_kartika_2026', 'ashtahnika_phalguna_2026']);
    });

    test('a doubled Ashtami starts on the first day, a doubled Purnima ends on the second', () {
      final readings = [...run(kartika, 1, 8), (kartika, 8), ...run(kartika, 9, 15), (kartika, 15), ...run(kartika, 16, 30)];
      expect(spans(ashtahnika(days(readings))), [('ashtahnika_kartika_2026', '2026-07-08', '2026-07-17')]);
    });

    test('a kshaya Ashtami starts on the first Saptami', () {
      final readings = [...run(kartika, 1, 7), (kartika, 7), ...run(kartika, 9, 30)];
      expect(spans(ashtahnika(days(readings))).single.$2, '2026-07-07');
    });

    test('with neither Ashtami nor Saptami it starts the day before the first day of Shukla 8-15', () {
      final readings = [...run(kartika, 1, 6), ...run(kartika, 9, 30)];
      expect(spans(ashtahnika(days(readings))).single.$2, '2026-07-06');
    });

    test('a kshaya Purnima ends on the last day of Shukla 8-14', () {
      final readings = [...run(kartika, 1, 14), (kartika, 14), ...run(kartika, 16, 30)];
      expect(spans(ashtahnika(days(readings))).single.$3, '2026-07-15');
    });

    test('Purnima alone of Shukla 8-15 still makes a span, from the day before', () {
      final readings = [...run(kartika, 1, 6), (kartika, 15), ...run(kartika, 16, 30)];
      expect(spans(ashtahnika(days(readings))), [('ashtahnika_kartika_2026', '2026-07-06', '2026-07-07')]);
    });

    test('a month without any of Shukla 8-15 gives none', () {
      expect(ashtahnika(days([...run(kartika, 1, 7), ...run(kartika, 16, 30)])), isEmpty);
    });

    test('when the month repeats only its Adhik days count', () {
      final readings = [...whole(kartika), ...whole(adhik(kartika))];
      expect(spans(ashtahnika(days(readings))), [('ashtahnika_kartika_2026', '2026-08-07', '2026-08-14')]);
    });

    test("only the given year's days count", () {
      expect(ashtahnika(days(whole(kartika)), year: 2027), isEmpty);
    });
  });
}
