import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/format/festival_text.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:panchang_engine/panchang_engine.dart';

FestivalOccurrence festival({
  required String category,
  required CivilDate start,
  CivilDate? end,
  String name = 'A festival',
  String nameHindi = 'एक पर्व',
  String? id,
}) => FestivalOccurrence(
  id: id ?? '${category}_${start.iso}_$name',
  occurrenceId: '${id ?? category}_${start.iso}_$name',
  ruleId: id ?? category,
  category: category,
  name: name,
  nameHindi: nameHindi,
  start: start,
  end: end ?? start,
);

const oct20 = CivilDate(2026, 10, 20);

void main() {
  group('the mark each registry category gets', () {
    test('kalyanaks get the ring', () {
      expect(kindOf('kalyanak'), FestivalKind.kalyanak);
      expect(kindOf('janam_kalyanak'), FestivalKind.kalyanak);
    });

    test('mahaparvas get the square', () {
      for (final category in ['mahaparv', 'festival', 'utsav']) {
        expect(kindOf(category), FestivalKind.mahaparva, reason: category);
      }
    });

    test('every kind of vrat gets the green dot, Navapad Oli and the Namokar chain included', () {
      for (final category in ['vrat', 'monthly_vrat', 'tap_vrat', 'parva_vrat', 'mahaparv_vrat']) {
        expect(kindOf(category), FestivalKind.vrat, reason: category);
      }
    });

    test('the other observances get the red parva dot', () {
      for (final category in [
        'parva',
        'jayanti',
        'punyatithi',
        'punya_tithi',
        'shastra',
        'auspicious',
        'poojan',
        'parv_vidhi',
      ]) {
        expect(kindOf(category), FestivalKind.parva, reason: category);
      }
    });

    test('red is for parva and kalyanak, green for vrat', () {
      expect(FestivalKind.values.where((k) => k.isVrat), [FestivalKind.vrat]);
    });

    test('every category in the registry is one the mapping names', () {
      final registry = jsonDecode(File('assets/festival_registry.json').readAsStringSync()) as Map<String, Object?>;
      final categories = {
        for (final f in registry['festivals']! as List<Object?>) (f! as Map<String, Object?>)['category'],
      };
      expect(categories.difference(namedCategories), isEmpty);
    });
  });

  group('the festivals on a date', () {
    test('a span covers every day from its start to its end, and no other', () {
      final span = festival(
        category: 'mahaparv',
        start: const CivilDate(2026, 11, 17),
        end: const CivilDate(2026, 11, 24),
      );

      expect(festivalsOn([span], const CivilDate(2026, 11, 16)), isEmpty);
      for (var d = span.start; d.compareTo(span.end) <= 0; d = d.next()) {
        expect(festivalsOn([span], d), [span]);
      }
      expect(festivalsOn([span], const CivilDate(2026, 11, 25)), isEmpty);
    });
  });

  group('festival lines', () {
    test('use the Hindi name in Hindi and the English one in English', () {
      final f = festival(category: 'kalyanak', start: oct20, name: 'Shri Neminath Ji', nameHindi: 'श्री नेमिनाथ जी');

      expect(festivalLines([f], Lang.hi).single.name, 'श्री नेमिनाथ जी');
      expect(festivalLines([f], Lang.en).single.name, 'Shri Neminath Ji');
    });

    test('fall back to English where the registry has no Hindi name', () {
      final f = festival(category: 'parva', start: oct20, name: 'Pakhi', nameHindi: '');

      expect(festivalLines([f], Lang.hi).single.name, 'Pakhi');
    });

    test('show a repeated name once', () {
      final six = [
        for (var i = 0; i < 6; i++) festival(category: 'vrat', start: oct20, id: 'multi_$i', name: 'Multi-Vrat Start'),
      ];

      expect(festivalLines(six, Lang.en), hasLength(1));
    });

    test('put mahaparva first, then kalyanak, parva and vrat, keeping the engine order within a kind', () {
      final lines = festivalLines([
        festival(category: 'vrat', start: oct20, name: 'v'),
        festival(category: 'parva', start: oct20, name: 'p1'),
        festival(category: 'kalyanak', start: oct20, name: 'k'),
        festival(category: 'parva', start: oct20, name: 'p2'),
        festival(category: 'mahaparv', start: oct20, name: 'm'),
      ], Lang.en);

      expect(lines.map((l) => l.name), ['m', 'k', 'p1', 'p2', 'v']);
    });

    test('carry the span of their festival', () {
      final span = festival(
        category: 'mahaparv',
        start: const CivilDate(2026, 11, 17),
        end: const CivilDate(2026, 11, 24),
      );

      final line = festivalLines([span], Lang.en).single;

      expect((line.start, line.end), (span.start, span.end));
      expect(line.kind, FestivalKind.mahaparva);
    });
  });

  group('one event under several registry entries', () {
    const nov9 = CivilDate(2026, 11, 9);

    test('shows once, under the name its group chooses, with the strongest mark', () {
      final lines = festivalLines([
        festival(
          category: 'kalyanak',
          start: nov9,
          id: 'shri_mahavira_ji___liberation_kalyanak_15_vrindavan_uttarapurana_ashadhara',
          name: 'k',
        ),
        festival(category: 'mahaparv', start: nov9, id: 'mahavir_nirvana_deepavali', name: 'n'),
        festival(category: 'mahaparv', start: nov9, id: 'diwali', name: 'Diwali'),
        festival(category: 'parva', start: nov9, id: 'pakhi', name: 'p'),
      ], Lang.en);

      expect(lines.map((l) => (l.name, l.kind)), [('Diwali', FestivalKind.mahaparva), ('p', FestivalKind.parva)]);
    });

    test('takes the strongest mark even when the named entry is weaker', () {
      final lines = festivalLines([
        festival(category: 'vrat', start: nov9, id: 'raksha_bandhan', name: 'Raksha Bandhan'),
        festival(category: 'mahaparv', start: nov9, id: 'rakshabandhan_vrat', name: 'r'),
      ], Lang.en);

      expect(lines.map((l) => (l.name, l.kind)), [('Raksha Bandhan', FestivalKind.mahaparva)]);
    });

    test('keeps its own name on a date the named entry is not on', () {
      final lines = festivalLines([
        festival(category: 'vrat', start: nov9, id: 'rakshabandhan_vrat', name: 'Rakshabandhan Vrat'),
        festival(category: 'mahaparv', start: nov9, id: 'shravana_purnima_rakshabandhan', name: 'Shravana Purnima'),
      ], Lang.en);

      expect(lines.map((l) => (l.name, l.kind)), [('Rakshabandhan Vrat', FestivalKind.mahaparva)]);
    });

    test('carries the span of the entry it is named after', () {
      final line = festivalLines([
        festival(category: 'mahaparv', start: nov9, end: const CivilDate(2026, 11, 11), id: 'diwali', name: 'Diwali'),
        festival(category: 'mahaparv', start: nov9, id: 'mahavir_nirvana_deepavali', name: 'n'),
      ], Lang.en).single;

      expect((line.start, line.end), (nov9, const CivilDate(2026, 11, 11)));
    });

    test('stays apart from another group on the same date', () {
      final lines = festivalLines([
        festival(category: 'mahaparv', start: nov9, id: 'diwali', name: 'Diwali'),
        festival(category: 'mahaparv', start: nov9, id: 'raksha_bandhan', name: 'Raksha Bandhan'),
      ], Lang.en);

      expect(lines.map((l) => l.name), ['Diwali', 'Raksha Bandhan']);
    });

    test('names only entries the bundled registry has', () {
      final registry = jsonDecode(File('assets/festival_registry.json').readAsStringSync()) as Map<String, Object?>;
      final ids = {for (final f in registry['festivals']! as List<Object?>) (f! as Map<String, Object?>)['id']};

      for (final group in sameEvents) {
        expect(ids, containsAll({group.shown, ...group.also}), reason: group.shown);
      }
    });
  });

  group('the marks in a Month cell', () {
    test('one per kind, in the lines\' order, at most three', () {
      final lines = festivalLines([
        festival(category: 'vrat', start: oct20, name: 'v1'),
        festival(category: 'vrat', start: oct20, name: 'v2'),
        festival(category: 'parva', start: oct20, name: 'p'),
        festival(category: 'kalyanak', start: oct20, name: 'k'),
      ], Lang.en);

      expect(cellMarks(lines), [FestivalKind.kalyanak, FestivalKind.parva, FestivalKind.vrat]);
    });

    test('drop the vrat dot when all four kinds fall on the day', () {
      final lines = festivalLines([
        for (final category in ['vrat', 'parva', 'kalyanak', 'mahaparv'])
          festival(category: category, start: oct20, name: category),
      ], Lang.en);

      expect(cellMarks(lines), [FestivalKind.mahaparva, FestivalKind.kalyanak, FestivalKind.parva]);
    });
  });

  group('upcoming festivals', () {
    final year = [
      festival(category: 'kalyanak', start: const CivilDate(2026, 10, 20), name: 'today'),
      festival(category: 'vrat', start: const CivilDate(2026, 10, 21), name: 'vrat only'),
      festival(category: 'parva', start: const CivilDate(2026, 10, 25), name: 'p25'),
      festival(category: 'vrat', start: const CivilDate(2026, 10, 25), name: 'v25'),
      festival(category: 'kalyanak', start: const CivilDate(2026, 10, 27), name: 'k27'),
      festival(category: 'kalyanak', start: const CivilDate(2026, 10, 29), name: 'k29'),
      festival(category: 'parva', start: const CivilDate(2026, 10, 29), name: 'p29'),
      festival(
        category: 'mahaparv',
        start: const CivilDate(2026, 11, 17),
        end: const CivilDate(2026, 11, 24),
        name: 'm',
      ),
      festival(category: 'parva', start: const CivilDate(2026, 11, 30), name: 'p30'),
    ];

    test('are the next four dates after the one shown, skipping vrats', () {
      final next = upcomingFestivals(year, after: oct20, lang: Lang.en);

      expect(next.map((d) => d.date), const [
        CivilDate(2026, 10, 25),
        CivilDate(2026, 10, 27),
        CivilDate(2026, 10, 29),
        CivilDate(2026, 11, 17),
      ]);
      expect(next.first.lines.map((l) => l.name), ['p25']);
      expect(next[2].lines.map((l) => l.name), ['k29', 'p29']);
    });

    test('list a span on its first day only', () {
      final next = upcomingFestivals(year, after: const CivilDate(2026, 11, 18), lang: Lang.en);

      expect(next.map((d) => d.date), const [CivilDate(2026, 11, 30)]);
    });
  });

  group('the Festivals list', () {
    const oct31 = CivilDate(2026, 10, 31);
    final year = [
      festival(category: 'kalyanak', start: const CivilDate(2026, 10, 20), name: 'past'),
      festival(
        category: 'mahaparv',
        start: const CivilDate(2026, 10, 29),
        end: const CivilDate(2026, 11, 2),
        name: 'ongoing',
      ),
      festival(category: 'vrat', start: oct31, name: 'v31'),
      festival(category: 'kalyanak', start: const CivilDate(2026, 11, 3), name: 'k3'),
      festival(category: 'parva', start: const CivilDate(2026, 11, 3), name: 'p3'),
      festival(category: 'vrat', start: const CivilDate(2026, 11, 4), name: 'v4'),
    ];

    test('starts at the given date and puts an ongoing span on it', () {
      final dates = festivalDates(year, from: oct31, lang: Lang.en);

      expect(dates.map((d) => d.date), const [oct31, CivilDate(2026, 11, 3), CivilDate(2026, 11, 4)]);
      expect(dates.first.lines.map((l) => l.name), ['ongoing', 'v31']);
      expect(dates[1].lines.map((l) => l.name), ['k3', 'p3']);
    });

    test('a filter keeps only its kind and drops the dates left empty', () {
      final dates = festivalDates(year, from: oct31, lang: Lang.en, filter: FestivalFilter.vrat);

      expect(
        [for (final d in dates) (d.date, d.lines.map((l) => l.name).join())],
        [(oct31, 'v31'), (const CivilDate(2026, 11, 4), 'v4')],
      );
    });

    test('each kind\'s filter keeps that kind alone, and all keeps every kind', () {
      final every = [
        for (final category in ['mahaparv', 'kalyanak', 'parva', 'vrat'])
          festival(category: category, start: oct31, name: category),
      ];

      for (final filter in FestivalFilter.values) {
        final kinds = festivalDates(every, from: oct31, lang: Lang.en, filter: filter).single.lines.map((l) => l.kind);
        expect(kinds, filter.kind == null ? FestivalKind.values : [filter.kind], reason: filter.name);
      }
    });

    test('a merged event is filed under its strongest mark', () {
      final nov9 = const CivilDate(2026, 11, 9);
      final day = [
        festival(category: 'mahaparv', start: nov9, id: 'diwali', name: 'Diwali'),
        festival(
          category: 'kalyanak',
          start: nov9,
          id: 'shri_mahavira_ji___liberation_kalyanak_15_vrindavan_uttarapurana_ashadhara',
          name: 'k',
        ),
      ];

      expect(festivalDates(day, from: nov9, lang: Lang.en, filter: FestivalFilter.kalyanak), isEmpty);
      expect(
        festivalDates(day, from: nov9, lang: Lang.en, filter: FestivalFilter.mahaparva).single.lines.single.name,
        'Diwali',
      );
    });
  });

  group('a span\'s dates', () {
    test('within one month name it once', () {
      expect(dateRange(const CivilDate(2026, 11, 17), const CivilDate(2026, 11, 24), Lang.hi), '17–24 नवंबर');
      expect(dateRange(const CivilDate(2026, 11, 17), const CivilDate(2026, 11, 24), Lang.en), '17–24 November');
    });

    test('across months name both', () {
      expect(dateRange(const CivilDate(2026, 8, 29), const CivilDate(2026, 10, 9), Lang.hi), '29 अगस्त – 9 अक्टूबर');
    });
  });
}
