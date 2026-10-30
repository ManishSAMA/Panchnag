// Bhaktambar Vrat (Python `BhaktambarVratFestival`): Ashtami and Chaturdashi of
// every paksha as two independent days (plans/case-study-bhaktambar-saptami.md).
// Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/bhaktambar.dart';
import 'package:test/test.dart';

const chaitra = LunarMonth(index: 0, isAdhika: false);
const ashwin = LunarMonth(index: 6, isAdhika: false);
const agrahayana = LunarMonth(index: 8, isAdhika: false);
const adhikJyeshtha = LunarMonth(index: 2, isAdhika: true);

/// One day per Jain day-start tithi from [start], all in one month.
List<FestivalDay> fortnight(List<int> tithis, {CivilDate start = const CivilDate(2026, 3, 1), LunarMonth month = chaitra}) {
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
        month: month,
        purnimantaMonth: month,
      ),
  ];
}

const shukla = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];

const bhaktambar = FestivalEntry(
  id: 'bhaktambar_vrat',
  ruleType: 'BhaktambarVrat',
  category: 'vrat',
  name: 'Bhaktambar Vrat',
  nameHindi: 'भक्ताम्बर व्रत',
  profiles: ['all'],
  jainMonth: null,
  paksha: null,
  tithi: null,
  dayRule: DayRule.udaya,
  vriddhiRule: null,
  originPullback: false,
);

Map<String, String> observed(List<FestivalDay> days, {int year = 2026}) =>
    {for (final o in bhaktambarVrat(bhaktambar, days, year: year)) o.id: o.start.iso};

void main() {
  test('a paksha holds an Ashtami and a Chaturdashi observance, each its own one-day occurrence', () {
    final o = bhaktambarVrat(bhaktambar, fortnight(shukla), year: 2026);
    expect([for (final x in o) (x.id, x.occurrenceId, x.start.iso, x.end.iso, x.ruleId)], [
      ('bhaktambar_vrat_2026_chaitra_shukla_ashtami', 'bhaktambar_vrat_2026_chaitra_shukla_ashtami', '2026-03-08',
          '2026-03-08', 'bhaktambar_vrat'),
      ('bhaktambar_vrat_2026_chaitra_shukla_chaturdashi', 'bhaktambar_vrat_2026_chaitra_shukla_chaturdashi',
          '2026-03-14', '2026-03-14', 'bhaktambar_vrat'),
    ]);
  });

  test('a Krishna paksha is named by its Purnimanta month', () {
    expect(observed(fortnight([for (var t = 16; t <= 30; t++) t])).keys,
        ['bhaktambar_vrat_2026_chaitra_krishna_ashtami', 'bhaktambar_vrat_2026_chaitra_krishna_chaturdashi']);
  });

  test('a doubled tithi is observed on its first day', () {
    expect(observed(fortnight([6, 7, 8, 8, 9, 10, 11, 12, 13, 14, 14, 15]))['bhaktambar_vrat_2026_chaitra_shukla_ashtami'],
        '2026-03-03');
  });

  test('a kshaya Ashtami is observed on the first Saptami day instead', () {
    expect(observed(fortnight([6, 7, 7, 9, 10]))['bhaktambar_vrat_2026_chaitra_shukla_ashtami'], '2026-03-02');
  });

  test('a kshaya Chaturdashi is not observed at all', () {
    expect(observed(fortnight([12, 13, 15])), isEmpty);
  });

  test('an Adhik fortnight is tagged in the id', () {
    expect(observed(fortnight([8, 14], month: adhikJyeshtha)).keys, [
      'bhaktambar_vrat_2026_adhika_jyeshtha_shukla_ashtami',
      'bhaktambar_vrat_2026_adhika_jyeshtha_shukla_chaturdashi',
    ]);
  });

  test('Ashwin and Agrahayana take their legacy id spellings', () {
    expect(observed(fortnight([8], month: ashwin)).keys, ['bhaktambar_vrat_2026_ashvina_shukla_ashtami']);
    expect(observed(fortnight([8], month: agrahayana)).keys, ['bhaktambar_vrat_2026_margashirsha_shukla_ashtami']);
  });

  test('a fortnight ends at a change of month or a gap in the days', () {
    final split = [...fortnight([7, 8]), ...fortnight([9, 10], start: const CivilDate(2026, 3, 10))];
    final shifted = [...fortnight([6, 7]), ...fortnight([8, 9], start: const CivilDate(2026, 3, 3), month: ashwin)];
    expect(observed(split).keys, ['bhaktambar_vrat_2026_chaitra_shukla_ashtami']);
    expect(observed(shifted).keys, ['bhaktambar_vrat_2026_chaitra_shukla_ashtami', 'bhaktambar_vrat_2026_ashvina_shukla_ashtami']);
  });

  test('only days in the requested year are observed', () {
    // Ashtami on 31 Dec 2025 belongs to 2025, though its fortnight runs into 2026.
    final days = fortnight([7, 8, 9, 10, 11, 12, 13, 14], start: const CivilDate(2025, 12, 30));
    expect(observed(days).keys, ['bhaktambar_vrat_2026_chaitra_shukla_chaturdashi']);
  });
}
