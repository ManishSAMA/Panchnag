/// Nutation (IAU 2000B) and the obliquity of the ecliptic (IAU 2006).
library;

import 'dart:math' as math;

import 'angles.dart';
import 'nutation_iau2000b.g.dart';

/// Nutation in longitude (Δψ) and obliquity (Δε), in degrees.
final class Nutation {
  const Nutation({required this.longitude, required this.obliquity});

  final double longitude;
  final double obliquity;
}

// IAU 2000B coefficients are in units of 0.1 µas.
const double _unitToDegrees = 1 / (1e7 * 3600);

/// Delaunay arguments l, l', F, D, Ω in radians (IERS Conventions 2003, eq. 5.43).
(double, double, double, double, double) _delaunay(double t) {
  double arg(double c0, double c1, double c2, double c3, double c4) =>
      radians(normalizeDegrees((c0 + t * (c1 + t * (c2 + t * (c3 + t * c4)))) / 3600));
  return (
    arg(485868.249036, 1717915923.2178, 31.8792, 0.051635, -0.00024470),
    arg(1287104.79305, 129596581.0481, -0.5532, 0.000136, -0.00001149),
    arg(335779.526232, 1739527262.8478, -12.7512, -0.001037, 0.00000417),
    arg(1072260.70369, 1602961601.2090, -6.3706, 0.006593, -0.00003169),
    arg(450160.398036, -6962890.5431, 7.4722, 0.007702, -0.00005939),
  );
}

Nutation nutation(double jdTT) {
  final t = centuriesSinceJ2000(jdTT);
  final (l, lp, f, d, om) = _delaunay(t);
  var psi = 0.0;
  var eps = 0.0;
  for (final (nl, nlp, nf, nd, nom, ps, pst, pc, ec, ect, es) in nutationTerms) {
    final a = nl * l + nlp * lp + nf * f + nd * d + nom * om;
    final (sinA, cosA) = (math.sin(a), math.cos(a));
    psi += (ps + pst * t) * sinA + pc * cosA;
    eps += (ec + ect * t) * cosA + es * sinA;
  }
  return Nutation(longitude: psi * _unitToDegrees, obliquity: eps * _unitToDegrees);
}

/// Mean obliquity of the ecliptic, IAU 2006 (Capitaine et al. 2003), degrees.
double meanObliquity(double jdTT) {
  final t = centuriesSinceJ2000(jdTT);
  final arcsec = 84381.406 +
      t * (-46.836769 + t * (-0.0001831 + t * (0.00200340 + t * (-0.000000576 + t * -0.0000000434))));
  return arcsec / 3600;
}

double trueObliquity(double jdTT) => meanObliquity(jdTT) + nutation(jdTT).obliquity;
