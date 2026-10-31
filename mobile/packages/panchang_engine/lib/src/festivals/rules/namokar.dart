/// Namokar Mahamantra 35-Vrat: 35 fasts over 18 lunar months, one per
/// syllable of the mantra (Python `Namokar35VratFestival`).
library;

import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

/// (step, Amanta month index, paksha, tithi, fallback tithi on kshaya), as in
/// Python `STEPS_DEFINITION`. Months are Amanta, so a Krishna step sits in the
/// first half of the named month.
const List<(int, int, String, int, int)> _steps = [
  // Ṇamō Arihantāṇaṁ: 7 Saptamis.
  (1, 3, 'Shukla', 7, 6), (2, 4, 'Krishna', 7, 6), (3, 4, 'Shukla', 7, 6), (4, 5, 'Krishna', 7, 6),
  (5, 5, 'Shukla', 7, 6), (6, 6, 'Krishna', 7, 6), (7, 6, 'Shukla', 7, 6),
  // Ṇamō Siddhāṇaṁ: 5 Panchamis.
  (8, 7, 'Krishna', 5, 4), (9, 7, 'Shukla', 5, 4), (10, 8, 'Krishna', 5, 4), (11, 8, 'Shukla', 5, 4),
  (12, 9, 'Krishna', 5, 4),
  // Ṇamō Āyariyāṇaṁ: 7 Chaturdashis.
  (13, 9, 'Krishna', 14, 13), (14, 9, 'Shukla', 14, 13), (15, 10, 'Krishna', 14, 13), (16, 10, 'Shukla', 14, 13),
  (17, 11, 'Krishna', 14, 13), (18, 11, 'Shukla', 14, 13), (19, 0, 'Krishna', 14, 13),
  // Ṇamō Uvajjhāyāṇaṁ: 7 Chaturdashis.
  (20, 0, 'Shukla', 14, 13), (21, 1, 'Krishna', 14, 13), (22, 1, 'Shukla', 14, 13), (23, 2, 'Krishna', 14, 13),
  (24, 2, 'Shukla', 14, 13), (25, 3, 'Krishna', 14, 13), (26, 3, 'Shukla', 14, 13),
  // Ṇamō Lōē Savvasāhūṇaṁ: 9 Navamis.
  (27, 4, 'Krishna', 9, 8), (28, 4, 'Shukla', 9, 8), (29, 5, 'Krishna', 9, 8), (30, 5, 'Shukla', 9, 8),
  (31, 6, 'Krishna', 9, 8), (32, 6, 'Shukla', 9, 8), (33, 7, 'Krishna', 9, 8), (34, 7, 'Shukla', 9, 8),
  (35, 8, 'Krishna', 9, 8),
];

List<FestivalOccurrence> namokar35Vrat(FestivalEntry entry, List<FestivalDay> days, {required int year}) => [
  for (final (step, monthIndex, paksha, tithi, fallback) in _steps)
    if (_observedDay(amantaMonthInYear(days, year, monthIndex), paksha, tithi, fallback) case final day?)
      _occurrence(entry, step, year, day),
];

/// The first day of [tithi], or on a kshaya the last day of [fallback].
FestivalDay? _observedDay(List<FestivalDay> month, String paksha, int tithi, int fallback) =>
    month.where((d) => holds(d, Reading.jain, paksha, tithi)).firstOrNull ??
    month.where((d) => holds(d, Reading.jain, paksha, fallback)).lastOrNull;

FestivalOccurrence _occurrence(FestivalEntry entry, int step, int year, FestivalDay day) {
  final id = 'namokar_vrat_step_${step}_$year';
  return FestivalOccurrence(
    id: id,
    occurrenceId: id,
    ruleId: entry.id,
    category: 'mahaparv_vrat',
    name: entry.name,
    nameHindi: entry.nameHindi,
    start: day.date,
    end: day.date,
  );
}
