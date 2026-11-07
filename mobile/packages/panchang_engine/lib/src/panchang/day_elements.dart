/// Yoga, Karana, the Moon's and Sun's Rashi and the gata across a
/// sunrise-to-sunrise day, as the app's Panchang section reads them (Python
/// `day_elements.py`).
///
/// Rashis are 0-based (0 = Mesha … 11 = Meena); yoga 1-27 and karana 1-60 are
/// 1-based, as tithi and nakshatra are.
library;

import '../astro/angles.dart';
import '../astro/boundary.dart';
import '../astro/sidereal.dart';
import 'elements.dart';

/// An element and the UT Julian Day it ends at.
typedef Span = ({int index, double endsAt});

/// An element within a day; [endsAt] is null when it lasts past the next sunrise.
typedef DaySpan = ({int index, double? endsAt});

/// Python steps 30 s past each end before reading the next element.
const double _nudgeDays = 30 / 86400;

const double _yogaWidth = 360 / 27, _karanaWidth = 6, _rashiWidth = 30;

/// Sun + Moon grows 12.65-16.4° a day (the Moon 11.7-15.4, the Sun about 1).
const double _minYogaRate = 12, _maxYogaRate = 17.5;

/// Moon − Sun, as for tithis.
const double _minElongationRate = 9.5, _maxElongationRate = 16;
const double _minMoonRate = 11;

/// The Sun moves 0.95-1.02° a day.
const double _minSunRate = 0.9, _maxSunRate = 1.1;

double _yogaAngle(double jdUt) => normalizeDegrees(siderealSunLongitude(jdUt) + siderealMoonLongitude(jdUt));

int yogaAt(double jdUt) => _yogaAngle(jdUt) ~/ _yogaWidth + 1;
double yogaEnd(double jdUt) =>
    nextAngleBoundary(jdUt, _yogaAngle, _yogaWidth, minRate: _minYogaRate, maxRate: _maxYogaRate);

int karanaAt(double jdUt) => elongation(jdUt) ~/ _karanaWidth + 1;
double karanaEnd(double jdUt) =>
    nextAngleBoundary(jdUt, elongation, _karanaWidth, minRate: _minElongationRate, maxRate: _maxElongationRate);

int moonRashiAt(double jdUt) => siderealMoonLongitude(jdUt) ~/ _rashiWidth;
double moonRashiEnd(double jdUt) =>
    nextAngleBoundary(jdUt, siderealMoonLongitude, _rashiWidth, minRate: _minMoonRate, maxRate: maxMoonRate);

int sunRashiAt(double jdUt) => siderealSunLongitude(jdUt) ~/ _rashiWidth;
double _sunRashiEnd(double jdUt) =>
    nextAngleBoundary(jdUt, siderealSunLongitude, _rashiWidth, minRate: _minSunRate, maxRate: _maxSunRate);

/// The element holding at [start] and the one after it, each with its end.
List<Span> pairFrom(double start, int Function(double) at, double Function(double) end) {
  final first = (index: at(start), endsAt: end(start));
  final second = first.endsAt + _nudgeDays;
  return [first, (index: at(second), endsAt: end(second))];
}

/// Every Karana from [sunrise] up to and including the one holding at [nextSunrise].
List<Span> dayKaranas(double sunrise, double nextSunrise) {
  final karanas = <Span>[];
  var instant = sunrise;
  while (karanas.isEmpty || karanas.last.endsAt < nextSunrise) {
    final span = (index: karanaAt(instant), endsAt: karanaEnd(instant));
    karanas.add(span);
    instant = span.endsAt + _nudgeDays;
  }
  return karanas;
}

/// The Sun's Rashi, and on a Sankranti day the one it enters.
List<DaySpan> daySunRashis(double sunrise, double nextSunrise) {
  final first = sunRashiAt(sunrise);
  if (sunRashiAt(nextSunrise) == first) return [(index: first, endsAt: null)];
  return [(index: first, endsAt: _sunRashiEnd(sunrise)), (index: (first + 1) % 12, endsAt: null)];
}

/// The Rashi the Sun is in on the day ending at [nextSunrise], and how many
/// days it has been there: the day holding the Sankranti is day 1. The first
/// sunrise after the Sankranti ([sunriseAfter]) closes that day.
({int rashi, int day}) gataOf(double nextSunrise, {required double Function(double) sunriseAfter}) {
  final longitude = siderealSunLongitude(nextSunrise);
  // The Sun entered this Rashi longitude % 30 degrees ago, so at most this
  // many days ago; starting here, the next boundary is that entry.
  final start = nextSunrise - longitude % _rashiWidth / _minSunRate - 0.5;
  final sankranti = _sunRashiEnd(start);
  return (rashi: longitude ~/ _rashiWidth, day: (nextSunrise - sunriseAfter(sankranti)).round() + 1);
}
