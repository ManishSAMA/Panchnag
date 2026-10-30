/// Pushpanjali Vrat: Shukla Panchami (5) to Navami (9) of Chaitra, Bhadrapada
/// and Magha, one occurrence per civil day (Python `PushpanjaliVratFestival`).
library;

import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

/// Amanta month index and the season its occurrence ids are tagged with.
const List<(int, String)> _seasons = [(0, 'spring'), (5, 'monsoon'), (10, 'winter')];

List<FestivalOccurrence> pushpanjaliVrat(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final only = entry.jainMonth == null ? null : monthIndexOf(entry.jainMonth!);
  return [
    for (final (monthIndex, season) in _seasons)
      if (entry.jainMonth == null || only == monthIndex)
        for (final date in _span(amantaMonthInYear(days, year, monthIndex)))
          _occurrence(entry, season, date),
  ];
}

/// Shukla 5-9, starting a day early on Chaturthi when a tithi of Shukla 5-14
/// is kshaya and none is doubled.
List<CivilDate> _span(List<FestivalDay> month) {
  List<CivilDate> datesOf(int tithi) => [for (final d in month) if (holds(d, Reading.jain, 'Shukla', tithi)) d.date];
  final active = {for (var t = 5; t <= 9; t++) ...datesOf(t)}.toList()..sort();
  if (active.isEmpty) return const [];

  final counts = [for (var t = 5; t <= 14; t++) datesOf(t).length];
  final onlyKshaya = counts.contains(0) && counts.every((n) => n <= 1);
  final chaturthi = datesOf(4);
  final start = !onlyKshaya ? active.first : (chaturthi.firstOrNull ?? active.first.previous());
  return [for (var d = start; d.compareTo(active.last) <= 0; d = d.next()) d];
}

FestivalOccurrence _occurrence(FestivalEntry entry, String season, CivilDate date) {
  final id = 'pushpanjali_vrat_${season}_${date.iso}';
  return FestivalOccurrence(
    id: id,
    occurrenceId: id,
    ruleId: entry.id,
    category: 'vrat',
    name: entry.name,
    nameHindi: entry.nameHindi,
    start: date,
    end: date,
  );
}
