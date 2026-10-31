import 'dart:convert';
import 'dart:io';

import 'package:panchang_engine/panchang_engine.dart';
import 'package:test/test.dart';

/// The committed registry, generated from Python `registry.py` (run from the package root).
String sharedRegistryJson() => File('../../../shared/festival_registry.json').readAsStringSync();

String registryJson(List<Map<String, Object?>> festivals, {int schemaVersion = 1}) =>
    jsonEncode({'schema_version': schemaVersion, 'festivals': festivals});

Map<String, Object?> entry({
  String id = 'test_kalyanak',
  String ruleType = 'SingleTithi',
  Map<String, Object?> extra = const {},
}) => {
  'id': id,
  'rule_type': ruleType,
  'category': 'kalyanak',
  'name': 'Test Kalyanak',
  'name_hindi': 'परीक्षण कल्याणक',
  'profiles': ['all'],
  'jain_month': 'Chaitra',
  'paksha': 'Shukla',
  'tithi': 13,
  ...extra,
};

void main() {
  group('the shared registry', () {
    final registry = FestivalRegistry.fromJson(sharedRegistryJson());

    test('loads every festival with a unique id', () {
      final ids = registry.entries.map((e) => e.id).toList();
      expect(ids, isNotEmpty);
      expect(ids.toSet(), hasLength(ids.length));
    });

    test('keeps registry order, which decides the order rules run in', () {
      final raw = (jsonDecode(sharedRegistryJson()) as Map<String, Object?>)['festivals']! as List<Object?>;
      expect(registry.entries.map((e) => e.id), [for (final f in raw.cast<Map<String, Object?>>()) f['id']]);
    });
  });

  group('an entry', () {
    FestivalEntry only(Map<String, Object?> e) => FestivalRegistry.fromJson(registryJson([e])).entries.single;

    test('carries its rule, target tithi and names', () {
      final e = only(entry());
      expect(
        (e.id, e.ruleType, e.category, e.name, e.nameHindi, e.jainMonth, e.paksha, e.tithi),
        ('test_kalyanak', 'SingleTithi', 'kalyanak', 'Test Kalyanak', 'परीक्षण कल्याणक', 'Chaitra', 'Shukla', 13),
      );
      expect(e.profiles, ['all']);
    });

    test('defaults to the udaya day rule, no vriddhi override and no origin pull-back', () {
      final e = only(entry());
      expect((e.dayRule, e.vriddhiRule, e.originPullback), (DayRule.udaya, null, false));
    });

    test('reads the optional day rule, vriddhi rule and origin pull-back', () {
      final e = only(entry(extra: {'day_rule': 'pradosh', 'vriddhi_rule': 'second_day', 'origin_pullback': true}));
      expect((e.dayRule, e.vriddhiRule, e.originPullback), (DayRule.pradosh, 'second_day', true));
    });

    test('treats an empty month or a missing paksha and tithi as absent', () {
      final e = only({...entry(extra: {'jain_month': ''}), 'paksha': null, 'tithi': null}
        ..removeWhere((_, v) => v == null));
      expect((e.jainMonth, e.paksha, e.tithi), (null, null, null));
    });

    test('an unknown day rule fails at load time, not silently as udaya', () {
      expect(
        () => only(entry(extra: {'day_rule': 'pradosha'})),
        throwsA(isA<FormatException>().having((e) => e.message, 'message', contains('pradosha'))),
      );
    });
  });

  test('a registry of another schema version is refused', () {
    expect(() => FestivalRegistry.fromJson(registryJson([entry()], schemaVersion: 2)), throwsFormatException);
  });
}
