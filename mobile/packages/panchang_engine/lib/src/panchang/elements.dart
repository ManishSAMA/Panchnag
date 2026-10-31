/// Tithi and nakshatra: which one holds at an instant, when it ends, and the
/// tithis of a sunrise-to-sunrise day (Python `panchang.py` /
/// `panchang_service._collect_all_tithis_in_day`).
library;

import 'dart:math' as math;

import '../astro/angles.dart';
import '../astro/boundary.dart';
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

int tithiAt(double jdUt) => tithiOf(_elongation(jdUt));

/// The tithi an elongation (degrees in [0, 360)) falls in.
int tithiOf(double elongation) => elongation ~/ _tithiWidth + 1;

int nakshatraAt(double jdUt) => nakshatraOf(_siderealMoon(jdUt));

/// The quarter (1-4) of the nakshatra holding at [jdUt] (Python `get_nakshatra_pada`).
int nakshatraPadaAt(double jdUt) => _siderealMoon(jdUt) ~/ (_nakshatraWidth / 4) % 4 + 1;

/// Moon − Sun elongation, degrees in [0, 360).
double elongation(double jdUt) => _elongation(jdUt);

/// Elongation grows 10-15° a day; these bounds leave a margin on both sides.
const double _minElongationRate = 9.5, _maxElongationRate = 16;

/// When the tithi holding at [jdUt] ends.
double tithiEnd(double jdUt) => nextAngleBoundary(jdUt, _elongation, _tithiWidth,
    minRate: _minElongationRate, maxRate: _maxElongationRate);

/// The elongation read at a UT Julian Day.
typedef ElongationReading = ({double jd, double elongation});

/// [tithiAt] for an instant after the reading [before] and, when given,
/// before the reading [after], each within a day of it. The elongation's
/// growth rate bounds where it can be at [jdUt]; when that range lies inside
/// one tithi, no Moon or Sun need be computed, otherwise it is read directly.
int tithiBetween(double jdUt, ElongationReading before, ElongationReading? after) {
  final sinceBefore = jdUt - before.jd;
  var low = before.elongation + _minElongationRate * sinceBefore;
  var high = before.elongation + _maxElongationRate * sinceBefore;
  if (after != null) {
    final afterUnwrapped = before.elongation + normalizeDegrees(after.elongation - before.elongation);
    final untilAfter = after.jd - jdUt;
    low = math.max(low, afterUnwrapped - _maxElongationRate * untilAfter);
    high = math.min(high, afterUnwrapped - _minElongationRate * untilAfter);
  }
  final first = (low / _tithiWidth).floor();
  return first == (high / _tithiWidth).floor() ? first % 30 + 1 : tithiAt(jdUt);
}

/// The Moon moves 11.7-15.4° a day; these bounds leave a margin on both sides.
const double _minMoonRate = 11;

/// Degrees a day the Moon never reaches.
const double maxMoonRate = 16;

/// When the nakshatra holding at [jdUt] ends.
double nakshatraEnd(double jdUt) =>
    nextAngleBoundary(jdUt, _siderealMoon, _nakshatraWidth, minRate: _minMoonRate, maxRate: maxMoonRate);

/// The Moon's sidereal longitude, degrees in [0, 360), as nakshatras are read.
double siderealMoonLongitude(double jdUt) => _siderealMoon(jdUt);

/// The nakshatra (1-27) a sidereal longitude falls in, and the longitude it starts at.
int nakshatraOf(double siderealLongitude) => siderealLongitude ~/ _nakshatraWidth + 1;
double nakshatraStart(int nakshatra) => (nakshatra - 1) * _nakshatraWidth;

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
