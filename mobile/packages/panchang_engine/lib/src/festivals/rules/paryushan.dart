/// The Shwetambar 50-day Paryushan count from Ashadha Shukla 14 to Samvatsari
/// (Python `ShvetambaraParyushan50DayFestival`), and Labdhi Vidhan Vrat, which
/// ends on that Samvatsari (Python `LabdhiVidhanVratFestival`).
library;

import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

const int _ashadha = 3;

/// Samvatsari is day 50 of the count, 49 days after its first.
const int _samvatsariOffset = 49;

/// Paryushan days 1-7 are days 43-49 of the count.
const int _paryushanFirstDay = 43;
const int _paryushanDays = 7;

/// The last day of the year whose Jain day-start holds non-Adhik Ashadha
/// Shukla 14: the second when it holds two. Python names the month from the
/// Amanta reading here and the Purnimanta one in Labdhi Vidhan; a Shukla day
/// has the same month in both.
CivilDate? _ashadhaShukla14(List<FestivalDay> days, int year) => days
    .where((d) =>
        d.date.year == year &&
        d.month.index == _ashadha &&
        !d.month.isAdhika &&
        holds(d, Reading.jain, 'Shukla', 14))
    .lastOrNull
    ?.date;

List<FestivalOccurrence> paryushan50Day(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final start = _ashadhaShukla14(days, year);
  if (start == null) return const [];
  return [
    _occurrence(entry, 'shvetambara_chaturmas_prarambh_$year', start, category: 'mahaparv'),
    for (var n = 1; n <= _paryushanDays; n++)
      _occurrence(entry, 'paryushan_parv_day_${n}_$year', start.plusDays(_paryushanFirstDay + n - 2),
          category: 'mahaparv'),
    _occurrence(entry, 'samvatsari_mahaparv_$year', start.plusDays(_samvatsariOffset), category: 'mahaparv'),
  ];
}

List<FestivalOccurrence> labdhiVidhanVrat(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final anchor = _ashadhaShukla14(days, year);
  final start = _bhadrapadaKrishnaAmavasya(days, year);
  if (anchor == null || start == null) return const [];
  return [
    _occurrence(entry, 'labdhi_vidhan_vrat_prarambh_$year', start, category: entry.category),
    _occurrence(entry, 'labdhi_vidhan_vrat_purna_$year', anchor.plusDays(_samvatsariOffset), category: entry.category),
  ];
}

/// The first Purnimanta Bhadrapada Krishna Amavasya of the year, reading only
/// the Adhik days when there are any; on a kshaya, the last Krishna 14.
CivilDate? _bhadrapadaKrishnaAmavasya(List<FestivalDay> days, int year) {
  final bhadrapada = days.where((d) => d.date.year == year && jainMonthName(d) == 'BHADRAPADA').toList();
  final hasAdhik = bhadrapada.any((d) => d.month.isAdhika);
  final month = bhadrapada.where((d) => d.month.isAdhika == hasAdhik).toList();
  return (month.where((d) => holds(d, Reading.jain, 'Krishna', 15)).firstOrNull ??
          month.where((d) => holds(d, Reading.jain, 'Krishna', 14)).lastOrNull)
      ?.date;
}

FestivalOccurrence _occurrence(FestivalEntry entry, String id, CivilDate date, {required String category}) =>
    FestivalOccurrence(
      id: id,
      occurrenceId: id,
      ruleId: entry.id,
      category: category,
      name: entry.name,
      nameHindi: entry.nameHindi,
      start: date,
      end: date,
    );
