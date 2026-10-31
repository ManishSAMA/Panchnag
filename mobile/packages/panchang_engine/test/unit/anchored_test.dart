// Family B (plans/mobile-phase5-festivals.md §3): one anchor day in a named
// month, carrying 1-3 events with fixed ids. The month filter keeps the year's
// days of that month, only the Adhik ones when it repeats; a vriddhi takes the
// first or second day, a kshaya the last day of a fallback tithi. Python names
// the month from the Amanta reading in some rules and the Purnimanta one in
// others. Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/anchored.dart';
import 'package:test/test.dart';

const shravana = LunarMonth(index: 4, isAdhika: false);
const ashadha = LunarMonth(index: 3, isAdhika: false);
const vaishakha = LunarMonth(index: 1, isAdhika: false);
const ashvina = LunarMonth(index: 6, isAdhika: false);
const kartika = LunarMonth(index: 7, isAdhika: false);
const margashirsha = LunarMonth(index: 8, isAdhika: false);

LunarMonth adhik(LunarMonth m) => LunarMonth(index: m.index, isAdhika: true);

/// One day per (Amanta month, Jain tithi) from [start]; [evening] overrides the
/// sunset tithi of a day by its index. A Krishna day's Purnimanta month is the
/// next one, as in a year without an Adhik month.
List<FestivalDay> days(
  List<(LunarMonth, int)> readings, {
  CivilDate start = const CivilDate(2026, 7, 1),
  Map<int, int> evening = const {},
}) => [
  for (final (i, (month, tithi)) in readings.indexed)
    FestivalDay(
      date: start.plusDays(i),
      sunrise: 2461222.5 + i,
      sunset: 2461223.0 + i,
      sunriseTithi: tithi,
      jainTithi: tithi,
      eveningTithi: evening[i] ?? tithi,
      month: month,
      purnimantaMonth: tithi <= 15 ? month : LunarMonth(index: (month.index + 1) % 12, isAdhika: month.isAdhika),
      standardOffset: Duration.zero,
    ),
];

List<(LunarMonth, int)> run(LunarMonth month, int from, int to) => [for (var t = from; t <= to; t++) (month, t)];

/// A whole Amanta month, Shukla 1 to Amavasya.
List<(LunarMonth, int)> whole(LunarMonth month) => run(month, 1, 30);

