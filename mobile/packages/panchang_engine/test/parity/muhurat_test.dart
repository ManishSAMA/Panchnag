// Parity: PanchangEngine.muhurat against Python's muhurat_day.py, on a
// sample of core days for every location and both rules.
import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/time/julian_day.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

/// Coprime with 7, so the sample walks every weekday; about 150 days a location.
const stride = 61;
const toleranceSeconds = 10.0;

typedef Row = Map<String, Object?>;

double jd(Object? v) => (v! as num).toDouble();
Row map(Object? v) => v! as Row;
List<Row> rows(Object? v) => (v! as List<Object?>).cast<Row>();

bool near(DateTime? ours, Object? theirs) =>
    ours == null && theirs == null ||
    ours != null && theirs != null && (julianDayFromUtc(ours) - jd(theirs)).abs() * 86400 <= toleranceSeconds;

bool sameWindow(TimeWindow? ours, Object? theirs) =>
    ours == null && theirs == null ||
    ours != null && theirs != null && near(ours.start, map(theirs)['start_jd']) && near(ours.end, map(theirs)['end_jd']);

/// Windows from both engines agree one for one, leaving out any shorter
/// than the tolerance: a boundary within it of a sunrise may make a sliver
/// on one side only.
bool sameWindows<T>(
  List<T> ours,
  List<Row> theirs, {
  required TimeWindow Function(T) window,
  required bool Function(T, Row) sameLabel,
}) {
  bool long(double start, double end) => (end - start) * 86400 > toleranceSeconds;
  final o = [for (final w in ours) if (long(julianDayFromUtc(window(w).start), julianDayFromUtc(window(w).end))) w];
  final t = [for (final r in theirs) if (long(jd(r['start_jd']), jd(r['end_jd']))) r];
  return o.length == t.length &&
      [
        for (var k = 0; k < o.length; k++) sameWindow(window(o[k]), t[k]) && sameLabel(o[k], t[k]),
      ].every((ok) => ok);
}

void main() {
  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final location = Location(lat: loc.lat, lon: loc.lon, timezone: loc.timezone);
        final mismatches = <String>[];
        final all = dayRows(loc.slug, rule.name);
        for (var i = 0; i < all.length; i += stride) {
          final row = all[i];
          final date = row['date']! as String;
          final sunrise = jd(row['sunrise']);
          final theirs = map(row['muhurat']);
          final ours = const PanchangEngine().muhurat(location: location, date: CivilDate.parse(date), sunriseRule: rule);
          void check(String what, bool ok) {
            if (!ok) mismatches.add('$date $what');
          }

          check('rahu kaal', sameWindow(ours.rahuKaal, theirs['rahu_kaal']));
          check('yamaganda', sameWindow(ours.yamaganda, theirs['yamaganda']));
          check('gulika', sameWindow(ours.gulika, theirs['gulika']));
          check('abhijit', sameWindow(ours.abhijit, theirs['abhijit']));

          final panchak = map(theirs['panchak']);
          check('panchak window', sameWindow(ours.panchak.window, panchak['window']));
          check('panchak period', sameWindow(ours.panchak.period, panchak['period']));
          check('panchak next', sameWindow(ours.panchak.nextPeriod, panchak['next_period']));

          check(
            'bhadra',
            sameWindows(
              ours.bhadra,
              rows(theirs['bhadra']),
              window: (b) => (start: b.start, end: b.end),
              sameLabel: (b, r) =>
                  b.moonRashi == r['moon_rashi'] && b.residence.name == (r['residence']! as String).toLowerCase(),
            ),
          );
          check(
            'gandmool',
            sameWindows(
              ours.gandmool,
              rows(theirs['gandmool']),
              window: (g) => (start: g.start, end: g.end),
              sameLabel: (g, r) => g.nakshatra == r['nakshatra'],
            ),
          );

          check(
            'yogas',
            sameWindows(
              ours.yogas,
              rows(theirs['yogas']),
              window: (y) => (start: y.start, end: y.end),
              sameLabel: (y, r) =>
                  y.kind.name == r['kind'] &&
                  y.name == r['name'] &&
                  y.nature.name == r['nature'] &&
                  y.isNullified == r['is_nullified'] &&
                  y.cancelled == r['cancelled'] &&
                  y.diminished == r['diminished'] &&
                  sameWindow(y.varjya, r['varjya']),
            ),
          );

          final chandraBal = rows(theirs['chandra_bal']);
          check(
            'chandra bal',
            ours.chandraBal.length == chandraBal.length &&
                [
                  for (var k = 0; k < chandraBal.length; k++)
                    ours.chandraBal[k].moonRashi == chandraBal[k]['moon_rashi'] &&
                        near(ours.chandraBal[k].endsAt, chandraBal[k]['ends_jd']) &&
                        ours.chandraBal[k].rashis.join(',') == (chandraBal[k]['rashis']! as List<Object?>).join(','),
                ].every((ok) => ok),
          );

          final agni = map(theirs['agni_vaas']);
          // The tithi at sunrise decides it, so a tithi end within tolerance
          // of sunrise may flip it in either engine.
          final tithiEnd = rows(row['tithi']).first['ends'];
          final tithiAtSunrise = tithiEnd != null && (jd(tithiEnd) - sunrise).abs() * 86400 <= toleranceSeconds;
          check(
            'agni vaas',
            tithiAtSunrise ||
                ours.agniVaas.name == (agni['residence']! as String).toLowerCase() &&
                    ours.agniVaas.isAuspicious == agni['is_auspicious'],
          );
        }
        expect(mismatches, isEmpty);
      });
    }
  }
}
