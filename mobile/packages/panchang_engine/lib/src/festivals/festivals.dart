/// A year of festivals for one place and profile (Python
/// `festival_service.generate_jain_festivals`).
///
/// Design: python_engine/python_engine/plans/mobile-phase5-festivals.md.
library;

import '../astro/rise_set.dart';
import '../day.dart';
import '../time/civil_day.dart';
import 'registry.dart';

/// The profiles the app offers. Stored as open string ids, so Digambar can be
/// added later without a migration (plans/mobile-app-flutter.md §1a).
const List<String> festivalProfiles = [
  'shwetambar_murtipujak_tapagachchha',
  'shwetambar_sthanakvasi',
  'shwetambar_terapanthi',
];

final class FestivalOccurrence {
  const FestivalOccurrence({
    required this.id,
    required this.occurrenceId,
    required this.ruleId,
    required this.category,
    required this.name,
    required this.nameHindi,
    required this.start,
    required this.end,
    this.status = 'confirmed',
  });

  /// The observance's id; a rule emitting several events gives each its own.
  final String id;

  /// Unique within a year's list.
  final String occurrenceId;

  /// The registry entry that produced it.
  final String ruleId;
  final String category;

  /// The registry entry's names (event titles come in Phase 6).
  final String name, nameHindi;
  final CivilDate start, end;
  final String status;
}

List<FestivalOccurrence> festivalsOf({
  required Location location,
  required int year,
  required String profile,
  required FestivalRegistry registry,
  required SunriseRule sunriseRule,
}) {
  if (!festivalProfiles.contains(profile)) {
    throw ArgumentError.value(profile, 'profile', 'must be one of ${festivalProfiles.join(', ')}');
  }
  return const [];
}
