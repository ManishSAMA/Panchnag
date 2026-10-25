/// Tithi and nakshatra: which one holds at an instant, when it ends, and the
/// tithis of a sunrise-to-sunrise day (Python `panchang.py` /
/// `panchang_service._collect_all_tithis_in_day`).
library;

import '../astro/angles.dart';
import '../astro/moon.dart';
import '../astro/sidereal.dart';
import '../astro/sun.dart';

/// The Jain day starts 6 ghati (2 h 24 min) after sunrise.
const double jainTithiOffsetDays = 144 / 1440;

const double _tithiWidth = 12;
const double _nakshatraWidth = 360 / 27;

/// Moon − Sun. The ayanamsa cancels, so tropical and sidereal agree.
double _elongation(double jdUt) =>
    normalizeDegrees(moonApparentLongitude(jdUt) - sunApparent(jdUt).longitude);

double _siderealMoon(double jdUt) => siderealLongitude(moonApparentLongitude(jdUt), jdUt);

int tithiAt(double jdUt) => _elongation(jdUt) ~/ _tithiWidth + 1;

int nakshatraAt(double jdUt) => _siderealMoon(jdUt) ~/ _nakshatraWidth + 1;

/// When the tithi holding at [jdUt] ends. Elongation grows 10-15° a day.
double tithiEnd(double jdUt) =>
    _nextBoundary(jdUt, _elongation, _tithiWidth, minRate: 9.5, maxRate: 16);

/// When the nakshatra holding at [jdUt] ends. The Moon moves 11.7-15.4° a day.
double nakshatraEnd(double jdUt) =>
    _nextBoundary(jdUt, _siderealMoon, _nakshatraWidth, minRate: 11, maxRate: 16);

const double _toleranceDays = 1e-7; // about 0.01 s

/// First instant after [start] at which the steadily increasing [angle]
/// reaches the next multiple of [width] degrees.
double _nextBoundary(
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

/// A tithi in a day's list; [endsAt] is null when it lasts past the next sunrise.
final class DayTithi {
  const DayTithi({required this.index, required this.endsAt});

  final int index;
  final double? endsAt;
}

/// Python steps 30 s past each end before asking for the next tithi.
const double _nudgeDays = 30 / 86400;
const int _maxTithisPerDay = 10;

/// Every tithi from [sunrise] up to [nextSunrise], in order.
List<DayTithi> dayTithis(double sunrise, double nextSunrise) {
  final tithis = <DayTithi>[];
  var instant = sunrise;
  while (tithis.length < _maxTithisPerDay) {
    final index = tithiAt(instant);
    final end = tithiEnd(instant);
    if (end >= nextSunrise) return [...tithis, DayTithi(index: index, endsAt: null)];
    tithis.add(DayTithi(index: index, endsAt: end));
    instant = end + _nudgeDays;
  }
  throw StateError('More than $_maxTithisPerDay tithis between JD $sunrise and $nextSunrise.');
}
