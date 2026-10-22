/// Sunrise and sunset as the Python engine defines them (Swiss Ephemeris
/// `rise_trans`, searching forward from the civil-day anchor).
library;

import 'dart:math' as math;

import 'angles.dart';
import 'sidereal_time.dart';
import 'sun.dart';

enum SunriseRule {
  /// Upper limb on the horizon, with standard refraction.
  modern,

  /// Centre of the disc on the horizon, no refraction: the printed-panchang rule.
  traditional,
}

/// Horizon refraction Swiss Ephemeris applies for 1013.25 hPa and 15 °C.
/// Measured in the Phase 0 spike: one constant fits 45,660 city-days of
/// `rise_trans` to 0.19″ (mobile/spikes/astro_accuracy/REPORT.md).
const double _horizonRefractionDegrees = 33.447 / 60;

/// The Sun's angular radius at 1 AU, arcseconds.
const double _semidiameterAt1Au = 959.63;

/// The Sun's horizontal parallax at 1 AU, arcseconds. Swiss Ephemeris puts the
/// disc centre at 0° *topocentric* altitude for the traditional rule, which is
/// +parallax in the geocentric altitude computed here. (For the modern rule the
/// measured refraction constant already absorbs it.)
const double _parallaxAt1Au = 8.794;

double _altitude(double jdUt, double lat, double lon) {
  final sun = sunApparent(jdUt);
  final hourAngle = radians(greenwichApparentSiderealHours(jdUt) * 15 + lon - sun.rightAscension);
  final (phi, delta) = (radians(lat), radians(sun.declination));
  return degrees(math.asin(math.sin(phi) * math.sin(delta) +
      math.cos(phi) * math.cos(delta) * math.cos(hourAngle)));
}

/// Altitude of the disc centre at the instant the rule calls sunrise.
double _horizon(double jdUt, SunriseRule rule) => switch (rule) {
      SunriseRule.modern =>
        -(_horizonRefractionDegrees + _semidiameterAt1Au / sunApparent(jdUt).distance / 3600),
      SunriseRule.traditional => _parallaxAt1Au / sunApparent(jdUt).distance / 3600,
    };

const double _scanStepDays = 1 / 24;
const int _scanSteps = 26;
const double _toleranceDays = 1e-7; // about 0.01 s

/// First instant after [anchor] at which the Sun crosses the rule's horizon
/// going up ([rising]) or down. Throws [StateError] when it never does within
/// a day, as on a polar day or night.
double _crossing(double anchor, double lat, double lon, SunriseRule rule, {required bool rising}) {
  double above(double jd) => _altitude(jd, lat, lon) - _horizon(jd, rule);
  bool crossed(double before, double after) => rising ? before < 0 && after >= 0 : before > 0 && after <= 0;

  final estimate = _estimate(anchor, lat, lon, rule, rising: rising);
  if (estimate != null) {
    final (a, b) = (math.max(anchor, estimate - _bracketDays), estimate + _bracketDays);
    final (fa, fb) = (above(a), above(b));
    if (crossed(fa, fb)) return _refine(above, a, fa, b, fb);
  }

  var (t0, f0) = (anchor, above(anchor));
  for (var step = 1; step <= _scanSteps; step++) {
    final t1 = anchor + step * _scanStepDays;
    final f1 = above(t1);
    if (crossed(f0, f1)) return _refine(above, t0, f0, t1, f1);
    (t0, f0) = (t1, f1);
  }
  throw StateError('No ${rising ? 'sunrise' : 'sunset'} within a day of JD $anchor at ($lat, $lon).');
}

const double _bracketDays = 1 / 24;
const double _siderealDegreesPerDay = 360.98564736629;

/// Hour-angle estimate of the first crossing after [anchor], from the Sun's
/// position at the anchor; null when the Sun never reaches the horizon then.
double? _estimate(double anchor, double lat, double lon, SunriseRule rule, {required bool rising}) {
  final sun = sunApparent(anchor);
  final (phi, delta) = (radians(lat), radians(sun.declination));
  final cosH0 = (math.sin(radians(_horizon(anchor, rule))) - math.sin(phi) * math.sin(delta)) /
      (math.cos(phi) * math.cos(delta));
  if (cosH0.abs() > 1) return null;
  final h0 = degrees(math.acos(cosH0));
  final hourAngleNow = greenwichApparentSiderealHours(anchor) * 15 + lon - sun.rightAscension;
  final target = rising ? -h0 : h0;
  return anchor + normalizeDegrees(target - hourAngleNow) / _siderealDegreesPerDay;
}

/// Root of [f] in [a, b] by the Illinois variant of regula falsi.
double _refine(double Function(double) f, double a, double fa, double b, double fb) {
  var side = 0;
  while (b - a > _toleranceDays) {
    final c = (a * fb - b * fa) / (fb - fa);
    final fc = f(c);
    if (fc * fb > 0) {
      (b, fb) = (c, fc);
      if (side == -1) fa /= 2;
      side = -1;
    } else if (fa * fc > 0) {
      (a, fa) = (c, fc);
      if (side == 1) fb /= 2;
      side = 1;
    } else {
      return c;
    }
  }
  return (a + b) / 2;
}

/// First sunrise after [anchor] (a UT Julian Day), as a UT Julian Day.
double sunrise(double anchor, double lat, double lon, SunriseRule rule) =>
    _crossing(anchor, lat, lon, rule, rising: true);

/// First sunset after [anchor] (a UT Julian Day), as a UT Julian Day.
double sunset(double anchor, double lat, double lon, SunriseRule rule) =>
    _crossing(anchor, lat, lon, rule, rising: false);
