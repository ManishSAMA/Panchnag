/// Apparent geocentric Sun from VSOP87D (Bretagnon & Francou 1988), with the
/// FK5 correction, nutation and aberration as in Meeus, Astronomical
/// Algorithms ch. 25 and 32.
library;

import 'dart:math' as math;

import '../time/delta_t.dart';
import 'angles.dart';
import 'nutation.dart';
import 'vsop87d_earth.g.dart';

/// Apparent position of the Sun of date. Angles in degrees, distance in AU.
final class SunPosition {
  const SunPosition({
    required this.longitude,
    required this.latitude,
    required this.distance,
    required this.rightAscension,
    required this.declination,
  });

  final double longitude;
  final double latitude;
  final double distance;
  final double rightAscension;
  final double declination;
}

/// Σ_k τ^k Σ A·cos(B + C·τ) for one VSOP87 coordinate.
double _vsop(List<List<(double, double, double)>> series, double tau) {
  var result = 0.0;
  var power = 1.0;
  for (final terms in series) {
    var sum = 0.0;
    for (final (a, b, c) in terms) {
      sum += a * math.cos(b + c * tau);
    }
    result += sum * power;
    power *= tau;
  }
  return result;
}

/// Aberration in longitude, arcseconds (Meeus 25, "higher accuracy").
double _aberrationArcsec(double tau, double distance) {
  double s(double a, double b, double c) => a * math.sin(radians(b + c * tau));
  final dailyMotion = 3548.330 +
      s(118.568, 87.5287, 359993.7286) +
      s(2.476, 85.0561, 719987.4571) +
      s(1.376, 27.8502, 4452671.1152) +
      s(0.119, 73.1375, 450368.8564) +
      s(0.114, 337.2264, 329644.6718) +
      s(0.086, 222.5400, 659289.3436) +
      s(0.078, 162.8136, 9224659.7915) +
      s(0.054, 82.5823, 1079981.1857) +
      s(0.052, 171.5189, 225184.4282) +
      s(0.034, 30.3214, 4092677.3866) +
      s(0.033, 119.8105, 337181.4711) +
      s(0.023, 247.5418, 299295.6151) +
      s(0.023, 325.1526, 315559.5560) +
      s(0.021, 155.1241, 675553.2846) +
      tau * (s(7.311, 333.4515, 359993.7286) + s(0.305, 330.9814, 719987.4571) + s(0.010, 328.5170, 1079981.1857)) +
      tau * tau * (s(0.309, 241.4518, 359993.7286) + s(0.021, 205.0482, 719987.4571) + s(0.004, 297.8610, 4452671.1152)) +
      tau * tau * tau * s(0.010, 154.7066, 359993.7286);
  return -0.005775518 * distance * dailyMotion;
}

SunPosition sunApparent(double jdUt) {
  final jdTT = terrestrialTime(jdUt);
  final tau = (jdTT - 2451545.0) / 365250;
  final t = tau * 10;
  final distance = _vsop(earthR, tau);
  // Heliocentric Earth -> geocentric Sun.
  final theta = normalizeDegrees(degrees(_vsop(earthL, tau)) + 180);
  final beta = -degrees(_vsop(earthB, tau));
  // FK5 frame correction (Meeus eq. 32.3).
  final lambdaPrime = radians(theta - 1.397 * t - 0.00031 * t * t);
  final fk5Longitude = (-0.09033 + 0.03916 * (math.cos(lambdaPrime) + math.sin(lambdaPrime)) * math.tan(radians(beta))) / 3600;
  final fk5Latitude = 0.03916 * (math.cos(lambdaPrime) - math.sin(lambdaPrime)) / 3600;
  final nut = nutation(jdTT);
  final longitude = normalizeDegrees(
      theta + fk5Longitude + nut.longitude + _aberrationArcsec(tau, distance) / 3600);
  final latitude = beta + fk5Latitude;
  final epsilon = radians(meanObliquity(jdTT) + nut.obliquity);
  final (lam, bet) = (radians(longitude), radians(latitude));
  final rightAscension = normalizeDegrees(degrees(math.atan2(
      math.sin(lam) * math.cos(epsilon) - math.tan(bet) * math.sin(epsilon), math.cos(lam))));
  final declination = degrees(math.asin(
      math.sin(bet) * math.cos(epsilon) + math.cos(bet) * math.sin(epsilon) * math.sin(lam)));
  return SunPosition(
    longitude: longitude,
    latitude: latitude,
    distance: distance,
    rightAscension: rightAscension,
    declination: declination,
  );
}
