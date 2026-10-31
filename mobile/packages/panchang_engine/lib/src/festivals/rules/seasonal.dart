/// Step 11 (plans/mobile-phase5-festivals.md §5): vrats observed once in each
/// of several Amanta months, Python `KarmaNirjaraVratFestival` and
/// `AshtahnikaVratFestival`. Neither takes the second day of a vriddhi
/// (`jain_observances/vriddhi.py`).
library;

import '../../calendar/month.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

const String _shukla = 'Shukla';

final Map<String, FestivalRule> seasonalRules = {
  'KarmaNirjaraVrat': _karmaNirjara,
  'AshtahnikaVrat': _ashtahnika,
};

/// Shukla 14 of each Chaturmas month (kshaya: the last Shukla 13). Python
/// tries the first of two consecutive Chaturdashi days, then the first one,
/// twice over; within one month's days these are all the first Chaturdashi.
List<FestivalOccurrence> _karmaNirjara(FestivalEntry entry, List<FestivalDay> days, {required int year}) => [
  for (final monthIndex in const [3, 4, 5, 6])
    if (amantaMonthInYear(days, year, monthIndex) case final month)
      if (firstHolding(month, _shukla, 14) ?? lastHolding(month, _shukla, 13) case final date?)
        FestivalOccurrence(
          id: 'karma_nirjara_vrat_${_monthKey(month.first.month)}_$year',
          occurrenceId: 'karma_nirjara_vrat_${date.iso}',
          ruleId: entry.id,
          category: 'parva_vrat',
          name: entry.name,
          nameHindi: entry.nameHindi,
          start: date,
          end: date,
        ),
];

/// `ashwin`, or `adhik_shravana` for an Adhik month.
String _monthKey(LunarMonth month) =>
    '${month.isAdhika ? 'adhik_' : ''}${lunarMonthNames[month.index].toLowerCase()}';

/// Shukla 8 to Purnima of Ashadha, Kartika and Phalguna. A kshaya Ashtami
/// starts on the first Saptami, else the day before the first of Shukla 8-15;
/// the end is the last Purnima, else the last of Shukla 8-14.
List<FestivalOccurrence> _ashtahnika(FestivalEntry entry, List<FestivalDay> days, {required int year}) => [
  for (final (monthIndex, season) in const [(3, 'ashadha'), (7, 'kartika'), (11, 'phalguna')])
    if (amantaMonthInYear(days, year, monthIndex) case final month)
      if (month.where((d) => d.jainTithi >= 8 && d.jainTithi <= 15).toList() case final span when span.isNotEmpty)
        FestivalOccurrence(
          id: 'ashtahnika_${season}_$year',
          occurrenceId: 'ashtahnika_${season}_$year',
          ruleId: entry.id,
          category: 'mahaparv',
          name: entry.name,
          nameHindi: entry.nameHindi,
          start: firstHolding(month, _shukla, 8) ?? firstHolding(month, _shukla, 7) ?? span.first.date.previous(),
          end: lastHolding(month, _shukla, 15) ?? span.last.date,
        ),
];
