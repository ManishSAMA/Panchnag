/// Ravi Vrat: nine Sundays from the last Sunday of the year's non-Adhik Ashadha
/// Shukla paksha (Python `RaviVratFestival`). Python also titles each day
/// (Ravi Pushya, Ravi Saptami); titles come with Phase 6.
library;

import '../../calendar/month.dart';
import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

const int _ashadha = 3;
const int _sunday = 0;
const int _sundays = 9;

List<FestivalOccurrence> raviVratSundays(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final start = days
      .where((d) =>
          d.date.year == year &&
          d.month == const LunarMonth(index: _ashadha, isAdhika: false) &&
          pakshaOf(d.jainTithi) == 'Shukla' &&
          d.date.vara == _sunday)
      .lastOrNull;
  if (start == null) return const [];

  final read = {for (final d in days) d.date};
  return [
    for (var week = 0; week < _sundays; week++)
      if (_daysAfter(start.date, 7 * week) case final date when read.contains(date)) _occurrence(entry, date),
  ];
}

CivilDate _daysAfter(CivilDate date, int days) {
  final later = DateTime.utc(date.year, date.month, date.day + days);
  return CivilDate(later.year, later.month, later.day);
}

FestivalOccurrence _occurrence(FestivalEntry entry, CivilDate date) => FestivalOccurrence(
  id: entry.id,
  occurrenceId: '${entry.id}_${date.iso}',
  ruleId: entry.id,
  category: entry.category,
  name: entry.name,
  nameHindi: entry.nameHindi,
  start: date,
  end: date,
);
