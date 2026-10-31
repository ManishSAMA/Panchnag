/// Family D (plans/mobile-phase5-festivals.md §3): vrats spanning from a start
/// day to an end day, both found the way Python `_purn_month_tithi_day` does:
/// in the Purnimanta fortnight a registry-style Amanta month and paksha name.
library;

import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

const String _shukla = 'Shukla';
const String _krishna = 'Krishna';

const int _shravana = 4, _bhadrapada = 5;

/// Every family D rule type, by registry `rule_type`.
final Map<String, FestivalRule> fortnightRules = {
  'BhadrapadaKrishnaEkamMultiVrat': _bhadrapadaKrishnaEkam,
  'TeenChaubisiVrat': _toAshvinKrishna14('teen_chaubisi_vrat_prarambh', startTithi: 3),
  'BhayaHaranVrat': _toAshvinKrishna14('bhaya_haran_vrat', startTithi: 4),
};

/// The first day of [tithi] in the year's part of the fortnight; on a kshaya
/// the last day of the tithi before, which for Ekam is none.
CivilDate? _fortnightDay(List<FestivalDay> days, int year, int amantaMonth, String paksha, int tithi) {
  final fortnight = days.where((d) => d.date.year == year && inTargetMonth(d, amantaMonth, paksha)).toList();
  return firstHolding(fortnight, paksha, tithi) ?? lastHolding(fortnight, paksha, tithi - 1);
}

/// Purnimanta Bhadrapada Krishna 1: six vrats begin, two ending on Bhadrapada
/// Purnima and four on Purnimanta Ashvin Krishna 14.
List<FestivalOccurrence> _bhadrapadaKrishnaEkam(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final start = _fortnightDay(days, year, _shravana, _krishna, 1);
  if (start == null) return const [];
  final purnima = _fortnightDay(days, year, _bhadrapada, _shukla, 15) ?? start;
  final month = _fortnightDay(days, year, _bhadrapada, _krishna, 14) ?? start;
  return [
    for (final (prefix, category, end) in [
      ('solah_karan_vrat_prarambh', 'mahaparv_vrat', month),
      ('shri_jin_mukhavlokan_vrat_prarambh', 'vrat', month),
      ('shrut_skandha_vrat_prarambh', 'vrat', month),
      ('mushti_vidhan_vrat_prarambh', 'vrat', purnima),
      ('dhanda_kalash_vrat_prarambh', 'vrat', purnima),
      ('megh_mala_vrat_prarambh', 'vrat', month),
    ])
      _span(entry, '${prefix}_$year', category, start, end),
  ];
}

/// Purnimanta Bhadrapada Krishna [startTithi] to Purnimanta Ashvin Krishna 14.
FestivalRule _toAshvinKrishna14(String prefix, {required int startTithi}) => (entry, days, {required year}) {
  final start = _fortnightDay(days, year, _shravana, _krishna, startTithi);
  if (start == null) return const [];
  final end = _fortnightDay(days, year, _bhadrapada, _krishna, 14) ?? start;
  return [_span(entry, '${prefix}_$year', 'vrat', start, end)];
};

FestivalOccurrence _span(FestivalEntry entry, String id, String category, CivilDate start, CivilDate end) =>
    FestivalOccurrence(
      id: id,
      occurrenceId: id,
      ruleId: entry.id,
      category: category,
      name: entry.name,
      nameHindi: entry.nameHindi,
      start: start,
      end: end,
    );
