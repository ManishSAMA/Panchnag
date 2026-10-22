/// Greenwich sidereal time, IAU 2006: Earth Rotation Angle plus the
/// precession polynomial (Capitaine et al. 2003), and the equation of the
/// equinoxes for apparent time. UT1 is taken as UT.
library;

import 'dart:math' as math;

import '../time/delta_t.dart';
import 'angles.dart';
import 'nutation.dart';

/// Earth Rotation Angle in degrees (IERS Conventions 2010, eq. 5.15).
double _earthRotationDegrees(double jdUt) {
  final days = jdUt - 2451545.0;
  return normalizeDegrees(360 * (0.7790572732640 + 0.00273781191135448 * days + days % 1));
}

/// Greenwich mean sidereal time in degrees.
double greenwichMeanSiderealDegrees(double jdUt) {
  final t = centuriesSinceJ2000(terrestrialTime(jdUt));
  final arcsec = 0.014506 +
      t * (4612.156534 + t * (1.3915817 + t * (-0.00000044 + t * (-0.000029956 + t * -0.0000000368))));
  return normalizeDegrees(_earthRotationDegrees(jdUt) + arcsec / 3600);
}

/// Greenwich apparent sidereal time in hours.
double greenwichApparentSiderealHours(double jdUt) {
  final jdTT = terrestrialTime(jdUt);
  final nut = nutation(jdTT);
  final epsilon = radians(meanObliquity(jdTT) + nut.obliquity);
  return normalizeDegrees(
          greenwichMeanSiderealDegrees(jdUt) + nut.longitude * math.cos(epsilon)) /
      15;
}
