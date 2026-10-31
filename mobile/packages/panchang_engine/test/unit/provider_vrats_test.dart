// Step 12 (plans/mobile-phase5-festivals.md §3 F): the vrats Python computes
// in its own day loop (`jain_observances/vrats/`) rather than from the
// snapshots. They read a 45- or 75-day window from 7 days before the first of
// the Gregorian month the target tithi falls in, skip Adhik days, and take the
// second day of a vriddhi through the provider (the first of two days sharing
// a Jain day-start tithi reads as the tithi before). The months are the raw
// days' own. Tithis are 1-30: Shukla n is n, Krishna n is 15 + n.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/rules/provider_vrats.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

const chaitra = LunarMonth(index: 0, isAdhika: false);
const ashadha = LunarMonth(index: 3, isAdhika: false);
const shravana = LunarMonth(index: 4, isAdhika: false);
const bhadrapada = LunarMonth(index: 5, isAdhika: false);
const ashvina = LunarMonth(index: 6, isAdhika: false);

LunarMonth adhik(LunarMonth m) => LunarMonth(index: m.index, isAdhika: true);

/// One day per (Amanta month, Jain tithi) from [start]; [atSunrise] overrides
/// the sunrise tithi of a day by its index.
List<FestivalDay> days(
  List<(LunarMonth, int)> readings, {
  required CivilDate start,
  Map<int, int> atSunrise = const {},
}) => [
  for (final (i, (month, tithi)) in readings.indexed)
    FestivalDay(
      date: start.plusDays(i),
      sunrise: 2461222.5 + i,
      sunset: 2461223.0 + i,
      sunriseTithi: atSunrise[i] ?? tithi,
      jainTithi: tithi,
      eveningTithi: tithi,
      month: month,
      purnimantaMonth: tithi <= 15 ? month : LunarMonth(index: (month.index + 1) % 12, isAdhika: month.isAdhika),
      standardOffset: Duration.zero,
    ),
];

List<(LunarMonth, int)> run(LunarMonth month, int from, int to) => [for (var t = from; t <= to; t++) (month, t)];

List<(LunarMonth, int)> whole(LunarMonth month) => run(month, 1, 30);

FestivalEntry entry(String ruleType, {required String id, required String jainMonth, String category = 'mahaparv_vrat'}) =>
    FestivalEntry(
      id: id,
      ruleType: ruleType,
      category: category,
      name: 'Registry name',
      nameHindi: 'नाम',
      profiles: const ['all'],
      jainMonth: jainMonth,
      paksha: null,
      tithi: null,
      dayRule: DayRule.udaya,
      vriddhiRule: null,
      originPullback: false,
    );

List<(String, String, String)> spans(List<FestivalOccurrence> list) =>
    [for (final o in list) (o.id, o.start.iso, o.end.iso)];

