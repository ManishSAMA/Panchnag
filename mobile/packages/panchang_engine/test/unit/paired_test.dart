// Family C (plans/mobile-phase5-festivals.md §3): a Prarambh event and a Purna
// event, each on its own anchor day. Months are Amanta by name unless a test
// says Purnimanta; when a month repeats only its Adhik days count (as in
// family B). Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/paired.dart';
import 'package:test/test.dart';

const chaitra = LunarMonth(index: 0, isAdhika: false);
const vaishakha = LunarMonth(index: 1, isAdhika: false);
const jyeshtha = LunarMonth(index: 2, isAdhika: false);
const ashadha = LunarMonth(index: 3, isAdhika: false);
const shravana = LunarMonth(index: 4, isAdhika: false);
const bhadrapada = LunarMonth(index: 5, isAdhika: false);
const ashvina = LunarMonth(index: 6, isAdhika: false);
const kartika = LunarMonth(index: 7, isAdhika: false);
const pausha = LunarMonth(index: 9, isAdhika: false);
const magha = LunarMonth(index: 10, isAdhika: false);
const phalguna = LunarMonth(index: 11, isAdhika: false);

/// One day per (Amanta month, Jain tithi) from 1 Jul 2026. A Krishna day's
/// Purnimanta month is the next one, as in a year without an Adhik month.
List<FestivalDay> days(List<(LunarMonth, int)> readings) => [
  for (final (i, (month, tithi)) in readings.indexed)
    FestivalDay(
      date: const CivilDate(2026, 7, 1).plusDays(i),
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

/// [readings] with the tithis in [tithis] (of [month]) said twice.
List<(LunarMonth, int)> doubling(List<(LunarMonth, int)> readings, LunarMonth month, Set<int> tithis) => [
  for (final r in readings) ...[r, if (r.$1 == month && tithis.contains(r.$2)) r],
];

FestivalEntry entry(String ruleType) => FestivalEntry(
  id: 'registry_id',
  ruleType: ruleType,
  category: 'vrat',
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

List<FestivalOccurrence> resolve(String ruleType, List<(LunarMonth, int)> readings) =>
    pairedRules[ruleType]!(entry(ruleType), days(readings), year: 2026);

List<(String, String)> placed(String ruleType, List<(LunarMonth, int)> readings) =>
    [for (final o in resolve(ruleType, readings)) (o.id, o.start.iso)];

void main() {
  test('each event is a one-day occurrence with its own id and category, attributed to the entry', () {
    final o = resolve('RatnatrayaSankatHaranVrat', whole(bhadrapada));
    expect([for (final x in o) (x.id, x.occurrenceId, x.category, x.start.iso, x.end.iso)], [
      ('ratnatraya_vrat_prarambh_2026', 'ratnatraya_vrat_prarambh_2026', 'mahaparv_vrat', '2026-07-13', '2026-07-13'),
      ('sankat_haran_vrat_prarambh_2026', 'sankat_haran_vrat_prarambh_2026', 'vrat', '2026-07-13', '2026-07-13'),
      ('ratnatraya_vrat_purna_2026', 'ratnatraya_vrat_purna_2026', 'mahaparv_vrat', '2026-07-15', '2026-07-15'),
      ('sankat_haran_vrat_purna_2026', 'sankat_haran_vrat_purna_2026', 'vrat', '2026-07-15', '2026-07-15'),
    ]);
    expect(o.map((x) => (x.ruleId, x.name)).toSet(), {('registry_id', 'Registry name')});
  });

  group('Chaitra and Magha Labdhi Vidhan', () {
    // Purnimanta Chaitra Krishna is Amanta Phalguna's Krishna half: Amavasya on day 29.
    test('from the first Purnimanta Krishna Amavasya to the last Shukla 4', () {
      expect(placed('ChaitraLabdhiVidhan', doubling([...whole(phalguna), ...whole(chaitra)], chaitra, {4})), [
        ('labdhi_vidhan_start_chaitra_2026', '2026-07-30'),
        ('labdhi_vidhan_purna_chaitra_2026', '2026-08-04'),
      ]);
      expect(resolve('MaghaLabdhiVidhan', [...whole(pausha), ...whole(magha)]).map((o) => (o.id, o.category)), [
        ('labdhi_vidhan_start_magha_2026', 'mahaparv_vrat'),
        ('labdhi_vidhan_purna_magha_2026', 'mahaparv_vrat'),
      ]);
    });

    test('a doubled Amavasya gives the first day; kshayas give the last Krishna 14 and the last Shukla 3', () {
      expect(placed('ChaitraLabdhiVidhan', doubling([...whole(phalguna), ...whole(chaitra)], phalguna, {30})).first.$2,
          '2026-07-30');
      final kshaya = [...run(phalguna, 1, 28), (phalguna, 29), (phalguna, 29), ...run(chaitra, 1, 3), ...run(chaitra, 5, 30)];
      expect(placed('ChaitraLabdhiVidhan', kshaya), [
        ('labdhi_vidhan_start_chaitra_2026', '2026-07-30'),
        ('labdhi_vidhan_purna_chaitra_2026', '2026-08-02'),
      ]);
    });

    test('no end gives nothing', () {
      expect(placed('ChaitraLabdhiVidhan', [...whole(phalguna), ...run(chaitra, 5, 30)]), isEmpty);
    });
  });

  group('Sapta Rishi Vrat', () {
    test('Ashadha Purnima to the last Shravana Krishna 5', () {
      final readings = doubling(doubling([...whole(ashadha), ...whole(shravana)], shravana, {20}), ashadha, {15});
      expect(placed('SaptaRishiVrat', readings), [
        ('sapta_rishi_vrat_prarambh_2026', '2026-07-15'),
        ('sapta_rishi_vrat_nishthapan_2026', '2026-08-21'),
      ]);
    });

    test('kshayas give the last Shukla 14 and the last Krishna 4; no Shravana gives nothing', () {
      final kshaya = [...run(ashadha, 1, 14), (ashadha, 14), ...run(ashadha, 16, 30), ...run(shravana, 1, 19), ...run(shravana, 21, 30)];
      expect(placed('SaptaRishiVrat', kshaya), [
        ('sapta_rishi_vrat_prarambh_2026', '2026-07-15'),
        ('sapta_rishi_vrat_nishthapan_2026', '2026-08-18'),
      ]);
      expect(placed('SaptaRishiVrat', whole(ashadha)), isEmpty);
    });
  });

  group('Sapta Paramsthan Vrat', () {
    test('the first Shravana Shukla 1 to the last Shukla 7', () {
      expect(placed('SaptaParamsthanVrat', doubling(whole(shravana), shravana, {1, 7})), [
        ('sapta_paramsthan_vrat_prarambh_2026', '2026-07-01'),
        ('sapta_paramsthan_vrat_purna_2026', '2026-07-09'),
      ]);
    });

    test("a kshaya Shukla 1 gives the month's last Amavasya, else the day before Shukla 2", () {
      expect(placed('SaptaParamsthanVrat', doubling(run(shravana, 2, 30), shravana, {30})).first,
          ('sapta_paramsthan_vrat_prarambh_2026', '2026-07-30'));
      expect(placed('SaptaParamsthanVrat', [(ashadha, 30), ...run(shravana, 2, 29)]).first,
          ('sapta_paramsthan_vrat_prarambh_2026', '2026-07-01'));
      expect(placed('SaptaParamsthanVrat', run(shravana, 2, 29)).first,
          ('sapta_paramsthan_vrat_prarambh_2026', '2026-07-01'), reason: 'no day before the first one read');
    });

    test('a kshaya Shukla 7 gives the last Shukla 6', () {
      expect(placed('SaptaParamsthanVrat', [...run(shravana, 1, 6), (shravana, 6), ...run(shravana, 8, 30)]).last,
          ('sapta_paramsthan_vrat_purna_2026', '2026-07-07'));
    });
  });

  group('Rakshabandhan Vrat', () {
    test('Shravana Shukla 13 to the last Purnima', () {
      expect(placed('RakshabandhanVrat', doubling(whole(shravana), shravana, {13, 15})), [
        ('rakshabandhan_vrat_prarambh_2026', '2026-07-13'),
        ('rakshabandhan_vrat_purna_2026', '2026-07-17'),
      ]);
      expect(resolve('RakshabandhanVrat', whole(shravana)).map((o) => o.category), ['vrat', 'mahaparv']);
    });

    test('a kshaya anywhere in Shukla 13-15 starts it on Shukla 12', () {
      final kshaya14 = [...run(shravana, 1, 13), ...run(shravana, 15, 30)];
      expect(placed('RakshabandhanVrat', kshaya14), [
        ('rakshabandhan_vrat_prarambh_2026', '2026-07-12'),
        ('rakshabandhan_vrat_purna_2026', '2026-07-14'),
      ]);
    });

    test('with Shukla 12 also gone, Shukla 13; with 13 gone too, the day before the first of 14 and 15', () {
      expect(placed('RakshabandhanVrat', [...run(shravana, 1, 11), ...run(shravana, 13, 13), ...run(shravana, 15, 30)]).first.$2,
          '2026-07-12');
      expect(placed('RakshabandhanVrat', [...run(shravana, 1, 11), ...run(shravana, 14, 30)]).first.$2, '2026-07-11');
    });

    test('a kshaya Purnima ends it on the last Shukla 14', () {
      expect(placed('RakshabandhanVrat', doubling([...run(shravana, 1, 14), ...run(shravana, 16, 30)], shravana, {14})), [
        ('rakshabandhan_vrat_prarambh_2026', '2026-07-12'),
        ('rakshabandhan_vrat_purna_2026', '2026-07-15'),
      ]);
    });
  });

  group('Akshaya Nidhi, Anant Chaturdashi', () {
    test('Akshaya Nidhi: the first Shravana Shukla 10 to the last Bhadrapada Krishna 10', () {
      final readings = doubling(doubling([...whole(shravana), ...whole(bhadrapada)], shravana, {10}), bhadrapada, {25});
      expect(placed('AkshayaNidhiVrat', readings), [
        ('akshaya_nidhi_vrat_prarambh_2026', '2026-07-10'),
        ('akshaya_nidhi_vrat_purna_2026', '2026-08-26'),
      ]);
    });

    test('Akshaya Nidhi kshayas give the last Shukla 9 and the last Krishna 9', () {
      final readings = [
        ...run(shravana, 1, 9), (shravana, 9), ...run(shravana, 11, 30),
        ...run(bhadrapada, 1, 24), ...run(bhadrapada, 26, 30),
      ];
      expect(placed('AkshayaNidhiVrat', readings), [
        ('akshaya_nidhi_vrat_prarambh_2026', '2026-07-10'),
        ('akshaya_nidhi_vrat_purna_2026', '2026-08-23'),
      ]);
    });

    test('Anant: the first Bhadrapada Shukla 11 to the last Shukla 14, or Shukla 10 and 13 on kshayas', () {
      expect(placed('AnantChaturdashiVrat', doubling(whole(bhadrapada), bhadrapada, {11, 14})), [
        ('anant_vrat_prarambh_2026', '2026-07-11'),
        ('anant_chaturdashi_purna_2026', '2026-07-16'),
      ]);
      expect(placed('AnantChaturdashiVrat', [...run(bhadrapada, 1, 10), ...run(bhadrapada, 12, 13), ...run(bhadrapada, 15, 30)]), [
        ('anant_vrat_prarambh_2026', '2026-07-10'),
        ('anant_chaturdashi_purna_2026', '2026-07-12'),
      ]);
    });

    test('Ratnatraya Sankat Haran kshayas give the last Shukla 12 and the last Shukla 14', () {
      final readings = doubling([...run(bhadrapada, 1, 12), (bhadrapada, 14), ...run(bhadrapada, 16, 30)], bhadrapada, {12, 14});
      expect(placed('RatnatrayaSankatHaranVrat', readings).map((p) => p.$2).toSet(), {'2026-07-13', '2026-07-15'});
      expect(placed('RatnatrayaSankatHaranVrat', doubling(whole(bhadrapada), bhadrapada, {13})).first.$2, '2026-07-13',
          reason: 'a doubled Shukla 13 starts on its first day');
    });
  });

  group('Shraddha Vrat', () {
    test('the first Ashwin Shukla 1 to the last Kartika Krishna 1', () {
      expect(placed('ShraddhaVrat', doubling([...whole(ashvina), ...whole(kartika)], kartika, {16})), [
        ('shraddha_vrat_prarambh_2026', '2026-07-01'),
        ('shraddha_vrat_purna_2026', '2026-08-16'),
      ]);
    });

    test("kshayas give the last Ashwin Amavasya and, outside Kartika, the last Ashwin Purnima", () {
      expect(placed('ShraddhaVrat', doubling(run(ashvina, 2, 30), ashvina, {30})), [
        ('shraddha_vrat_prarambh_2026', '2026-07-30'),
        ('shraddha_vrat_purna_2026', '2026-07-14'),
      ]);
    });
  });

  group('Navapad Oli', () {
    test('the first Shukla 7 to the last Purnima, in Chaitra and in Ashwin, each season on its own', () {
      expect(placed('NavapadOliVrat', doubling([...whole(chaitra), ...whole(ashvina)], chaitra, {7, 15})), [
        ('navapad_oli_vrat_prarambh_chaitra_2026', '2026-07-07'),
        ('navapad_oli_vrat_purna_chaitra_2026', '2026-07-17'),
        ('navapad_oli_vrat_prarambh_ashwin_2026', '2026-08-08'),
        ('navapad_oli_vrat_purna_ashwin_2026', '2026-08-16'),
      ]);
      expect(placed('NavapadOliVrat', [...run(chaitra, 1, 5), ...run(chaitra, 8, 13), ...whole(ashvina)]).map((p) => p.$1),
          ['navapad_oli_vrat_prarambh_ashwin_2026', 'navapad_oli_vrat_purna_ashwin_2026']);
    });

    test('kshayas give the last Shukla 6 and the last Shukla 14', () {
      expect(placed('NavapadOliVrat', doubling([...run(chaitra, 1, 6), ...run(chaitra, 8, 14), ...run(chaitra, 16, 30)], chaitra, {6, 14})), [
        ('navapad_oli_vrat_prarambh_chaitra_2026', '2026-07-07'),
        ('navapad_oli_vrat_purna_chaitra_2026', '2026-07-15'),
      ]);
    });
  });

  group('Pratham Jeth Jinvani (monthly vrat)', () {
    test("Jyeshtha Krishna 1 and Shukla 15, named after the entry, each on its own", () {
      final o = resolve('MonthlyVrat', doubling(whole(jyeshtha), jyeshtha, {15, 16}));
      expect([for (final x in o) (x.id, x.category, x.start.iso)], [
        ('registry_id_start_2026', 'monthly_vrat', '2026-07-17'),
        ('registry_id_end_2026', 'monthly_vrat', '2026-07-16'),
      ]);
      expect(placed('MonthlyVrat', [...run(jyeshtha, 1, 13), ...run(jyeshtha, 16, 30)]).map((p) => p.$1), ['registry_id_start_2026']);
    });

    test("a kshaya Krishna 1 gives the day before the month's first day; a kshaya Purnima the last Shukla 14", () {
      expect(placed('MonthlyVrat', [(vaishakha, 30), ...run(jyeshtha, 1, 14), ...run(jyeshtha, 17, 30)]), [
        ('registry_id_start_2026', '2026-07-01'),
        ('registry_id_end_2026', '2026-07-15'),
      ]);
    });
  });
}
