/// One sunrise-to-sunrise day's muhurats, as the app's Muhurat section reads
/// them (Python `muhurat_day.py`). Every instant is a UT Julian Day; Rashis
/// are 0-based (0 = Mesha), nakshatras 1-based.
library;

import 'dart:math' as math;

import '../astro/angles.dart';
import '../astro/boundary.dart';
import 'day_elements.dart';
import 'day_yogas.dart' show Segment;
import 'elements.dart';

/// A window of the day, in UT Julian Days.
typedef JdWindow = ({double start, double end});

/// Part (1-8) of the daylight by weekday (0 = Sunday).
const _rahuKaalPart = [8, 2, 7, 5, 6, 4, 3];
const _yamagandaPart = [5, 4, 3, 2, 1, 7, 6];
const _gulikaPart = [7, 6, 5, 4, 3, 2, 1];

/// Abhijit is the 8th of the 15 daylight muhurtas.
const _abhijitPart = 8, _dayMuhurtas = 15;

/// Part [part] (1-based) of the daylight cut into [parts] equal pieces.
JdWindow daylightPart(double sunrise, double sunset, {required int part, required int parts}) {
  final length = (sunset - sunrise) / parts;
  final start = sunrise + (part - 1) * length;
  return (start: start, end: start + length);
}

JdWindow rahuKaal(double sunrise, double sunset, int vara) =>
    daylightPart(sunrise, sunset, part: _rahuKaalPart[vara], parts: 8);
JdWindow yamaganda(double sunrise, double sunset, int vara) =>
    daylightPart(sunrise, sunset, part: _yamagandaPart[vara], parts: 8);
JdWindow gulika(double sunrise, double sunset, int vara) =>
    daylightPart(sunrise, sunset, part: _gulikaPart[vara], parts: 8);
JdWindow abhijit(double sunrise, double sunset) =>
    daylightPart(sunrise, sunset, part: _abhijitPart, parts: _dayMuhurtas);

/// The Moon's Rashi counted from the birth Rashi gives Chandra Bal at these places.
const _chandraBalCounts = {1, 3, 6, 7, 10, 11};

/// The six birth Rashis with Chandra Bal while the Moon is in [moonRashi].
List<int> chandraBalRashis(int moonRashi) => [
  for (var birth = 0; birth < 12; birth++)
    if (_chandraBalCounts.contains((moonRashi - birth) % 12 + 1)) birth,
];

/// The Moon's Rashi until [endsAt] (null: past the next sunrise).
typedef JdChandraBal = ({int moonRashi, double? endsAt});

List<JdChandraBal> chandraBalSpans(double sunrise, double nextSunrise) {
  final first = moonRashiAt(sunrise);
  if (moonRashiAt(nextSunrise) == first) return [(moonRashi: first, endsAt: null)];
  return [(moonRashi: first, endsAt: moonRashiEnd(sunrise)), (moonRashi: (first + 1) % 12, endsAt: null)];
}

/// Where Agni (the havan fire) lives: only on Prithvi is a havan good.
enum AgniVaas {
  prithvi(isAuspicious: true),
  aakash(isAuspicious: false),
  patal(isAuspicious: false);

  const AgniVaas({required this.isAuspicious});

  final bool isAuspicious;
}

/// (tithi + weekday number (Sunday 1) + 1) mod 4: 0 or 3 Prithvi, 1 Aakash, 2 Patal.
AgniVaas agniVaasOf(int tithi, int vara) =>
    const [AgniVaas.prithvi, AgniVaas.aakash, AgniVaas.patal, AgniVaas.prithvi][(tithi + vara + 2) % 4];

/// Panchak: the Moon's sidereal longitude in 300°-360°.
const double _panchakStart = 300;

/// The Moon moves 11.7-15.4° a day.
const double _minMoonRate = 11;

/// A Panchak period lasts at most 60° / 11.7° a day, about 5.1 days.
const double _longestPanchakDays = 6;

/// Past a crossing, so the next search finds the one after it.
const double _nudgeDays = 30 / 86400;

bool _inPanchak(double jdUt) => siderealMoonLongitude(jdUt) >= _panchakStart;

/// The first instant after [jdUt] at which the Moon reaches sidereal [degrees].
double _moonReaches(double jdUt, double degrees) => nextAngleBoundary(
  jdUt,
  (t) => normalizeDegrees(siderealMoonLongitude(t) - degrees),
  360,
  minRate: _minMoonRate,
  maxRate: maxMoonRate,
);

JdWindow _panchakFrom(double entry) => (start: entry, end: _moonReaches(entry + _nudgeDays, 0));

/// Today's Panchak window and its whole period, or, with no window today,
/// the next period.
typedef JdPanchak = ({JdWindow? window, JdWindow? period, JdWindow? nextPeriod});

JdPanchak panchakOf(double sunrise, double nextSunrise) {
  final (atSunrise, atNextSunrise) = (_inPanchak(sunrise), _inPanchak(nextSunrise));
  if (!atSunrise && !atNextSunrise) {
    return (window: null, period: null, nextPeriod: _panchakFrom(_moonReaches(nextSunrise, _panchakStart)));
  }
  final period = _panchakFrom(
    _moonReaches(atSunrise ? sunrise - _longestPanchakDays : sunrise, _panchakStart),
  );
  return (
    window: (start: atSunrise ? sunrise : period.start, end: atNextSunrise ? nextSunrise : period.end),
    period: period,
    nextPeriod: null,
  );
}

/// Where Bhadra lives, from the Moon's Rashi: on Earth it harms.
enum BhadraResidence { earth, heaven, underworld }

BhadraResidence bhadraResidenceOf(int moonRashi) => switch (moonRashi) {
  3 || 4 || 10 || 11 => BhadraResidence.earth,
  0 || 1 || 2 || 7 => BhadraResidence.heaven,
  _ => BhadraResidence.underworld,
};

typedef JdBhadra = ({double start, double end, int moonRashi});

/// Vishti is the 8th karana of each seven-karana cycle (2-57); karana 1 is fixed.
bool _isVishti(int karana) => karana > 1 && (karana - 1) % 7 == 0;

/// The Vishti karana windows of the day, cut at the day's ends and at a
/// Moon Rashi change.
List<JdBhadra> bhadraOf(double sunrise, double nextSunrise) {
  final karanas = dayKaranas(sunrise, nextSunrise);
  return [
    for (final (k, karana) in karanas.indexed)
      if (_isVishti(karana.index))
        ..._splitAtRashiChange(
          k == 0 ? sunrise : karanas[k - 1].endsAt,
          math.min(karana.endsAt, nextSunrise),
        ),
  ];
}

List<JdBhadra> _splitAtRashiChange(double start, double end) {
  final rashi = moonRashiAt(start);
  if (moonRashiAt(end) == rashi) return [(start: start, end: end, moonRashi: rashi)];
  final change = moonRashiEnd(start);
  return [(start: start, end: change, moonRashi: rashi), (start: change, end: end, moonRashi: (rashi + 1) % 12)];
}

/// Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati: the junction nakshatras.
const _gandmoolNakshatras = {1, 9, 10, 18, 19, 27};

typedef JdGandmool = ({double start, double end, int nakshatra});

/// Each stay of the Moon in a Gandmool nakshatra within the day.
List<JdGandmool> gandmoolOf(List<Segment> nakshatras) => [
  for (final n in nakshatras)
    if (_gandmoolNakshatras.contains(n.index)) (start: n.start, end: n.end, nakshatra: n.index),
];
