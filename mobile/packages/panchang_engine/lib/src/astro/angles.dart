/// Angle helpers shared by the astronomy modules.
library;

import 'dart:math' as math;

const double degPerRad = 180 / math.pi;

double radians(double degrees) => degrees / degPerRad;
double degrees(double radians) => radians * degPerRad;

/// [degrees] normalised to [0, 360).
double normalizeDegrees(double degrees) => (degrees % 360 + 360) % 360;

/// Julian centuries of TT since J2000.0.
double centuriesSinceJ2000(double jdTT) => (jdTT - 2451545.0) / 36525;
