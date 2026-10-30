/// The data-driven rule: a festival on one tithi of one month, or of every
/// month (Python `SingleTithiFestival`).
library;

import '../calendar/month.dart';
import '../time/civil_day.dart';
import 'days.dart';
import 'festivals.dart';
import 'primitives.dart';
import 'registry.dart';

/// Kalyanaks are fixed to the first civil day their tithi holds the Jain day-start.
const Set<String> _kalyanakCategories = {'kalyanak', 'janam_kalyanak', 'garbha_kalyanak'};

/// The occurrences of [entry] whose day falls in [year], read from [days].
List<FestivalOccurrence> singleTithi(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final tithi = entry.tithi;
  if (tithi == null) return const [];

  // Parva tithis select on the Jain day-start, matching the Amanta month
  // grouping they are bucketed by; every other category selects on sunrise,
  // the precondition the 6-ghati and Kalyanak comparisons rely on
  // (plans/tithi_unification/design.md).
  final reading = entry.category == 'parva' ? Reading.jain : Reading.sunrise;
  final monthIndex = entry.jainMonth == null ? null : monthIndexOf(entry.jainMonth!);
  final pool = [
    for (final d in days)
      if (d.date.year == year &&
          (entry.jainMonth == null || inTargetMonth(d, monthIndex, entry.paksha)) &&
          (entry.paksha == null || entry.dayRule == DayRule.pradosh || pakshaOf(reading.of(d)) == entry.paksha))
        d,
  ];

  final dates = entry.jainMonth != null
      ? _annual(entry, tithi, pool, days, reading)
      : [for (final month in _byAmantaMonthName(pool)) ..._monthly(entry, tithi, month, reading)];
  return [for (final date in dates) _occurrence(entry, date)];
}

List<CivilDate> _annual(FestivalEntry entry, int tithi, List<FestivalDay> pool, List<FestivalDay> days, Reading reading) {
  final candidates = entry.dayRule == DayRule.pradosh
      ? pradoshDays(pool, tithi, entry.paksha ?? 'Krishna')
      : [for (final d in pool) if (inPaksha(reading.of(d)) == tithi) d];
  if (candidates.isEmpty) return [?kshayaBackshift(pool, tithi, reading)];
  if (entry.category == 'parva') return [for (final d in candidates) d.date];

  final resolved =
      _kalyanakFirstActiveDay(entry, tithi, pool) ??
      sixGhatiPullback(_vriddhiChoice(entry, candidates), pool, tithi, entry.paksha);
  return [_originPullback(entry, tithi, resolved, days)];
}

List<CivilDate> _monthly(FestivalEntry entry, int tithi, List<FestivalDay> group, Reading reading) {
  final candidates = [for (final d in group) if (inPaksha(reading.of(d)) == tithi) d];
  if (candidates.isEmpty) return [?kshayaBackshift(group, tithi, reading)];
  if (entry.category == 'parva') return [for (final d in candidates) d.date];
  return [sixGhatiPullback(_vriddhiChoice(entry, candidates), group, tithi, entry.paksha)];
}

FestivalDay _vriddhiChoice(FestivalEntry entry, List<FestivalDay> candidates) =>
    candidates.length > 1 && entry.vriddhiRule == 'second_day' ? candidates[1] : candidates.first;

/// Python groups by the Amanta month's base name, so an Adhik month and its
/// Nija month, or the same name at both ends of a year, share one group.
Iterable<List<FestivalDay>> _byAmantaMonthName(List<FestivalDay> pool) {
  final groups = <String, List<FestivalDay>>{};
  for (final d in pool) {
    (groups[lunarMonthNames[d.month.index]] ??= []).add(d);
  }
  final names = groups.keys.toList()..sort();
  return [for (final name in names) groups[name]!..sort((a, b) => a.date.compareTo(b.date))];
}

/// A Kalyanak whose tithi holds the Jain day-start on two consecutive days is
/// fixed to the first of them (Python `_kalyanak_first_active_day`).
CivilDate? _kalyanakFirstActiveDay(FestivalEntry entry, int tithi, List<FestivalDay> pool) {
  final paksha = entry.paksha;
  if (!_kalyanakCategories.contains(entry.category) ||
      entry.dayRule != DayRule.udaya ||
      entry.jainMonth == null ||
      paksha == null) {
    return null;
  }
  return firstOfTwoJainDayStarts(pool, paksha, tithi);
}

/// The opt-in Day-1 anchor (Python `_origin_pullback_day`): the day before, when
/// the tithi was already active at its sunset without being its sunrise tithi.
CivilDate _originPullback(FestivalEntry entry, int tithi, CivilDate resolved, List<FestivalDay> days) {
  final paksha = entry.paksha;
  if (!entry.originPullback || paksha == null) return resolved;
  final previous = resolved.previous();
  final before = days.where((d) => d.date == previous).firstOrNull;
  if (before == null) return resolved;
  final alreadyUdaya = holds(before, Reading.sunrise, paksha, tithi);
  final activeBySunset = holds(before, Reading.evening, paksha, tithi);
  return activeBySunset && !alreadyUdaya ? previous : resolved;
}

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
