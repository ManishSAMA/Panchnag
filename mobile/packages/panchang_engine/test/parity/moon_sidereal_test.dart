// L1 parity: Moon, Lahiri ayanamsa and sidereal longitudes against Swiss
// Ephemeris, every day 2016-2040 at 0h UT (astro.json.gz).
import 'package:panchang_engine/src/astro/moon.dart';
import 'package:panchang_engine/src/astro/sidereal.dart';
import 'package:panchang_engine/src/astro/sun.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

void main() {
  final samples = astroSamples();
  double field(Map<String, Object?> s, String key) => (s[key]! as num).toDouble();
  double worst(double Function(Map<String, Object?>) ours, String key) =>
      maxAbs(samples.map((s) => angleDiffArcsec(ours(s), field(s, key))));

  test('Moon apparent longitude within 4″ (plan 15″)', () {
    expect(worst((s) => moonApparentLongitude(field(s, 'jd_ut')), 'moon_apparent'), lessThan(4));
  });

  test('Lahiri ayanamsa within 0.2″ (plan 1″)', () {
    expect(worst((s) => lahiriAyanamsa(field(s, 'jd_ut')), 'ayanamsa'), lessThan(0.2));
  });

  test('sidereal Sun within 0.5″', () {
    expect(
      worst((s) => siderealLongitude(sunApparent(field(s, 'jd_ut')).longitude, field(s, 'jd_ut')),
          'sun_sidereal'),
      lessThan(0.5),
    );
  });

  test('sidereal Moon within 4″', () {
    expect(
      worst((s) => siderealLongitude(moonApparentLongitude(field(s, 'jd_ut')), field(s, 'jd_ut')),
          'moon_sidereal'),
      lessThan(4),
    );
  });
}
