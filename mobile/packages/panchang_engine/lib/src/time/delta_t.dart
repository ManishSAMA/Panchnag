/// ΔT = TT − UT, from the table exported from Swiss Ephemeris.
library;

import 'delta_t_table.g.dart';

/// ΔT in seconds at [jdUt], linearly interpolated between quarterly samples.
///
/// Throws [RangeError] outside the table: extrapolating ΔT would silently
/// part ways with the Python reference.
double deltaTSeconds(double jdUt) {
  final first = deltaTTable.first.$1;
  final last = deltaTTable.last.$1;
  if (jdUt < first || jdUt > last) {
    throw RangeError.value(jdUt, 'jdUt', 'outside the ΔT table [$first, $last]');
  }
  final upper = deltaTTable.indexWhere((row) => row.$1 >= jdUt);
  if (deltaTTable[upper].$1 == jdUt) return deltaTTable[upper].$2;
  final (jd0, dt0) = deltaTTable[upper - 1];
  final (jd1, dt1) = deltaTTable[upper];
  return dt0 + (dt1 - dt0) * (jdUt - jd0) / (jd1 - jd0);
}

/// Terrestrial Time Julian Day for a UT Julian Day.
double terrestrialTime(double jdUt) => jdUt + deltaTSeconds(jdUt) / 86400;
