/// Vikram Samvat and Vira Nirvana Samvat, and the two new-year days they turn
/// over on (Python `panchang.py` `find_chaitra_shukla_1`, `find_diwali`,
/// `_tithi_owns_civil_day`, `get_vikram_samvat`, `get_vira_nirvana_samvat`).
library;

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

/// Whether [target] owns [date], counting a kshaya [target] as merged onto
/// the preceding tithi's day.
bool _owns(
  CivilDate date,
  int target, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) {
  int on(CivilDate d) => prevailingTithi(d, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule);
  final today = on(date);
  if (today == target) return true;
  if (today != (target - 2) % 30 + 1) return false;
  return on(date.next()) == target % 30 + 1;
}

const int _amavasya = 30;

/// Chaitra Shukla Pratipada of [year]: the day after the first day owned by
/// an Amavasya between 1 March and 21 April (the Phalguna Amavasya).
CivilDate chaitraShuklaPratipada(
  int year, {
  required double lat,
  required double lon,
  required Duration utcOffset,
  required SunriseRule rule,
}) {
  for (var i = 0; i < 52; i++) {
    final day = _plusDays(CivilDate(year, 3, 1), i);
    if (_owns(day, _amavasya, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule)) return day.next();
  }
  throw StateError('No Phalguna Amavasya between 1 March and 21 April $year.');
}

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
}) {
  for (var i = 0; i < 46; i++) {
    final day = _plusDays(CivilDate(year, 10, 10), i);
    final reference =
        _sunriseOf(day, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule) + jainTithiOffsetDays;
    if (_owns(day, _amavasya, lat: lat, lon: lon, utcOffset: utcOffset, rule: rule) &&
        siderealSunLongitude(reference) >= _kartikaSunLongitude) {
      return day;
    }
  }
  throw StateError('No Kartika Amavasya between 10 October and 24 November $year.');
}

/// Vikram Samvat on [date]: Gregorian year + 57 from Chaitra Shukla Pratipada on.
int vikramSamvat(CivilDate date, {required CivilDate chaitraShukla1}) =>
    date.compareTo(chaitraShukla1) >= 0 ? date.year + 57 : date.year + 56;

/// Vira Nirvana Samvat on [date]: Gregorian year + 527 from the day after Diwali.
int viraNirvanaSamvat(CivilDate date, {required CivilDate diwali}) =>
    date.compareTo(diwali) > 0 ? date.year + 527 : date.year + 526;
