// L4 parity: the vara and the 16 choghadiya names of every core fixture day,
// against Python. Each row's own sunrise, sunset and next sunrise feed the
// slots, so the names must match exactly.
import 'package:panchang_engine/src/panchang/choghadiya.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

String pythonName(Choghadiya c) => '${c.name[0].toUpperCase()}${c.name.substring(1)}';

void main() {
  for (final loc in coreLocations()) {
    for (final rule in ['modern', 'traditional']) {
      test('${loc.slug} $rule', () {
        final mismatches = <String>[];
        double jd(Object? v) => (v! as num).toDouble();

        for (final row in dayRows(loc.slug, rule)) {
          final date = CivilDate.parse(row['date']! as String);
          if (date.vara != row['vara']) mismatches.add('${row['date']} vara');
          final names = choghadiyaSlots(
            sunrise: jd(row['sunrise']),
            sunset: jd(row['sunset']),
            nextSunrise: jd(row['next_sunrise']),
            vara: date.vara,
          ).map((s) => pythonName(s.name)).toList();
          if (names.toString() != row['choghadiya'].toString()) mismatches.add('${row['date']} choghadiya');
        }

        expect(mismatches, isEmpty);
      });
    }
  }
}
