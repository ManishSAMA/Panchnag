/// The festival definitions, read from `shared/festival_registry.json`, which
/// Python generates from `jain_observances/registry.py`.
library;

import 'dart:convert';

/// The registry document shape this engine understands; Python `registry_json.SCHEMA_VERSION`.
const int supportedRegistrySchema = 1;

/// Which moment of the civil day decides an observance's tithi.
enum DayRule {
  /// The Jain day-start, sunrise + 2 h 24 min. The default.
  udaya,

  /// Sunset, for night observances whose tithi can begin after the morning anchor.
  pradosh,
}

final class FestivalEntry {
  const FestivalEntry({
    required this.id,
    required this.ruleType,
    required this.category,
    required this.name,
    required this.nameHindi,
    required this.profiles,
    required this.jainMonth,
    required this.paksha,
    required this.tithi,
    required this.dayRule,
    required this.vriddhiRule,
    required this.originPullback,
  });

  final String id, ruleType, category, name, nameHindi;

  /// Profile ids, or `all` for every tradition.
  final List<String> profiles;

  /// The month as the registry stores it (Amanta naming); null when absent or empty.
  final String? jainMonth;
  final String? paksha;

  /// 1-15 within [paksha].
  final int? tithi;
  final DayRule dayRule;

  /// `second_day` where a festival overrides the first-day vriddhi default.
  final String? vriddhiRule;

  /// The opt-in Day-1 anchor (Python `_origin_pullback_day`).
  final bool originPullback;
}

final class FestivalRegistry {
  const FestivalRegistry(this.entries);

  /// Throws [FormatException] for another schema version or an unknown day rule,
  /// as Python fails at registry-load time.
  factory FestivalRegistry.fromJson(String json) {
    final document = jsonDecode(json) as Map<String, Object?>;
    final version = document['schema_version'];
    if (version != supportedRegistrySchema) {
      throw FormatException('festival registry has schema $version; this engine reads $supportedRegistrySchema.');
    }
    final festivals = (document['festivals']! as List<Object?>).cast<Map<String, Object?>>();
    return FestivalRegistry(List.unmodifiable(festivals.map(_entry)));
  }

  /// In registry order, which is the order rules run in.
  final List<FestivalEntry> entries;
}

FestivalEntry _entry(Map<String, Object?> f) {
  final id = f['id']! as String;
  final month = f['jain_month'] as String?;
  return FestivalEntry(
    id: id,
    ruleType: f['rule_type']! as String,
    category: f['category'] as String? ?? '',
    name: f['name']! as String,
    nameHindi: f['name_hindi'] as String? ?? '',
    profiles: List.unmodifiable((f['profiles']! as List<Object?>).cast<String>()),
    jainMonth: month == null || month.isEmpty ? null : month,
    paksha: f['paksha'] as String?,
    tithi: f['tithi'] as int?,
    dayRule: _dayRule(id, f['day_rule'] as String? ?? 'udaya'),
    vriddhiRule: f['vriddhi_rule'] as String?,
    originPullback: f['origin_pullback'] as bool? ?? false,
  );
}

DayRule _dayRule(String id, String name) => DayRule.values.firstWhere(
  (rule) => rule.name == name,
  orElse: () => throw FormatException("'$id': unknown day_rule '$name'; expected udaya or pradosh."),
);
