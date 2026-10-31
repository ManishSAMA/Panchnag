// The Shwetambar 50-day Paryushan count (Python `ShvetambaraParyushan50DayFestival`)
// and Labdhi Vidhan Vrat (Python `LabdhiVidhanVratFestival`), which ends on
// its Samvatsari. Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/paryushan.dart';
import 'package:test/test.dart';

const ashadha = LunarMonth(index: 3, isAdhika: false);
const shravana = LunarMonth(index: 4, isAdhika: false);
const bhadrapada = LunarMonth(index: 5, isAdhika: false);
const ashvina = LunarMonth(index: 6, isAdhika: false);

LunarMonth adhik(LunarMonth m) => LunarMonth(index: m.index, isAdhika: true);

/// One day per (Amanta month, Jain tithi) from [start]. A Krishna day's
/// Purnimanta month is the next one, as in a year without an Adhik month.
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

/// Ashadha Shukla 14 on 14 Jul 2026; Shravana's Amavasya (Purnimanta
/// Bhadrapada Krishna 15) on 29 Aug.
final List<(LunarMonth, int)> season = [
  ...run(ashadha, 1, 30),
  ...run(shravana, 1, 30),
  ...run(bhadrapada, 1, 30),
  ...run(ashvina, 1, 15),
];

FestivalEntry entry(String id, String ruleType, String category) => FestivalEntry(
  id: id,
  ruleType: ruleType,
  category: category,
  name: id,
  nameHindi: id,
  profiles: const ['all'],
  jainMonth: null,
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

final paryushanEntry = entry('shvetambara_paryushan_50_day', 'ShvetambaraParyushan50Day', 'mahaparv');
final labdhiEntry = entry('labdhi_vidhan_vrat', 'LabdhiVidhanVrat', 'vrat');

List<(String, String)> paryushan(List<FestivalDay> days, {int year = 2026}) =>
    [for (final o in paryushan50Day(paryushanEntry, days, year: year)) (o.id, o.start.iso)];

List<(String, String)> labdhi(List<FestivalDay> days, {int year = 2026}) =>
    [for (final o in labdhiVidhanVrat(labdhiEntry, days, year: year)) (o.id, o.start.iso)];

void main() {
  group('the 50-day Paryushan count', () {
    test('day 1 is Ashadha Shukla 14, Paryushan runs days 43-49 and Samvatsari is day 50', () {
      expect(paryushan(days(season)), [
        ('shvetambara_chaturmas_prarambh_2026', '2026-07-14'),
        for (var n = 1; n <= 7; n++) ('paryushan_parv_day_${n}_2026', '2026-08-${(24 + n).toString()}'),
        ('samvatsari_mahaparv_2026', '2026-09-01'),
      ]);
    });

    test('each day is a one-day mahaparv attributed to the registry entry', () {
      final o = paryushan50Day(paryushanEntry, days(season), year: 2026);
      expect(o.every((x) => x.occurrenceId == x.id && x.end == x.start), isTrue);
      expect(o.map((x) => (x.ruleId, x.category)).toSet(), {('shvetambara_paryushan_50_day', 'mahaparv')});
    });

    test('when Shukla 14 holds two days the count starts on the second', () {
      final readings = [...run(ashadha, 1, 14), (ashadha, 14), ...season.skip(14)];
      expect(paryushan(days(readings)).first, ('shvetambara_chaturmas_prarambh_2026', '2026-07-15'));
    });

    test('Adhik Ashadha and Ashadha Krishna 14 do not anchor it', () {
      final readings = [...run(adhik(ashadha), 1, 30), ...run(ashadha, 16, 30), ...season.skip(30)];
      expect(paryushan(days(readings)), isEmpty);
    });

    test('a kshaya Shukla 14 gives no count', () {
      final readings = [...run(ashadha, 1, 13), ...season.skip(14)];
      expect(paryushan(days(readings)), isEmpty);
    });

    test("only the given year's Ashadha counts", () {
      expect(paryushan(days(season), year: 2027), isEmpty);
    });
  });

  group('Labdhi Vidhan Vrat', () {
    test('starts on Purnimanta Bhadrapada Krishna Amavasya and ends on Samvatsari', () {
      expect(labdhi(days(season)), [
        ('labdhi_vidhan_vrat_prarambh_2026', '2026-08-29'),
        ('labdhi_vidhan_vrat_purna_2026', '2026-09-01'),
      ]);
      final o = labdhiVidhanVrat(labdhiEntry, days(season), year: 2026);
      expect(o.every((x) => x.occurrenceId == x.id && x.end == x.start && x.category == 'vrat'), isTrue);
    });

    test('a doubled Amavasya starts it on the first day', () {
      final readings = [...season.take(59), (shravana, 30), ...season.skip(59)];
      expect(labdhi(days(readings)).first, ('labdhi_vidhan_vrat_prarambh_2026', '2026-08-29'));
    });

    test('a kshaya Amavasya starts it on the last Krishna 14', () {
      final readings = [...season.take(59), (shravana, 29), ...season.skip(60)];
      expect(labdhi(days(readings)).first, ('labdhi_vidhan_vrat_prarambh_2026', '2026-08-29'));
    });

    test('with an Adhik Bhadrapada only its days are read', () {
      final readings = [
        ...season.take(60),
        ...run(adhik(shravana), 1, 30),
        ...season.skip(60),
      ];
      expect(labdhi(days(readings)).first, ('labdhi_vidhan_vrat_prarambh_2026', '2026-09-28'));
    });

    test("a Bhadrapada Amavasya of the year before is not the year's", () {
      final readings = [...run(shravana, 16, 30), ...season];
      expect(labdhi(days(readings, start: const CivilDate(2025, 12, 17))).first,
          ('labdhi_vidhan_vrat_prarambh_2026', '2026-03-01'));
    });

    test('no Amavasya or Krishna 14, or no Ashadha anchor, gives nothing', () {
      expect(labdhi(days([...season.take(57), ...season.skip(60)])), isEmpty);
      expect(labdhi(days([...run(ashadha, 1, 13), ...season.skip(14)])), isEmpty);
    });
  });
}
