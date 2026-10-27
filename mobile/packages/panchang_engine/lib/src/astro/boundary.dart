/// Finding the instant a steadily increasing angle reaches its next boundary:
/// tithi and nakshatra ends, new moons, Sankrantis.
library;

const double _toleranceDays = 1e-7; // about 0.01 s

/// First instant after [start] at which the steadily increasing [angle]
/// reaches the next multiple of [width] degrees. [minRate] and [maxRate]
/// bound how fast the angle grows, in degrees per day.
double nextAngleBoundary(
  double start,
  double Function(double) angle,
  double width, {
  required double minRate,
  required double maxRate,
}) {
  final initial = angle(start);
  final remaining = width - initial % width;
  final boundary = initial + remaining;
  double beyond(double jd) => (angle(jd) - boundary + 540) % 360 - 180;

  var (lo, hi) = (start + remaining / maxRate, start + remaining / minRate);
  var (fLo, fHi) = (beyond(lo), beyond(hi));
  if (fLo >= 0) (lo, fLo) = (start, -remaining);
  if (fHi <= 0) throw StateError('No boundary within ${hi - start} days of JD $start.');

  var side = 0;
  while (hi - lo > _toleranceDays) {
    final mid = (lo * fHi - hi * fLo) / (fHi - fLo);
    final fMid = beyond(mid);
    if (fMid > 0) {
      (hi, fHi) = (mid, fMid);
      if (side == -1) fLo /= 2;
      side = -1;
    } else if (fMid < 0) {
      (lo, fLo) = (mid, fMid);
      if (side == 1) fHi /= 2;
      side = 1;
    } else {
      return mid;
    }
  }
  return (lo + hi) / 2;
}
