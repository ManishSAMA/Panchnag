/// Bhaktambar Vrat: Ashtami (8) and Chaturdashi (14) of every paksha, as two
/// independent days (Python `BhaktambarVratFestival`).
library;

import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

/// (target, fallback on kshaya or null, id slug). A kshaya Ashtami is observed
/// on Saptami; a kshaya Chaturdashi is not observed that paksha. That asymmetry
/// is the rule (plans/case-study-bhaktambar-saptami.md).
const List<(int, int?, String)> _observanceDays = [(8, 7, 'ashtami'), (14, null, 'chaturdashi')];

List<FestivalOccurrence> bhaktambarVrat(FestivalEntry entry, List<FestivalDay> days, {required int year}) => [
  for (final block in pakshaBlocks(days))
    for (final (target, fallback, slug) in _observanceDays)
      if (_observedDay(block, target, fallback) case final day? when day.date.year == year)
        _occurrence(entry, block.first, day, slug, year),
];

/// The first day of [target] in the block, or of [fallback] when [target] is kshaya.
FestivalDay? _observedDay(List<FestivalDay> block, int target, int? fallback) =>
    block.where((d) => inPaksha(d.jainTithi) == target).firstOrNull ??
    (fallback == null ? null : block.where((d) => inPaksha(d.jainTithi) == fallback).firstOrNull);

FestivalOccurrence _occurrence(FestivalEntry entry, FestivalDay first, FestivalDay day, String slug, int year) {
  final adhika = first.purnimantaMonth.isAdhika ? 'adhika_' : '';
  final id = 'bhaktambar_vrat_${year}_$adhika${jainMonthName(first).toLowerCase()}_'
      '${pakshaOf(first.jainTithi).toLowerCase()}_$slug';
  return FestivalOccurrence(
    id: id,
    occurrenceId: id,
    ruleId: entry.id,
    category: entry.category.isEmpty ? 'vrat' : entry.category,
    name: entry.name,
    nameHindi: entry.nameHindi,
    start: day.date,
    end: day.date,
  );
}
