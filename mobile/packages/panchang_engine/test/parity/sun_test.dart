// L1 parity: Sun, nutation and sidereal time against Swiss Ephemeris, every
// day 2016-2040 at 0h UT (test/fixtures/core/astro.json.gz).
import 'package:panchang_engine/src/astro/nutation.dart';
import 'package:panchang_engine/src/astro/sidereal_time.dart';
import 'package:panchang_engine/src/astro/sun.dart';
import 'package:panchang_engine/src/time/delta_t.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

void main() {
  final samples = astroSamples();
  double field(Map<String, Object?> s, String key) => (s[key]! as num).toDouble();

  test('ΔT matches the reference within 0.01 s', () {
    final worst = maxAbs(samples.map((s) => deltaTSeconds(field(s, 'jd_ut')) - field(s, 'delta_t')));
    expect(worst, lessThan(0.01));
  });

  test('nutation matches within 0.01″', () {
    final psi = samples.map((s) {
      final n = nutation(terrestrialTime(field(s, 'jd_ut')));
      return angleDiffArcsec(n.longitude, field(s, 'nutation_longitude'));
    });
    final eps = samples.map((s) {
      final n = nutation(terrestrialTime(field(s, 'jd_ut')));
      return angleDiffArcsec(n.obliquity, field(s, 'nutation_obliquity'));
    });
    expect(maxAbs(psi), lessThan(0.01));
    expect(maxAbs(eps), lessThan(0.01));
  });

  test('true obliquity matches within 0.05″', () {
    final worst = maxAbs(samples.map((s) => angleDiffArcsec(
        trueObliquity(terrestrialTime(field(s, 'jd_ut'))), field(s, 'true_obliquity'))));
    expect(worst, lessThan(0.05));
  });

  test('Sun apparent longitude matches within 0.5″ (plan tolerance 5″)', () {
    final worst = maxAbs(samples.map((s) =>
        angleDiffArcsec(sunApparent(field(s, 'jd_ut')).longitude, field(s, 'sun_apparent'))));
    expect(worst, lessThan(0.5));
  });

  test('Sun right ascension and declination match within 0.5″', () {
    final ra = samples.map((s) =>
        angleDiffArcsec(sunApparent(field(s, 'jd_ut')).rightAscension, field(s, 'sun_ra')));
    final dec = samples.map((s) =>
        angleDiffArcsec(sunApparent(field(s, 'jd_ut')).declination, field(s, 'sun_dec')));
    expect(maxAbs(ra), lessThan(0.5));
    expect(maxAbs(dec), lessThan(0.5));
  });

  test('Greenwich apparent sidereal time matches within 2 ms', () {
    final worst = maxAbs(samples.map((s) =>
        (greenwichApparentSiderealHours(field(s, 'jd_ut')) - field(s, 'gast_hours')) * 3600));
    expect(worst, lessThan(0.002));
  });
}
