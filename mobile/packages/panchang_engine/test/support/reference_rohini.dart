// Rohini's search as it stood before it skipped the days Rohini cannot reach
// (plans/mobile-phase5-festivals.md, festival speed). Tests hold the faster
// search to this one. Do not edit: it is the old behaviour.

import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/festivals.dart';
import 'package:panchang_engine/src/festivals/registry.dart';

const int _rohini = 4;

/// Once Rohini is found the search moves on this many days.
const int _skipDays = 20;

/// Python steps this far past each nakshatra's end before reading the next.
const double _spanStepDays = 0.01;

List<FestivalOccurrence> referenceRohiniVrat(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final last = CivilDate(year, 12, 31);
  final found = <CivilDate>[];
  var i = days.indexWhere((d) => d.date == CivilDate(year - 1, 12, 15));
  while (i >= 0 && i + 1 < days.length && days[i].date.compareTo(last) <= 0) {
    final vratDay = _vratDay(days[i], days[i + 1]);
    if (vratDay == null) {
      i++;
      continue;
    }
    found.add(vratDay);
    i += _skipDays;
  }
  return [for (final date in found) _occurrence(entry, date)];
}

CivilDate? _vratDay(FestivalDay today, FestivalDay tomorrow) {
  final from = _clockReadAsUtc(today);
  final to = _clockReadAsUtc(tomorrow);
  if (nakshatraAt(from) == _rohini) return today.date;
  for (var instant = nakshatraEnd(from) + _spanStepDays; instant <= to; instant = nakshatraEnd(instant) + _spanStepDays) {
    if (nakshatraAt(instant) == _rohini) return nakshatraEnd(instant) < to ? tomorrow.date : null;
  }
  return null;
}

/// Python's provider hands back the sunrise as a naive local time and its
/// nakshatra search reads naive times as UTC, so the sunrise it compares
/// against is the local clock reading taken as UTC (plans/mobile-phase5-festivals.md
/// §6.1: kept for parity, to be fixed in Python first).
double _clockReadAsUtc(FestivalDay day) =>
    day.sunrise + day.standardOffset.inMicroseconds / Duration.microsecondsPerDay;

FestivalOccurrence _occurrence(FestivalEntry entry, CivilDate date) => FestivalOccurrence(
  id: entry.id,
  occurrenceId: '${entry.id}:${date.iso}',
  ruleId: entry.id,
  category: entry.category,
  name: entry.name,
  nameHindi: entry.nameHindi,
  start: date,
  end: date,
);