void main() {
  group('Daslakshan', () {
    List<FestivalOccurrence> daslakshan(List<FestivalDay> days) =>
        providerRules['DaslakshanVrat']!(entry('DaslakshanVrat', id: 'daslakshan_bhadrapada', jainMonth: 'Bhadrapada'), days,
            year: 2026);

    // Bhadrapada Shukla 5 is 2026-08-13 and Shukla 14 2026-08-22.
    List<(LunarMonth, int)> season({List<(LunarMonth, int)>? bhadrapadaDays}) =>
        [...run(shravana, 16, 30), ...(bhadrapadaDays ?? whole(bhadrapada)), ...whole(ashvina)];
    const from = CivilDate(2026, 7, 25);

    test('Shukla 5 to Shukla 14, named by the entry month as the registry spells it', () {
      final o = daslakshan(days(season(), start: from));
      expect([for (final x in o) (x.id, x.occurrenceId, x.ruleId, x.category, x.start.iso, x.end.iso)], [
        ('daslakshan_Bhadrapada_2026', 'daslakshan_Bhadrapada_2026', 'daslakshan_bhadrapada', 'mahaparv_vrat',
            '2026-08-13', '2026-08-22'),
      ]);
    });

    test('a vriddhi adds its day', () {
      final doubled = [...run(bhadrapada, 1, 7), (bhadrapada, 7), ...run(bhadrapada, 8, 30)];
      expect(spans(daslakshan(days(season(bhadrapadaDays: doubled), start: from))).single.$3, '2026-08-23');
    });

    test('a kshaya inside the ten days starts a day early, to keep ten', () {
      final noSaptami = [...run(bhadrapada, 1, 6), ...run(bhadrapada, 8, 30), (bhadrapada, 30)];
      expect(spans(daslakshan(days(season(bhadrapadaDays: noSaptami), start: from))),
          [('daslakshan_Bhadrapada_2026', '2026-08-12', '2026-08-21')]);
    });

    test("a vriddhi's extra day makes up for a kshaya, so the start stays", () {
      final both = [...run(bhadrapada, 1, 6), ...run(bhadrapada, 8, 9), (bhadrapada, 9), ...run(bhadrapada, 10, 30)];
      expect(spans(daslakshan(days(season(bhadrapadaDays: both), start: from))),
          [('daslakshan_Bhadrapada_2026', '2026-08-13', '2026-08-22')]);
    });

    test('a kshaya Panchami starts from the first Shashthi, a day early', () {
      final noPanchami = [...run(bhadrapada, 1, 4), (bhadrapada, 4), ...run(bhadrapada, 6, 30)];
      expect(spans(daslakshan(days(season(bhadrapadaDays: noPanchami), start: from))).single.$2, '2026-08-13');
    });

    // Bhadrapada Shukla 5 on 2026-09-30 puts the window at 2026-08-25 to
    // 2026-10-08, one day short of Shukla 14.
    test('days past the window are not seen', () {
      final late = days([...whole(bhadrapada), ...whole(ashvina)], start: const CivilDate(2026, 9, 26));
      expect(spans(daslakshan(late)), [('daslakshan_Bhadrapada_2026', '2026-09-29', '2026-10-08')]);
    });

    test('neither Panchami nor Shashthi in the month gives none', () {
      final readings = [...run(shravana, 16, 30), ...run(bhadrapada, 1, 4), ...run(bhadrapada, 7, 30)];
      expect(daslakshan(days(readings, start: from)), isEmpty);
    });
  });

  group('Ratnatraya', () {
    List<FestivalOccurrence> ratnatraya(List<FestivalDay> days) =>
        providerRules['RatnatrayaVrat']!(entry('RatnatrayaVrat', id: 'ratnatraya_chaitra', jainMonth: 'Chaitra'), days,
            year: 2026);

    // Chaitra Shukla 13 is 2026-03-13 and Purnima 2026-03-15.
    const from = CivilDate(2026, 3, 1);

    test('a Prarambh on Shukla 13 and a Purna on Purnima, one day each', () {
      final o = ratnatraya(days(whole(chaitra), start: from));
      expect([for (final x in o) (x.id, x.occurrenceId, x.category, x.start.iso, x.end.iso)], [
        ('ratnatraya_vrat_prarambh_chaitra_2026', 'ratnatraya_vrat_prarambh_chaitra_2026', 'mahaparv_vrat', '2026-03-13', '2026-03-13'),
        ('ratnatraya_vrat_purna_chaitra_2026', 'ratnatraya_vrat_purna_chaitra_2026', 'mahaparv_vrat', '2026-03-15', '2026-03-15'),
      ]);
    });

    test('a vriddhi of Purnima ends on its second day', () {
      final readings = [...run(chaitra, 1, 15), (chaitra, 15), ...run(chaitra, 16, 30)];
      expect(spans(ratnatraya(days(readings, start: from))).last.$2, '2026-03-16');
    });

    test('a doubled Trayodashi starts on its second day', () {
      final readings = [...run(chaitra, 1, 13), (chaitra, 13), ...run(chaitra, 14, 30)];
      expect(spans(ratnatraya(days(readings, start: from))).map((x) => x.$2), ['2026-03-14', '2026-03-16']);
    });

    test('a kshaya Purnima ends on Chaturdashi, starting on Dwadashi', () {
      final readings = [...run(chaitra, 1, 14), ...run(chaitra, 16, 30), (chaitra, 30)];
      expect(spans(ratnatraya(days(readings, start: from))).map((x) => x.$2), ['2026-03-12', '2026-03-14']);
    });

    test('a kshaya Chaturdashi starts on Dwadashi, to keep three days', () {
      final readings = [...run(chaitra, 1, 13), ...run(chaitra, 15, 30), (chaitra, 30)];
      expect(spans(ratnatraya(days(readings, start: from))).map((x) => x.$2), ['2026-03-12', '2026-03-14']);
    });

    // Chaitra Shukla 13 on 2026-09-28 puts the window at 2026-08-25 to
    // 2026-10-08, which holds the Adhik Shukla 13 of 2026-08-29 too.
    test('Adhik days are skipped', () {
      final readings = days([...whole(adhik(chaitra)), ...whole(chaitra)], start: const CivilDate(2026, 8, 17));
      expect(spans(ratnatraya(readings)).first.$2, '2026-09-28');
    });
  });

  group('Shodashkaran', () {
    List<FestivalOccurrence> shodashkaran(List<FestivalDay> days, {String cycle = 'BHADRAPADA_ASHVINA'}) =>
        providerRules['ShodashkaranVrat']!(entry('ShodashkaranVrat', id: 'shodashkaran_x', jainMonth: cycle), days,
            year: 2026);

    // Amanta Shravana Krishna 1 is 2026-07-16; Bhadrapada Krishna 1 2026-08-15.
    const from = CivilDate(2026, 7, 1);
    List<(LunarMonth, int)> season() => [...whole(shravana), ...whole(bhadrapada), ...whole(ashvina)];

    test('from Shravana Krishna 1 through the next Krishna 1, named by the cycle', () {
      final o = shodashkaran(days(season(), start: from));
      expect([for (final x in o) (x.id, x.occurrenceId, x.ruleId, x.category, x.start.iso, x.end.iso)], [
        ('shodashkaran_BHADRAPADA_ASHVINA_2026', 'shodashkaran_BHADRAPADA_ASHVINA_2026', 'shodashkaran_x', 'mahaparv_vrat',
            '2026-07-16', '2026-08-15'),
      ]);
    });

    test('a doubled closing Krishna 1 ends on its second day', () {
      final readings = [...whole(shravana), ...run(bhadrapada, 1, 16), (bhadrapada, 16), ...run(bhadrapada, 17, 30)];
      expect(spans(shodashkaran(days(readings, start: from))).single.$3, '2026-08-16');
    });

    test('Krishna 1 at sunrise counts when the Jain day-start has moved on', () {
      final readings = [...run(shravana, 1, 15), ...run(shravana, 17, 30), ...whole(bhadrapada)];
      expect(spans(shodashkaran(days(readings, start: from, atSunrise: {15: 16}))).single.$2, '2026-07-16');
    });

    test('without a closing Krishna 1 in Bhadrapada it runs 34 days, to Krishna 1 + 33', () {
      final readings = [...whole(shravana), ...run(bhadrapada, 1, 15), ...run(bhadrapada, 17, 30), ...whole(ashvina)];
      expect(spans(shodashkaran(days(readings, start: from))).single.$3, '2026-08-18');
    });

    test('the other cycles start in Pausha and Phalguna; an unknown cycle gives none', () {
      const pausha = LunarMonth(index: 9, isAdhika: false);
      const magha = LunarMonth(index: 10, isAdhika: false);
      final winter = days([...whole(pausha), ...whole(magha)], start: const CivilDate(2026, 1, 1));
      expect(spans(shodashkaran(winter, cycle: 'MAGHA_PHALGUNA')),
          [('shodashkaran_MAGHA_PHALGUNA_2026', '2026-01-16', '2026-02-15')]);
      expect(shodashkaran(days(season(), start: from), cycle: 'SHRAVANA'), isEmpty);
    });

    test("a Krishna 1 within its first 28 days, or another month's, does not close it", () {
      final short = [...run(shravana, 16, 30), ...run(bhadrapada, 1, 12), ...run(bhadrapada, 16, 30), ...whole(ashvina)];
      expect(spans(shodashkaran(days(short, start: from))).single.$3, '2026-08-03');
      final otherMonth = [...whole(shravana), ...whole(ashvina)];
      expect(spans(shodashkaran(days(otherMonth, start: from))).single.$3, '2026-08-18');
    });

    test("the previous month's Krishna 1 in the window does not start it", () {
      final readings = [...run(ashadha, 16, 30), ...whole(shravana), ...whole(bhadrapada)];
      expect(spans(shodashkaran(days(readings, start: from))).single.$2, '2026-07-31');
    });

    // Python finds the first Pausha Krishna 1 of the window in December of the
    // year before, then opens its window in December of the year itself.
    test('a December month opens the window in December of the year', () {
      final months = [for (var k = 0; k < 14; k++) LunarMonth(index: (9 + k) % 12, isAdhika: false)];
      final readings = days([for (final m in months) ...whole(m)], start: const CivilDate(2025, 12, 1));
      expect(spans(shodashkaran(readings, cycle: 'MAGHA_PHALGUNA')),
          [('shodashkaran_MAGHA_PHALGUNA_2026', '2026-12-11', '2027-01-10')]);
    });

    test('Adhik days are skipped', () {
      final readings = [...run(adhik(shravana), 16, 30), ...whole(shravana), ...whole(bhadrapada)];
      expect(spans(shodashkaran(days(readings, start: const CivilDate(2026, 7, 1)))).single.$2, '2026-07-31');
    });
  });

  group('Ravivara', () {
    final delhi = festivalDays(
      location: const Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
      year: 2026,
      sunriseRule: SunriseRule.modern,
    );
    bool ashadhaShukla(FestivalDay d) => d.month.index == 3 && tithiAt(d.sunrise + 84 / 1440) <= 15;

    test("nine Sundays from the last Sunday of Ashadha Shukla, read 84 minutes after sunrise", () {
      final o = providerRules['RavivaraVrat']!(
          entry('RavivaraVrat', id: 'ravivara', jainMonth: 'Ashadha', category: 'parva_vrat'), delhi, year: 2026).single;
      expect((o.id, o.occurrenceId, o.category), ('ravivara_2026', 'ravivara_2026', 'parva_vrat'));
      final start = delhi.firstWhere((d) => d.date == o.start);
      expect(start.date.vara, 0);
      expect(ashadhaShukla(start), isTrue);
      expect(ashadhaShukla(delhi.firstWhere((d) => d.date == o.start.plusDays(7))), isFalse);
      expect(o.end, o.start.plusDays(56));
    });

    test("none when no Sunday from June to mid-August is in Ashadha Shukla", () {
      expect(providerRules['RavivaraVrat']!(entry('RavivaraVrat', id: 'ravivara', jainMonth: 'Ashadha'), delhi, year: 2030),
          isEmpty);
    });
  });
}
