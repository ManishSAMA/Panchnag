// Family D (plans/mobile-phase5-festivals.md §3): vrats that run from a start
// day to an end day, each found in the Purnimanta fortnight the registry's
// Amanta month and paksha name. A vriddhi takes the first day, a kshaya the
// last day of the tithi before; a missing end makes a one-day span, a missing
// start no vrat. Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/fortnight.dart';
import 'package:test/test.dart';

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

List<(LunarMonth, int)> whole(LunarMonth month) => run(month, 1, 30);

/// Amanta Shravana and Bhadrapada: Purnimanta Bhadrapada Krishna 1 is
/// 2026-07-16, its Purnima 2026-08-14, Purnimanta Ashvin Krishna 14 2026-08-28.
List<(LunarMonth, int)> season() => [...whole(shravana), ...whole(bhadrapada)];

FestivalEntry entry(String ruleType) => FestivalEntry(
  id: 'registry_id',
  ruleType: ruleType,
  category: 'vrat',
  name: 'Registry name',
  nameHindi: 'नाम',
  profiles: const ['all'],
  jainMonth: 'Bhadrapada',
  paksha: 'Krishna',
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

List<FestivalOccurrence> resolve(String ruleType, List<FestivalDay> days, {int year = 2026}) =>
    fortnightRules[ruleType]!(entry(ruleType), days, year: year);

List<(String, String, String)> spans(String ruleType, List<FestivalDay> days, {int year = 2026}) =>
    [for (final o in resolve(ruleType, days, year: year)) (o.id, o.start.iso, o.end.iso)];

void main() {
  group('Bhadrapada Krishna 1: six vrats begin', () {
    test('two end on Bhadrapada Purnima, four on Ashvin Krishna 14, each with its own id and category', () {
      final o = resolve('BhadrapadaKrishnaEkamMultiVrat', days(season()));
      expect([for (final x in o) (x.id, x.occurrenceId, x.category, x.start.iso, x.end.iso)], [
        ('solah_karan_vrat_prarambh_2026', 'solah_karan_vrat_prarambh_2026', 'mahaparv_vrat', '2026-07-16', '2026-08-28'),
        ('shri_jin_mukhavlokan_vrat_prarambh_2026', 'shri_jin_mukhavlokan_vrat_prarambh_2026', 'vrat', '2026-07-16', '2026-08-28'),
        ('shrut_skandha_vrat_prarambh_2026', 'shrut_skandha_vrat_prarambh_2026', 'vrat', '2026-07-16', '2026-08-28'),
        ('mushti_vidhan_vrat_prarambh_2026', 'mushti_vidhan_vrat_prarambh_2026', 'vrat', '2026-07-16', '2026-08-14'),
        ('dhanda_kalash_vrat_prarambh_2026', 'dhanda_kalash_vrat_prarambh_2026', 'vrat', '2026-07-16', '2026-08-14'),
        ('megh_mala_vrat_prarambh_2026', 'megh_mala_vrat_prarambh_2026', 'vrat', '2026-07-16', '2026-08-28'),
      ]);
      expect(o.map((x) => (x.ruleId, x.name)).toSet(), {('registry_id', 'Registry name')});
    });

    // Python looks for the tithi before Ekam, "tithi 0", which never holds.
    test('a kshaya Krishna 1 gives no vrats at all', () {
      final readings = [...run(shravana, 1, 15), ...run(shravana, 17, 30), ...whole(bhadrapada)];
      expect(resolve('BhadrapadaKrishnaEkamMultiVrat', days(readings)), isEmpty);
    });

    test('a kshaya Purnima ends on the last Shukla 14', () {
      final readings = [...whole(shravana), ...run(bhadrapada, 1, 14), (bhadrapada, 14), ...run(bhadrapada, 16, 30)];
      expect(spans('BhadrapadaKrishnaEkamMultiVrat', days(readings))[3],
          ('mushti_vidhan_vrat_prarambh_2026', '2026-07-16', '2026-08-14'));
    });

    test('with neither end tithi every vrat is a one-day span', () {
      final o = spans('BhadrapadaKrishnaEkamMultiVrat', days(whole(shravana)));
      expect(o, hasLength(6));
      expect(o.every((x) => x.$2 == '2026-07-16' && x.$3 == '2026-07-16'), isTrue);
    });
  });

  group('Teen Chaubisi and Bhaya Haran', () {
    test('from Bhadrapada Krishna 3 and 4 to Ashvin Krishna 14, named by year', () {
      final d = days(season());
      expect([for (final o in resolve('TeenChaubisiVrat', d)) (o.id, o.occurrenceId, o.category, o.start.iso, o.end.iso)],
          [('teen_chaubisi_vrat_prarambh_2026', 'teen_chaubisi_vrat_prarambh_2026', 'vrat', '2026-07-18', '2026-08-28')]);
      expect(spans('BhayaHaranVrat', d), [('bhaya_haran_vrat_2026', '2026-07-19', '2026-08-28')]);
    });

    test('a vriddhi gives the first day', () {
      final readings = [...run(shravana, 1, 18), (shravana, 18), ...run(shravana, 19, 30), ...whole(bhadrapada)];
      expect(spans('TeenChaubisiVrat', days(readings)).single.$2, '2026-07-18');
    });

    test('a kshaya gives the last day of the tithi before', () {
      final noTritiya = [...run(shravana, 1, 17), (shravana, 17), ...run(shravana, 19, 30), ...whole(bhadrapada)];
      expect(spans('TeenChaubisiVrat', days(noTritiya)).single.$2, '2026-07-18');
      final noChaturthi = [...run(shravana, 1, 18), (shravana, 18), ...run(shravana, 20, 30), ...whole(bhadrapada)];
      expect(spans('BhayaHaranVrat', days(noChaturthi)).single.$2, '2026-07-19');
    });

    // Amanta Ashvin's Shukla half is Purnimanta Ashvin too; its Shukla 13 is not Krishna 13.
    test('a kshaya Krishna 14 ends on the last Krishna 13, not a later Shukla 13', () {
      final readings = [
        ...whole(shravana), ...run(bhadrapada, 1, 28), (bhadrapada, 28), (bhadrapada, 30), ...run(ashvina, 1, 15),
      ];
      expect(spans('BhayaHaranVrat', days(readings)).single.$3, '2026-08-28');
    });

    test('no start gives no vrat', () {
      expect(resolve('BhayaHaranVrat', days(whole(bhadrapada))), isEmpty);
    });
  });

  group('which days count', () {
    test('an Adhik Purnimanta month is skipped for the Nija one', () {
      final readings = [...whole(adhik(shravana)), ...season()];
      expect(spans('BhayaHaranVrat', days(readings)), [('bhaya_haran_vrat_2026', '2026-08-18', '2026-09-27')]);
    });

    test("only the given year's days count", () {
      expect(resolve('TeenChaubisiVrat', days(season()), year: 2027), isEmpty);
      final straddling = days(season(), start: const CivilDate(2026, 12, 1));
      expect(spans('TeenChaubisiVrat', straddling), [('teen_chaubisi_vrat_prarambh_2026', '2026-12-18', '2026-12-18')]);
    });
  });
}
