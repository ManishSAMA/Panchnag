// L3 parity: the Purnimanta and Amanta month (index and Adhik flag, exact) at
// the Jain reference instant, for every core fixture day, against Python.
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

const toleranceSeconds = 10.0;

/// The fixtures span 2016-2040, and a Krishna paksha looks up to 17 days
/// ahead. Months do not depend on the location.
final spans = lunarMonthsBetween(2457388.5, 2466520.5 + 31);
final amanta = amantaLookup(spans);

void main() {
  for (final loc in coreLocations()) {
    for (final rule in ['modern', 'traditional']) {
      test('${loc.slug} $rule', () {
        final mismatches = <String>[];
        final boundaryCases = <String>[];

        // A month label may differ only when the reference instant sits within
        // tolerance of the transition that decides it: a new moon (both systems)
        // or the end of Purnima (Purnimanta).
        String? nearTransition(double instant) {
          final transitions = [
            for (final span in spans) span.start,
            tithiEnd(instant - 0.5),
            tithiEnd(instant),
          ];
          final near = transitions.where((t) => (t - instant).abs() * 86400 < toleranceSeconds);
          return near.isEmpty ? null : '${((near.first - instant) * 86400).toStringAsFixed(2)} s';
        }

        void compare(String label, String date, double reference, LunarMonth ours, Map<String, Object?> theirs) {
          if (ours.index == theirs['index'] && ours.isAdhika == theirs['is_adhika']) return;
          final gap = nearTransition(reference);
          (gap != null ? boundaryCases : mismatches)
              .add('$date $label ours ${ours.name} python ${theirs['name']} ${gap ?? ''}');
        }

        for (final row in dayRows(loc.slug, rule)) {
          final reference = ((row['jain_tithi']! as Map<String, Object?>)['reference']! as num).toDouble();
          final date = row['date']! as String;
          compare('purnimanta', date, reference, purnimantaMonth(reference, amanta: amanta),
              row['month']! as Map<String, Object?>);
          compare('amanta', date, reference, amanta(reference), row['month_amanta']! as Map<String, Object?>);
        }

        print('${loc.slug} $rule: boundary cases ${boundaryCases.length} $boundaryCases');
        expect(mismatches, isEmpty);
      });
    }
  }
}
