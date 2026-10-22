// L1 parity: sunrise, sunset and next sunrise for every day of every core
// location under both rules, against the Python engine (days.json.gz).
import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

/// The plan allows 10 s (plans/mobile-app-flutter.md §3); the engine achieves
/// hundredths, so guard that instead and catch small regressions early.
const toleranceSeconds = 0.1;

void main() {
  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final errors = <String, List<double>>{'sunrise': [], 'sunset': [], 'next_sunrise': []};
        for (final row in dayRows(loc.slug, rule.name)) {
          final date = CivilDate.parse(row['date']! as String);
          final anchor = civilDayAnchor(date, loc.timezone);
          final nextAnchor = civilDayAnchor(date.next(), loc.timezone);
          double seconds(double ours, String key) => (ours - (row[key]! as num).toDouble()) * 86400;

          errors['sunrise']!.add(seconds(sunrise(anchor, loc.lat, loc.lon, rule), 'sunrise'));
          errors['sunset']!.add(seconds(sunset(anchor, loc.lat, loc.lon, rule), 'sunset'));
          errors['next_sunrise']!
              .add(seconds(sunrise(nextAnchor, loc.lat, loc.lon, rule), 'next_sunrise'));
        }
        final worst = errors.entries.map((e) => '${e.key} ${maxAbs(e.value).toStringAsFixed(3)} s');
        print('${loc.slug} ${rule.name}: worst ${worst.join(', ')}');
        for (final MapEntry(:key, :value) in errors.entries) {
          expect(maxAbs(value), lessThan(toleranceSeconds), reason: '$key worst error (s)');
        }
      });
    }
  }
}
