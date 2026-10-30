// L4 parity: every festival occurrence (id, occurrence id, dates, status) of
// every ported rule type, for each core location, sunrise rule, year and
// Shwetambar profile, against Python. Rule types land one at a time
// (plans/mobile-phase5-festivals.md §5); fixture rows are attributed to their
// rule type by id (§6.4), and rows of types not yet ported are left out.
import 'dart:io';

import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/festivals.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

const toleranceDays = 10 / 86400;

/// Months do not depend on the location; name 2015-2041 once.
final amanta = amantaLookup(lunarMonthsBetween(2457357.5, 2466551.5 + 31));

final registry = FestivalRegistry.fromJson(File('../../../shared/festival_registry.json').readAsStringSync());

/// Rule types whose occurrences carry an id of their own rather than the
/// registry id, by the ids they emit. Filled in as each type is ported.
final Map<String, RegExp> emittedIds = {
  'BhaktambarVrat': RegExp(r'^bhaktambar_vrat_\d{4}_'),
};

String? ruleTypeOf(String id) {
  final entry = registry.entries.where((e) => e.id == id).firstOrNull;
  if (entry != null) return entry.ruleType;
  return emittedIds.entries.where((e) => e.value.hasMatch(id)).firstOrNull?.key;
}

String rowKey(Map<String, Object?> row) =>
    '${row['start_date']} ${row['occurrence_id']} id=${row['id']} end=${row['end_date']} ${row['status']}';

String occurrenceKey(FestivalOccurrence o) => '${o.start} ${o.occurrenceId} id=${o.id} end=${o.end} ${o.status}';

/// The keys of [from] not matched one for one in [other] (a multiset difference).
List<String> missing(List<String> from, List<String> other) {
  final unmatched = <String, int>{};
  for (final key in other) {
    unmatched.update(key, (n) => n + 1, ifAbsent: () => 1);
  }
  return [
    for (final key in from)
      if (unmatched.update(key, (n) => n - 1, ifAbsent: () => -1) < 0) key,
  ];
}

void main() {
  final ported = portedRuleTypes.toSet();

  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final location = Location(lat: loc.lat, lon: loc.lon, timezone: loc.timezone);
        final fixtures = {
          for (final profile in festivalProfiles)
            profile: readCoreFixture('${loc.slug}/${rule.name}/festivals.$profile.json.gz')['years']!
                as Map<String, Object?>,
        };
        final mismatches = <String>[];
        final boundaryCases = <String>[];
        var compared = 0;

        for (final year in fixtures.values.first.keys.map(int.parse)) {
          final days = festivalDays(location: location, year: year, sunriseRule: rule, amanta: amanta);

          // §6.6 boundary rule: a date may differ only when a reading near it
          // (sunrise, Jain day-start or evening tithi, or the month) lies within
          // 10 s of the transition that decides it.
          bool nearBoundary(String iso) {
            final date = CivilDate.parse(iso);
            for (final (i, d) in days.indexed) {
              if (d.date != date) continue;
              for (final near in days.sublist((i - 2).clamp(0, days.length), (i + 3).clamp(0, days.length))) {
                final reference = near.sunrise + jainTithiOffsetDays;
                for (final x in [near.sunrise, reference, near.sunset]) {
                  if (tithiAt(x - toleranceDays) != tithiAt(x + toleranceDays)) return true;
                }
                if (amanta(reference - toleranceDays) != amanta(reference + toleranceDays)) return true;
              }
            }
            return false;
          }

          for (final profile in festivalProfiles) {
            final rows = (fixtures[profile]!['$year']! as List<Object?>).cast<Map<String, Object?>>();
            final expected = [for (final row in rows) if (ported.contains(ruleTypeOf(row['id']! as String))) rowKey(row)];
            final ours = [
              for (final o in festivalsFromDays(days, year: year, profile: profile, registry: registry)) occurrenceKey(o),
            ];
            compared += expected.length;
            for (final (side, keys) in [('python only', missing(expected, ours)), ('dart only', missing(ours, expected))]) {
              for (final key in keys) {
                final line = '$profile $side: $key';
                (nearBoundary(key.substring(0, 10)) ? boundaryCases : mismatches).add(line);
              }
            }
          }
        }

        print('${loc.slug} ${rule.name}: compared $compared rows of $ported; '
            'boundary cases ${boundaryCases.length} $boundaryCases');
        expect(mismatches, isEmpty);
      });
    }
  }
}
