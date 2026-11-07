// Parity: PanchangEngine.section against Python's day_elements.py, on a
// sample of core days for every location and both rules.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

/// Coprime with 7, so the sample walks every weekday; about 150 days a location.
const stride = 61;
const toleranceSeconds = 10.0;

void main() {
  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final location = Location(lat: loc.lat, lon: loc.lon, timezone: loc.timezone);
        final mismatches = <String>[];
        double jd(Object? v) => (v! as num).toDouble();
        bool near(DateTime? ours, Object? theirs) =>
            ours == null && theirs == null ||
            ours != null && theirs != null && (julianDayFromUtc(ours) - jd(theirs)).abs() * 86400 <= toleranceSeconds;
        List<Map<String, Object?>> rows(Object? v) => (v! as List<Object?>).cast<Map<String, Object?>>();

        /// A list read from [readAt] may differ only when either engine's
        /// first element ends within tolerance of that instant.
        void spans(
          String what,
          String date,
          List<({int index, DateTime? endsAt})> ours,
          List<Map<String, Object?>> theirs,
          double readAt,
        ) {
          final same =
              ours.length == theirs.length &&
              [
                for (var k = 0; k < ours.length; k++)
                  ours[k].index == theirs[k]['index'] && near(ours[k].endsAt, theirs[k]['ends']),
              ].every((ok) => ok);
          if (same) return;
          bool atReadInstant(double? end) => end != null && (end - readAt).abs() * 86400 <= toleranceSeconds;
          final ourFirst = ours.first.endsAt == null ? null : julianDayFromUtc(ours.first.endsAt!);
          final theirFirst = theirs.first['ends'] == null ? null : jd(theirs.first['ends']);
          if (!atReadInstant(ourFirst) && !atReadInstant(theirFirst)) mismatches.add('$date $what');
        }

        final all = dayRows(loc.slug, rule.name);
        for (var i = 0; i < all.length; i += stride) {
          final row = all[i];
          final date = row['date']! as String;
          final sunrise = jd(row['sunrise']), nextSunrise = jd(row['next_sunrise']);
          final reference = jd((row['jain_tithi']! as Map<String, Object?>)['reference']);
          final section = const PanchangEngine().section(
            location: location,
            date: CivilDate.parse(date),
            sunriseRule: rule,
          );

          spans('next tithi', date, [section.nextTithi], [row['tithi_next']! as Map<String, Object?>], reference);
          spans(
            'next nakshatra',
            date,
            [section.nextNakshatra],
            [row['nakshatra_next']! as Map<String, Object?>],
            sunrise,
          );
          spans('yoga', date, section.yogas, rows(row['yoga']), sunrise);
          spans('karana', date, section.karanas, rows(row['karana']), sunrise);
          spans('moon rashi', date, section.moonRashis, rows(row['moon_rashi']), sunrise);
          spans('sun rashi', date, section.sunRashis, rows(row['sun_rashi']), nextSunrise);
          final gata = row['gata']! as Map<String, Object?>;
          if (section.gata != (rashi: gata['rashi'], day: gata['day'])) mismatches.add('$date gata');
        }

        expect(mismatches, isEmpty);
      });
    }
  }
}
