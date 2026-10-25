// L2/L3 parity: the day's tithis, Jain tithi and nakshatra (indices exact,
// end times within tolerance) for every core fixture day, against Python.
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

/// Plan allows 60 s for transition instants. The Phase 0 spike measured 6 s
/// worst; Python's bisection alone is up to 0.86 s late. Guard 10 s.
const toleranceSeconds = 10.0;

void main() {
  for (final loc in coreLocations()) {
    for (final rule in ['modern', 'traditional']) {
      test('${loc.slug} $rule', () {
        final timeErrors = <double>[];
        final labelMismatches = <String>[];
        final boundaryCases = <String>[];
        double jd(Object? v) => (v! as num).toDouble();

        for (final row in dayRows(loc.slug, rule)) {
          final sunrise = jd(row['sunrise']), nextSunrise = jd(row['next_sunrise']);
          final expectedTithis = (row['tithi']! as List<Object?>).cast<Map<String, Object?>>();
          final jain = row['jain_tithi']! as Map<String, Object?>;
          final nak = row['nakshatra']! as Map<String, Object?>;

          // §3 boundary rule: a label may differ only when either engine's
          // transition lies within tolerance of the instant the label is read
          // at. The deciding transition is often one the row never records
          // (the label that ended just before sunrise), so ours count too.
          String? nearTransition(double instant, Iterable<double?> transitions) {
            final gaps = [
              for (final t in transitions)
                if (t != null && (t - instant).abs() * 86400 < toleranceSeconds) (t - instant) * 86400,
            ];
            return gaps.isEmpty ? null : '${gaps.first.toStringAsFixed(2)} s';
          }
          final tithiEnds = expectedTithis.map((t) => t['ends'] == null ? null : jd(t['ends']));

          final ours = dayTithis(sunrise, nextSunrise);
          final sameTithis = ours.map((t) => t.index).toList().toString() ==
              expectedTithis.map((t) => t['index']).toList().toString();
          if (!sameTithis) {
            final allEnds = [...tithiEnds, ...ours.map((t) => t.endsAt), tithiEnd(sunrise - 0.5)];
            final gap = nearTransition(sunrise, allEnds) ?? nearTransition(nextSunrise, allEnds);
            (gap != null ? boundaryCases : labelMismatches).add('${row['date']} tithis ${gap ?? ''}');
          } else {
            for (var i = 0; i < ours.length; i++) {
              final expectedEnd = expectedTithis[i]['ends'];
              if (expectedEnd != null) timeErrors.add((ours[i].endsAt! - jd(expectedEnd)) * 86400);
            }
          }

          final reference = sunrise + jainTithiOffsetDays;
          if (tithiAt(reference) != jain['index']) {
            final gap = nearTransition(
                reference, [jd(jain['ends']), tithiEnd(reference), tithiEnd(reference - 0.5)]);
            (gap != null ? boundaryCases : labelMismatches).add('${row['date']} jain tithi ${gap ?? ''}');
          } else {
            timeErrors.add((tithiEnd(reference) - jd(jain['ends'])) * 86400);
          }

          if (nakshatraAt(sunrise) != nak['index']) {
            final gap = nearTransition(
                sunrise, [jd(nak['ends']), nakshatraEnd(sunrise), nakshatraEnd(sunrise - 0.5)]);
            (gap != null ? boundaryCases : labelMismatches).add('${row['date']} nakshatra ${gap ?? ''}');
          } else {
            timeErrors.add((nakshatraEnd(sunrise) - jd(nak['ends'])) * 86400);
          }
        }

        print('${loc.slug} $rule: worst end time ${maxAbs(timeErrors).toStringAsFixed(2)} s, '
            'boundary cases ${boundaryCases.length} $boundaryCases');
        expect(labelMismatches, isEmpty);
        expect(maxAbs(timeErrors), lessThan(toleranceSeconds));
      });
    }
  }
}
