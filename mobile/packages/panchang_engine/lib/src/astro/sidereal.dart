/// Lahiri ayanamsa and sidereal (nirayana) longitudes as the Python engine
/// computes them with Swiss Ephemeris `FLG_SIDEREAL`.
library;

import '../time/delta_t.dart';
import 'angles.dart';
import 'nutation.dart';
import 'sun.dart';

/// Lahiri (Indian Calendar Reform Committee): 23°15′00.658″ on the 1956
/// equinox epoch as Swiss Ephemeris defines SIDM_LAHIRI.
const double _lahiriEpochJd = 2435553.5;
const double _lahiriAtEpoch = 23.250182778 - 0.004658035;

/// General precession in longitude since J2000, arcseconds (IAU 2006, Capitaine et al. 2003).
double _precessionArcsec(double jdTT) {
  final t = centuriesSinceJ2000(jdTT);
  return t * (5028.796195 + t * (1.1054348 + t * (0.00007964 + t * -0.000023857)));
}

/// Mean Lahiri ayanamsa (no nutation), degrees.
double lahiriAyanamsa(double jdUt) =>
    _lahiriAtEpoch + (_precessionArcsec(terrestrialTime(jdUt)) - _precessionArcsec(_lahiriEpochJd)) / 3600;

/// Sidereal longitude from an apparent tropical one: Swiss Ephemeris
/// FLG_SIDEREAL measures from the mean equinox, so nutation is removed too.
double siderealLongitude(double tropicalApparent, double jdUt) => normalizeDegrees(
    tropicalApparent - nutation(terrestrialTime(jdUt)).longitude - lahiriAyanamsa(jdUt));

/// The Sun's sidereal apparent longitude (Python `get_planetary_longitude(jd, 'Sun')`).
double siderealSunLongitude(double jdUt) => siderealLongitude(sunApparent(jdUt).longitude, jdUt);
