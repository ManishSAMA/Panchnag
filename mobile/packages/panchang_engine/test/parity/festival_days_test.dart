// L3 parity of the readings festival rules choose days from: sunrise, Jain
// day-start and evening tithis, and the Amanta and Purnimanta months, for every
// core fixture day, against Python.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

const toleranceSeconds = 10.0;

/// Months do not depend on the location; name 2015-2041 once.
final spans = lunarMonthsBetween(2457357.5, 2466551.5 + 31);
final amanta = amantaLookup(spans);

void main() {
  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final mismatches = <String>[];
        final boundaryCases = <String>[];
        double jd(Object? v) => (v! as num).toDouble();

        final rows = {for (final row in dayRows(loc.slug, rule.name)) row['date']! as String: row};
        final years = {for (final date in rows.keys) int.parse(date.substring(0, 4))};
        final location = Location(lat: loc.lat, lon: loc.lon, timezone: loc.timezone);

        for (final year in years) {
          for (final day in festivalDays(location: location, year: year, sunriseRule: rule, amanta: amanta)) {
            final row = rows[day.date.iso];
            if (row == null || day.date.year != year) continue;

            final tithis = (row['tithi']! as List<Object?>).cast<Map<String, Object?>>();
            final ends = [for (final t in tithis) if (t['ends'] != null) jd(t['ends'])];
            final reference = jd((row['jain_tithi']! as Map<String, Object?>)['reference']);
            final sunset = jd(row['sunset']);
            final evening = tithis.firstWhere((t) => t['ends'] == null || jd(t['ends']) > sunset)['index'];
            final month = row['month_amanta']! as Map<String, Object?>;
            final purnimanta = row['month']! as Map<String, Object?>;

            // §3 boundary rule: a label may differ only when a transition that
            // decides it lies within tolerance of the instant it is read at.
            String? near(double instant, Iterable<double> transitions) {
              final gaps = [
                for (final t in transitions)
                  if ((t - instant).abs() * 86400 < toleranceSeconds) (t - instant) * 86400,
              ];
              return gaps.isEmpty ? null : '${gaps.first.toStringAsFixed(2)} s';
            }

            void check(String label, Object ours, Object? theirs, double instant, Iterable<double> transitions) {
              if (ours == theirs) return;
              final gap = near(instant, transitions);
              (gap != null ? boundaryCases : mismatches).add('${day.date} $label ours $ours python $theirs ${gap ?? ''}');
            }

            final ourEnds = [tithiEnd(day.sunrise - 1.2), tithiEnd(day.sunrise), tithiEnd(day.sunset - 0.5)];
            final newMoons = [for (final s in spans) s.start];
            check('sunrise', (day.sunrise - jd(row['sunrise'])).abs() * 86400 < toleranceSeconds, true, 0, const []);
            check('sunset', (day.sunset - sunset).abs() * 86400 < toleranceSeconds, true, 0, const []);
            check('sunrise tithi', day.sunriseTithi, tithis.first['index'], day.sunrise, [...ends, ...ourEnds]);
            check('jain tithi', day.jainTithi, (row['jain_tithi']! as Map<String, Object?>)['index'], reference,
                [...ends, ...ourEnds, tithiEnd(reference - 1.2)]);
            check('evening tithi', day.eveningTithi, evening, sunset, [...ends, ...ourEnds]);
            check('month', (day.month.index, day.month.isAdhika), (month['index'], month['is_adhika']), reference,
                newMoons);
            // Python's festival snapshots name a Krishna paksha from the next
            // Shukla day; the fixture's month uses get_purnimanta_month. Both
            // must agree, and a disagreement can only come from a label above.
            check('purnimanta month', (day.purnimantaMonth.index, day.purnimantaMonth.isAdhika),
                (purnimanta['index'], purnimanta['is_adhika']), reference, [...newMoons, ...ends, ...ourEnds]);
          }
        }

        print('${loc.slug} ${rule.name}: boundary cases ${boundaryCases.length} $boundaryCases');
        expect(mismatches, isEmpty);
      });
    }
  }
}
