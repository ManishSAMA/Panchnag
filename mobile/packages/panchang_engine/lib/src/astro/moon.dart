/// Apparent geocentric longitude of the Moon from ELP/MPP02 (Chapront &
/// Francou 2003), truncated for 2016-2040 (see elp_mpp02_longitude.g.dart).
library;

import 'dart:math' as math;

import '../time/delta_t.dart';
import 'angles.dart';
import 'elp_mpp02_longitude.g.dart';
import 'nutation.dart';

/// Mean longitude W1 of the Moon, radians (ELP/MPP02, fitted to DE405).
double _meanLongitude(double t) =>
    3.81034409083088 +
    t * (8399.68473007193 + t * (-3.31895204255009e-5 + t * (3.11024944910606e-8 + t * -2.03282376489228e-10)));

/// Precession from the J2000 ecliptic to the ecliptic of date, arcseconds.
double _precession(double t) =>
    t * ((5029.0966 - 0.29965) + t * (1.112 + t * (0.000077 + t * -0.00002353)));

/// Light-time (aberration) correction, degrees.
double _aberration(double t) => -0.00019524 - 0.00001059 * math.sin(radians(225 + 477198.9 * t));

double moonApparentLongitude(double jdUt) {
  final jdTT = terrestrialTime(jdUt);
  final t = centuriesSinceJ2000(jdTT);
  final powers = [1.0, t, t * t, t * t * t];
  var perturbations = 0.0;
  for (final (k, a, p0, p1, p2, p3, p4) in moonLongitudeTerms) {
    perturbations += powers[k] * a * math.sin(p0 + t * (p1 + t * (p2 + t * (p3 + t * p4))));
  }
  final trueLongitude =
      degrees(_meanLongitude(t)) + (perturbations + _precession(t)) / 3600;
  return normalizeDegrees(trueLongitude + nutation(jdTT).longitude + _aberration(t));
}
