/// Day-selection helpers shared by the festival rules (the module-level
/// functions of Python `festival_rules.py`). Tithis are 1-30; a paksha is
/// 'Shukla' or 'Krishna', as the registry spells it.
library;

import '../calendar/month.dart';
import '../time/civil_day.dart';
import 'days.dart';

/// Which instant of the day a rule reads the tithi at.
enum Reading {
  /// Sunrise (Python's private `_sunrise_*` fields).
  sunrise,

  /// The Jain day-start, sunrise + 2 h 24 min (Python `jain_*` / `tithi_in_paksha`).
  jain,

  /// Sunset (Python `evening_*`).
  evening;

  int of(FestivalDay day) => switch (this) {
    Reading.sunrise => day.sunriseTithi,
    Reading.jain => day.jainTithi,
    Reading.evening => day.eveningTithi,
  };
}

String pakshaOf(int tithi) => tithi <= 15 ? 'Shukla' : 'Krishna';

/// 1-15 within the paksha.
int inPaksha(int tithi) => tithi <= 15 ? tithi : tithi - 15;

bool holds(FestivalDay day, Reading reading, String? paksha, int tithi) {
  final t = reading.of(day);
  return pakshaOf(t) == paksha && inPaksha(t) == tithi;
}

/// Python `months._ALIASES`: registry and regional spellings of month names.
const Map<String, String> _monthAliases = {
  'ASHVINA': 'ASHWIN', 'ASO': 'ASHWIN', 'ASOJ': 'ASHWIN',
  'MARGASHIRSHA': 'AGRAHAYANA', 'MARGASHIRSA': 'AGRAHAYANA', 'MAGSAR': 'AGRAHAYANA',
  'MANSIR': 'AGRAHAYANA', 'MARGASHIRA': 'AGRAHAYANA',
  'JYESTHA': 'JYESHTHA', 'JETH': 'JYESHTHA',
  'VAISAKH': 'VAISHAKHA', 'BAISAKH': 'VAISHAKHA',
  'KARTIK': 'KARTIKA',
};

/// The month index (0 = Chaitra) a registry month name means, or null for a
/// name that is no month (Python `months.canonical`).
int? monthIndexOf(String name) {
  final upper = name.toUpperCase();
  final canonical = _monthAliases[upper] ?? upper;
  final index = lunarMonthNames.indexWhere((m) => m.toUpperCase() == canonical);
  return index < 0 ? null : index;
}

/// Python `_matches_purnimanta_target`: whether [day] sits in the non-Adhik
/// Purnimanta month a registry entry targets. Entries store the Amanta month,
/// so a Krishna entry is read in the following Purnimanta month.
bool inTargetMonth(FestivalDay day, int? monthIndex, String? paksha) {
  if (monthIndex == null) return false;
  final target = paksha == 'Krishna' ? (monthIndex + 1) % 12 : monthIndex;
  return day.purnimantaMonth.index == target && !day.purnimantaMonth.isAdhika;
}

/// Python `_pradosh_days`: days on which [tithi] of [paksha] holds at sunset, in order.
List<FestivalDay> pradoshDays(List<FestivalDay> days, int tithi, String paksha) =>
    days.where((d) => holds(d, Reading.evening, paksha, tithi)).toList()..sort((a, b) => a.date.compareTo(b.date));

/// Python `_sixghati_pullback`. [day] is the udaya day for [tithi]. If the tithi
/// is weak (gone by the Jain day-start), the observance moves to the day before
/// when that day is strong for the tithi before, or, for a Purnima or Amavasya
/// only, when that day's Jain day-start has already reached it.
CivilDate sixGhatiPullback(FestivalDay day, List<FestivalDay> days, int tithi, String? paksha) {
  if (holds(day, Reading.jain, paksha, tithi)) return day.date;
  final previous = day.date.previous();
  final before = days.where((d) => d.date == previous);
  final buildingToward =
      before.any((d) => holds(d, Reading.sunrise, paksha, tithi - 1) && holds(d, Reading.jain, paksha, tithi - 1));
  final alreadyReached = tithi == 15 && before.any((d) => holds(d, Reading.jain, paksha, tithi));
  return buildingToward || alreadyReached ? previous : day.date;
}

/// Python `_kshaya_backshift`: a tithi that holds on no day moves back to the
/// last day of the tithi before it. A Pratipada, whose predecessor is in the
/// previous paksha, lands on the eve of the first later tithi; any other tithi
/// falls forward only when its predecessor is missing. [reading] must be the one
/// [pool] was selected on.
CivilDate? kshayaBackshift(List<FestivalDay> pool, int tithi, Reading reading) {
  final previous = [for (final d in pool) if (inPaksha(reading.of(d)) == tithi - 1) d.date]..sort();
  if (previous.isNotEmpty) return previous.last;
  final later = [for (final d in pool) if (inPaksha(reading.of(d)) > tithi) d.date]..sort();
  if (later.isEmpty) return null;
  return tithi == 1 ? later.first.previous() : later.first;
}

/// Python `_first_of_two_jain_daystart_days`: the first of two consecutive days
/// on which [tithi] of [paksha] holds the Jain day-start, or null.
CivilDate? firstOfTwoJainDayStarts(List<FestivalDay> days, String paksha, int tithi) {
  final dates = [for (final d in days) if (holds(d, Reading.jain, paksha, tithi)) d.date]..sort();
  for (var i = 0; i + 1 < dates.length; i++) {
    if (dates[i].next() == dates[i + 1]) return dates[i];
  }
  return null;
}
