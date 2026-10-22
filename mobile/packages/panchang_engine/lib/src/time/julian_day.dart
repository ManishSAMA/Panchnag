/// Julian Day (UT) conversions. A Julian Day is the engine's instant type,
/// as in the Python reference (Swiss Ephemeris).
library;

/// Julian Day of the Unix epoch, 1970-01-01T00:00Z.
const double _unixEpochJd = 2440587.5;
const double _msPerDay = 86400000;

double julianDayFromUtc(DateTime utc) {
  if (!utc.isUtc) {
    throw ArgumentError.value(utc, 'utc', 'must be a UTC DateTime');
  }
  return utc.millisecondsSinceEpoch / _msPerDay + _unixEpochJd;
}

DateTime utcFromJulianDay(double jd) => DateTime.fromMillisecondsSinceEpoch(
      ((jd - _unixEpochJd) * _msPerDay).round(),
      isUtc: true,
    );
