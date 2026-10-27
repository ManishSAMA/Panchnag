/// Vikram Samvat and Vira Nirvana Samvat, and the two new-year days they turn
/// over on (Python `panchang.py` `find_chaitra_shukla_1`, `find_diwali`,
/// `_tithi_owns_civil_day`, `get_vikram_samvat`, `get_vira_nirvana_samvat`).
library;

import 'dart:math' as math;

import '../astro/rise_set.dart';
import '../astro/sidereal.dart';
import '../panchang/elements.dart';
import '../time/civil_day.dart';
import '../time/julian_day.dart';

CivilDate _plusDays(CivilDate date, int days) {
  final shifted = DateTime.utc(date.year, date.month, date.day + days);
  return CivilDate(shifted.year, shifted.month, shifted.day);
}

/// Sunrise of [date], searched from local midnight on a fixed [utcOffset].
/// Python searches a whole window on the offset of the day being computed,
/// not of each day in the window.
double _sunriseOf(
  CivilDate date, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) {
  final midnight = DateTime.utc(date.year, date.month, date.day).subtract(utcOffset);
  return sunrise(julianDayFromUtc(midnight), lat, lon, rule);
}

/// The tithi that owns [date]: the one prevailing 6 ghati after its sunrise.
int prevailingTithi(
  CivilDate date, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) => tithiAt(_sunriseOf(date, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule) + jainTithiOffsetDays);

/// The elongation grows at most 16° in the day between two reference instants
/// (plus a few minutes of sunrise drift), so a day's tithi index runs at most
/// this far ahead of the day before.
const double _maxTithisPerDay = 1.4;

/// The first of [days] days from [from] owned by [target], counting a kshaya
/// [target] as merged onto the preceding tithi's day, that [accept] takes.
/// Days whose tithi cannot yet have reached [target]'s predecessor are skipped.
CivilDate? _firstOwned(
  CivilDate from,
  int days,
  int target, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
  bool Function(double reference) accept = _any,
}) {
  final references = <int, double>{};
  double referenceOf(int i) => references[i] ??=
      _sunriseOf(_plusDays(from, i), lat: lat, lon: lon, utcOffset: utcOffset, rule: rule) + jainTithiOffsetDays;
  final predecessor = (target - 2) % 30 + 1;

  for (var i = 0; i < days;) {
    final today = tithiAt(referenceOf(i));
    final owns = today == target || (today == predecessor && tithiAt(referenceOf(i + 1)) == target % 30 + 1);
    if (owns && accept(referenceOf(i))) return _plusDays(from, i);
    final ahead = (predecessor - today) % 30;
    i += math.max(1, (ahead - 1) ~/ _maxTithisPerDay);
  }
  return null;
}

bool _any(double reference) => true;

const int _amavasya = 30;

/// Chaitra Shukla Pratipada of [year]: the day after the first day owned by
/// an Amavasya between 1 March and 21 April (the Phalguna Amavasya).
CivilDate chaitraShuklaPratipada(
  int year, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) =>
    _firstOwned(CivilDate(year, 3, 1), 52, _amavasya, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule)?.next() ??
    (throw StateError('No Phalguna Amavasya between 1 March and 21 April $year.'));

/// The Sun is past 179° sidereal only from the Kartika Amavasya on; the Ashwin
/// one before it peaks near 178°.
const double _kartikaSunLongitude = 179;

/// Diwali (Kartika Krishna Amavasya) of [year]: the first day between 10 Oct
/// and 24 Nov owned by an Amavasya, with the Sun past 179° at its 6-ghati mark.
CivilDate diwali(
  int year, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) =>
    _firstOwned(
      CivilDate(year, 10, 10),
      46,
      _amavasya,
      lat: lat,
      lon: lon,
      utcOffset: utcOffset,
      rule: rule,
      accept: (reference) => siderealSunLongitude(reference) >= _kartikaSunLongitude,
    ) ??
    (throw StateError('No Kartika Amavasya between 10 October and 24 November $year.'));

/// Vikram Samvat on [date]: Gregorian year + 57 from Chaitra Shukla Pratipada on.
int vikramSamvat(CivilDate date, {required CivilDate chaitraShukla1}) =>
    date.compareTo(chaitraShukla1) >= 0 ? date.year + 57 : date.year + 56;

/// Vira Nirvana Samvat on [date]: Gregorian year + 527 from the day after Diwali.
int viraNirvanaSamvat(CivilDate date, {required CivilDate diwali}) =>
    date.compareTo(diwali) > 0 ? date.year + 527 : date.year + 526;

/// [chaitraShuklaPratipada] falls from 2 March to 22 April and [diwali] from
/// 10 October to 24 November, so a day outside those windows needs no search.
({int vikram, int viraNirvana}) samvatsOn(
  CivilDate date, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) {
  final year = date.year;
  final vikram = switch (date) {
    _ when date.compareTo(CivilDate(year, 3, 2)) < 0 => year + 56,
    _ when date.compareTo(CivilDate(year, 4, 22)) >= 0 => year + 57,
    _ => vikramSamvat(
      date,
      chaitraShukla1: chaitraShuklaPratipada(year, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule),
    ),
  };
  final viraNirvana = switch (date) {
    _ when date.compareTo(CivilDate(year, 10, 10)) <= 0 => year + 526,
    _ when date.compareTo(CivilDate(year, 11, 24)) > 0 => year + 527,
    _ => viraNirvanaSamvat(
      date,
      diwali: diwali(year, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule),
    ),
  };
  return (vikram: vikram, viraNirvana: viraNirvana);
}
