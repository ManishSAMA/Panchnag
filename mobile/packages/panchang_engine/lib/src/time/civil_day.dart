/// Civil dates and the anchor instant each civil day is computed from.
library;

import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'julian_day.dart';

/// A calendar date with no time or zone, like Python's `datetime.date`.
final class CivilDate implements Comparable<CivilDate> {
  const CivilDate(this.year, this.month, this.day);

  factory CivilDate.parse(String iso) {
    final parsed = DateTime.parse(iso);
    return CivilDate(parsed.year, parsed.month, parsed.day);
  }

  final int year;
  final int month;
  final int day;

  CivilDate next() {
    final following = DateTime.utc(year, month, day + 1);
    return CivilDate(following.year, following.month, following.day);
  }

  /// The weekday, 0 = Sunday (Python `get_vara_from_date`).
  int get vara => DateTime.utc(year, month, day).weekday % 7;

  String get iso =>
      '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}-${day.toString().padLeft(2, '0')}';

  @override
  int compareTo(CivilDate other) => iso.compareTo(other.iso);

  @override
  bool operator ==(Object other) =>
      other is CivilDate && other.year == year && other.month == month && other.day == day;

  @override
  int get hashCode => Object.hash(year, month, day);

  @override
  String toString() => iso;
}

bool _timeZonesLoaded = false;

tz.Location _location(String name) {
  if (!_timeZonesLoaded) {
    tzdata.initializeTimeZones();
    _timeZonesLoaded = true;
  }
  return tz.getLocation(name);
}

/// The zone's standard (non-daylight) UTC offset in force on [date].
///
/// Like the Python engine, the offset is read at local noon so a DST-change
/// day uses its own clock. During daylight time the standard offset is that of
/// the nearest earlier non-DST period.
Duration standardOffset(CivilDate date, String timeZone) {
  final location = _location(timeZone);
  final noon = tz.TZDateTime(location, date.year, date.month, date.day, 12);
  var instant = location.lookupTimeZone(noon.millisecondsSinceEpoch);
  while (instant.timeZone.isDst && instant.start > tz.minTime) {
    instant = location.lookupTimeZone(instant.start - 1);
  }
  return instant.timeZone.offset;
}

/// Julian Day of local midnight starting [date], on the zone's standard clock.
///
/// Mirrors Python `local_date_anchor_jd(date, tz, hour=0, clock="standard")`;
/// the day's sunrise is searched for from this instant.
double civilDayAnchor(CivilDate date, String timeZone) {
  final midnightUtc = DateTime.utc(date.year, date.month, date.day);
  return julianDayFromUtc(midnightUtc.subtract(standardOffset(date, timeZone)));
}
