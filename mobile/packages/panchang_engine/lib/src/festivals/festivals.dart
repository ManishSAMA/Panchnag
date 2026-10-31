/// A year of festivals for one place and profile (Python
/// `festival_service.generate_jain_festivals`).
///
/// Design: python_engine/python_engine/plans/mobile-phase5-festivals.md.
library;

import '../astro/rise_set.dart';
import '../day.dart';
import '../time/civil_day.dart';
import 'days.dart';
import 'registry.dart';
import 'rules/anchored.dart';
import 'rules/bhaktambar.dart';
import 'rules/namokar.dart';
import 'rules/paryushan.dart';
import 'rules/pushpanjali.dart';
import 'rules/ravi_vrat.dart';
import 'rules/rohini.dart';
import 'single_tithi.dart';

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
  final days = festivalDays(location: location, year: year, sunriseRule: sunriseRule);
  return festivalsFromDays(days, year: year, profile: profile, registry: registry);
}

/// A rule type: the occurrences one registry entry resolves to over a year's window.
typedef FestivalRule = List<FestivalOccurrence> Function(FestivalEntry entry, List<FestivalDay> days, {required int year});

/// Rule types ported so far, by registry `rule_type`. The rest are skipped
/// until their parity passes (plans/mobile-phase5-festivals.md §5).
final Map<String, FestivalRule> _rules = {
  'SingleTithi': singleTithi,
  'BhaktambarVrat': bhaktambarVrat,
  'Namokar35Vrat': namokar35Vrat,
  'PushpanjaliVrat': pushpanjaliVrat,
  'RaviVrat': raviVratSundays,
  'ShvetambaraParyushan50Day': paryushan50Day,
  'LabdhiVidhanVrat': labdhiVidhanVrat,
  'RohiniVrat': rohiniVrat,
  ...anchoredRules,
};

Iterable<String> get portedRuleTypes => _rules.keys;

/// [festivalsOf] from readings already built, so a caller resolving several
/// profiles for one place and year builds them once.
List<FestivalOccurrence> festivalsFromDays(
  List<FestivalDay> days, {
  required int year,
  required String profile,
  required FestivalRegistry registry,
}) {
  final vratDays = vratView(days);
  final occurrences = [
    for (final entry in registry.entries)
      if (entry.profiles.contains(profile) || entry.profiles.contains('all'))
        if (_rules[entry.ruleType] case final rule?)
          ...rule(entry, takesSecondDayOfVriddhi(entry.id, entry.category) ? vratDays : days, year: year),
  ];
  // Rules may resolve into the window's neighbouring years; List.sort is not
  // stable, so the registry order of same-day festivals is kept by index.
  final inYear = [
    for (final o in occurrences)
      if (o.start.year == year) o,
  ];
  final order = {for (final (i, o) in inYear.indexed) o: i};
  return inYear..sort((a, b) {
    final byDate = a.start.compareTo(b.start);
    return byDate != 0 ? byDate : order[a]!.compareTo(order[b]!);
  });
}