FestivalEntry entry(String ruleType, {String id = 'registry_id', String category = 'mahaparv'}) => FestivalEntry(
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

List<FestivalOccurrence> resolve(String ruleType, List<FestivalDay> days, {int year = 2026, String id = 'registry_id'}) =>
    anchoredRules[ruleType]!(entry(ruleType, id: id), days, year: year);

List<(String, String)> placed(String ruleType, List<FestivalDay> days, {int year = 2026}) =>
    [for (final o in resolve(ruleType, days, year: year)) (o.id, o.start.iso)];

void main() {
  group('one anchor day with fixed events', () {
    test('every event sits on the anchor day, with its own id and category, attributed to the entry', () {
      final o = resolve('ShravanaPurnimaRakshabandhan', days(whole(shravana)));
      expect([for (final x in o) (x.id, x.occurrenceId, x.category, x.start.iso, x.end.iso)], [
        ('rakshabandhan_700_muni_raksha_divas_2026', 'rakshabandhan_700_muni_raksha_divas_2026', 'mahaparv', '2026-07-15', '2026-07-15'),
        ('muni_vishnukumar_akampanacharya_pujan_2026', 'muni_vishnukumar_akampanacharya_pujan_2026', 'poojan', '2026-07-15', '2026-07-15'),
        ('sorana_pujan_2026', 'sorana_pujan_2026', 'parv_vidhi', '2026-07-15', '2026-07-15'),
      ]);
      expect(o.map((x) => (x.ruleId, x.name)).toSet(), {('registry_id', 'Registry name')});
    });

    test('a vriddhi gives the first day for most rules and the second for the Purnima ones', () {
      final doubled = days([...run(kartika, 1, 2), (kartika, 2), ...run(kartika, 3, 15), (kartika, 15), ...run(kartika, 16, 30)]);
      expect(placed('BhaiDooj', doubled), [('bhai_dooj_2026', '2026-07-02')]);
      expect(placed('KartikaPurnimaAshtahnikaPurna', doubled).first, ('kartika_ashtahnika_purna_2026', '2026-07-17'));
    });

    test('a kshaya gives the last day of the fallback tithi', () {
      final readings = [(kartika, 1), (kartika, 1), ...run(kartika, 3, 30)];
      expect(placed('BhaiDooj', days(readings)), [('bhai_dooj_2026', '2026-07-02')]);
    });

    test('the fallback may sit in the other paksha: a kshaya Kartika Shukla 1 goes back to Amavasya', () {
      final readings = [...whole(ashvina), (ashvina, 30), ...run(kartika, 2, 15)];
      expect(placed('KartikaShuklaEkamNewYear', days(readings)).first, ('jain_new_year_2026', '2026-07-31'));
    });

    test('neither tithi nor fallback gives nothing', () {
      expect(placed('BhaiDooj', days([...run(kartika, 3, 30)])), isEmpty);
    });

    test('a Purnimanta rule finds a Krishna tithi in the Amanta month before', () {
      final readings = [...whole(ashvina), ...whole(kartika)];
      expect(placed('GyanDhanTrayodashi', days(readings)).first, ('gyan_trayodashi_2026', '2026-07-28'));
      expect(placed('KartikaNandishwarAshtami', days(readings)), [('nandishwar_ashtami_kartika_2026', '2026-08-07')]);
    });

    test('when the month repeats only its Adhik days count', () {
      final readings = [...whole(adhik(shravana)), ...whole(shravana)];
      expect(placed('ShravanaPurnimaRakshabandhan', days(readings)).first.$2, '2026-07-15');
      final nija = [...whole(shravana), ...whole(adhik(shravana))];
      expect(placed('ShravanaPurnimaRakshabandhan', days(nija)).first.$2, '2026-08-14');
    });

    test("only the given year's days count", () {
      expect(placed('BhaiDooj', days(whole(kartika)), year: 2027), isEmpty);
      expect(placed('MargashirshaSheetalnathStotram', days(whole(margashirsha))), [('sheetalnath_stotram_rachna_2026', '2026-07-09')]);
      final lastYear = days([...whole(ashvina), ...whole(kartika)], start: const CivilDate(2025, 7, 1));
      expect(placed('GyanDhanTrayodashi', lastYear), isEmpty);
    });
  });

  group('Akshaya Tritiya', () {
    test("Vaishakha Shukla 3, named after the registry entry", () {
      final o = resolve('AkshayaTritiya', days(whole(vaishakha)), id: 'akshaya_tritiya_dan_divas');
      expect([for (final x in o) (x.id, x.category, x.start.iso)], [('akshaya_tritiya_dan_divas_2026', 'mahaparv', '2026-07-03')]);
    });

    test('a kshaya Tritiya gives the last Dwitiya', () {
      expect(placed('AkshayaTritiya', days([(vaishakha, 1), (vaishakha, 2), (vaishakha, 2), ...run(vaishakha, 4, 30)])),
          [('registry_id_2026', '2026-07-03')]);
    });
  });

  group('Diwali and Chaturmas Nishthapan', () {
    // Amanta Ashvina is Purnimanta Kartika in its Krishna half: Amavasya is day 29.
    test('Diwali on the last evening of Amavasya, Nishthapan on the last Amavasya at the Jain day-start', () {
      final o = resolve('DiwaliChaturmasNishthapan', days(whole(ashvina), evening: {28: 30}), id: 'diwali');
      expect([for (final x in o) (x.id, x.category, x.start.iso)], [
        ('diwali_2026', 'mahaparv', '2026-07-30'),
        ('chaturmas_nishthapan_2026', 'mahaparv', '2026-07-30'),
      ]);
      final evenings = days(whole(ashvina), evening: {29: 1, 28: 30});
      expect(placed('DiwaliChaturmasNishthapan', evenings).first, ('registry_id_2026', '2026-07-29'));
      final doubled = days([...whole(ashvina), (ashvina, 30)], evening: {30: 1});
      expect(placed('DiwaliChaturmasNishthapan', doubled).last, ('chaturmas_nishthapan_2026', '2026-07-31'));
    });

    test('a kshaya Amavasya gives the last Chaturdashi for both when no evening holds Amavasya', () {
      final readings = [...run(ashvina, 1, 29), (ashvina, 29), (kartika, 1)];
      expect(placed('DiwaliChaturmasNishthapan', days(readings, evening: {29: 29})), [
        ('registry_id_2026', '2026-07-30'),
        ('chaturmas_nishthapan_2026', '2026-07-30'),
      ]);
    });
  });

  group('Veer Shasan Jayanti', () {
    test('Purnimanta Shravana Krishna 1, the day after Ashadha Purnima', () {
      expect(placed('VeerShasanJayanti', days([...whole(ashadha), ...whole(shravana)])), [
        ('veer_shasan_jayanti_2026', '2026-07-16'),
        ('shrut_udbhav_divas_2026', '2026-07-16'),
      ]);
    });

    test('a kshaya Krishna 1 falls back to the last Ashadha Purnima', () {
      final readings = [...run(ashadha, 1, 15), (ashadha, 15), ...run(ashadha, 17, 30)];
      expect(placed('VeerShasanJayanti', days(readings)).first, ('veer_shasan_jayanti_2026', '2026-07-16'));
      final adhikPurnima = [...run(adhik(ashadha), 1, 15), ...run(ashadha, 17, 30)];
      expect(placed('VeerShasanJayanti', days(adhikPurnima)), isEmpty);
      expect(placed('VeerShasanJayanti', days(run(ashadha, 1, 15))), isEmpty, reason: 'no Purnimanta Shravana at all');
    });
  });

  group('Karwa Chauth, Ahoi and Dampatya Ashtami', () {
    // Amanta Ashvina's Krishna half: Krishna 4 is day 18, Krishna 8 day 22.
    test('Karwa on the first Krishna 4; Ahoi and Dampatya on the first evening of Krishna 8', () {
      final o = resolve('SplitDayAhoiKarwaDampatya', days(whole(ashvina), evening: {21: 23}));
      expect([for (final x in o) (x.id, x.category, x.start.iso)], [
        ('karwa_chauth_2026', 'vrat', '2026-07-19'),
        ('ahoi_ashtami_2026', 'vrat', '2026-07-22'),
        ('dampatya_ashtami_2026', 'vrat', '2026-07-22'),
      ]);
    });

    test('a kshaya Krishna 4 gives the last Krishna 3; no evening of Krishna 8 gives the first of Krishna 7', () {
      final readings = [...run(ashvina, 1, 18), (ashvina, 18), ...run(ashvina, 20, 30)];
      expect(placed('SplitDayAhoiKarwaDampatya', days(readings, evening: {21: 22, 22: 24})), [
        ('karwa_chauth_2026', '2026-07-19'),
        ('ahoi_ashtami_2026', '2026-07-22'),
        ('dampatya_ashtami_2026', '2026-07-22'),
      ]);
    });

    test('a doubled Krishna 4 gives Karwa its first day; an evening of Krishna 8 wins over an earlier one of Krishna 7', () {
      final readings = [...run(ashvina, 1, 19), (ashvina, 19), ...run(ashvina, 20, 30)];
      expect(placed('SplitDayAhoiKarwaDampatya', days(readings)).take(2), [
        ('karwa_chauth_2026', '2026-07-19'),
        ('ahoi_ashtami_2026', '2026-07-24'),
      ]);
    });

    test('with neither tithi the events are left out one by one', () {
      final readings = [...run(ashvina, 1, 17), ...run(ashvina, 24, 30)];
      expect(placed('SplitDayAhoiKarwaDampatya', days(readings)), isEmpty);
    });
  });
}
