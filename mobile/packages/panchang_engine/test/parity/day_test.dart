// Façade parity: PanchangEngine.day field by field against Python, on a
// sample of core days for every location and both rules. The layer parity
// tests check every day; this one checks the façade wires the layers right.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

/// Coprime with 7, so the sample walks every weekday; about 40 days a location.
const stride = 223;
const toleranceSeconds = 10.0;

void main() {
  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final location = Location(lat: loc.lat, lon: loc.lon, timezone: loc.timezone);
        final mismatches = <String>[];
        double jd(Object? v) => (v! as num).toDouble();
        void near(String what, DateTime? ours, Object? theirs, String date) {
          if (theirs == null && ours == null) return;
          if (theirs == null ||
              ours == null ||
              (julianDayFromUtc(ours) - jd(theirs)).abs() * 86400 > toleranceSeconds) {
            mismatches.add('$date $what');
          }
        }

        final rows = dayRows(loc.slug, rule.name);
        for (var i = 0; i < rows.length; i += stride) {
          final row = rows[i];
          final date = row['date']! as String;
          final day = const PanchangEngine().day(location: location, date: CivilDate.parse(date), sunriseRule: rule);
          final tithis = (row['tithi']! as List<Object?>).cast<Map<String, Object?>>();
          final jain = row['jain_tithi']! as Map<String, Object?>;
          final nakshatra = row['nakshatra']! as Map<String, Object?>;
          final month = row['month']! as Map<String, Object?>;

          near('sunrise', day.sunrise, row['sunrise'], date);
          near('sunset', day.sunset, row['sunset'], date);
          near('next sunrise', day.nextSunrise, row['next_sunrise'], date);
          if (day.tithis.map((t) => t.index).toString() != tithis.map((t) => t['index']).toString()) {
            mismatches.add('$date tithis');
          } else {
            for (final (k, t) in day.tithis.indexed) {
              near('tithi ${t.index} end', t.endsAt, tithis[k]['ends'], date);
            }
          }
          if (day.jainTithi.index != jain['index']) mismatches.add('$date jain tithi');
          near('jain tithi end', day.jainTithi.endsAt, jain['ends'], date);
          near('reference', day.jainTithi.reference, jain['reference'], date);
          if (day.nakshatra.index != nakshatra['index']) mismatches.add('$date nakshatra');
          near('nakshatra end', day.nakshatra.endsAt, nakshatra['ends'], date);
          if (day.vara != row['vara']) mismatches.add('$date vara');
          if ((day.month.index, day.month.isAdhika) != (month['index'], month['is_adhika'])) {
            mismatches.add('$date month');
          }
          if ((day.vikramSamvat, day.viraNirvanaSamvat) != (row['vikram_samvat'], row['vira_nirvana_samvat'])) {
            mismatches.add('$date samvat');
          }
          final names = day.choghadiya.map((c) => '${c.name.name[0].toUpperCase()}${c.name.name.substring(1)}');
          if (names.toList().toString() != row['choghadiya'].toString()) mismatches.add('$date choghadiya');
        }

        expect(mismatches, isEmpty);
      });
    }
  }
}
