import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

bool _timeZonesLoaded = false;

tz.Location _zone(String name) {
  if (!_timeZonesLoaded) {
    tzdata.initializeTimeZones();
    _timeZonesLoaded = true;
  }
  return tz.getLocation(name);
}

/// [utc] as the city's wall clock reads it, as a plain (zone-less) DateTime.
DateTime cityWall(DateTime utc, String timezone) {
  final t = tz.TZDateTime.from(utc, _zone(timezone));
  return DateTime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.millisecond, t.microsecond);
}

/// The civil date in the city at [now].
CivilDate todayIn(String timezone, DateTime now) {
  final wall = cityWall(now, timezone);
  return CivilDate(wall.year, wall.month, wall.day);
}
