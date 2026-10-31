/// Family F (plans/mobile-phase5-festivals.md §3): the vrats Python computes in
/// its own day loop over `SwissEphTithiProvider` (`jain_observances/vrats/`)
/// rather than from the snapshots. The provider reads each day's Jain day-start
/// tithi, sunrise tithi and Amanta month at the same instants the days hold, so
/// these rules read the days.
///
/// They take the raw days: the provider names a day's month as computed, while
/// [vratView] would move a relabelled day into the month before. Where the
/// entry takes the second day of a vriddhi, the provider's tithi and Python's
/// `get_greg_month` (which reads the snapshots) come from the vrat view.
library;

import 'dart:math';

import '../../calendar/month.dart';
import '../../panchang/elements.dart';
import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

/// Every family F rule type but Rohini (in `rohini.dart`), by registry `rule_type`.
final Map<String, FestivalRule> providerRules = {
  'DaslakshanVrat': _daslakshan,
  'RatnatrayaVrat': _ratnatraya,
  'ShodashkaranVrat': _shodashkaran,
  'RavivaraVrat': _ravivara,
};

/// What the provider reads of one day.
typedef _Reading = ({int tithi, int sunriseTithi, LunarMonth month});

/// The provider's non-Adhik days from [from], [length] of them at most, by date.
Map<CivilDate, _Reading> _window(FestivalEntry entry, List<FestivalDay> days, CivilDate from, int length) {
  final view = takesSecondDayOfVriddhi(entry.id, entry.category) ? vratView(days) : days;
  final until = from.plusDays(length);
  return {
    for (final (i, d) in days.indexed)
      if (d.date.compareTo(from) >= 0 && d.date.compareTo(until) < 0 && !d.month.isAdhika)
        d.date: (tithi: view[i].jainTithi, sunriseTithi: d.sunriseTithi, month: d.month),
  };
}

/// Python `get_greg_month`: the Gregorian month of the first non-Adhik day of
/// [paksha] [tithi] in the Amanta month the name's first part names, else of
/// that paksha's first day. Python falls back to a fixed table after that,
/// which a 14-month window never reaches; here there is no vrat.
int? _gregorianMonth(FestivalEntry entry, List<FestivalDay> days, String name, String paksha, int tithi) {
  final monthIndex = monthIndexOf(name.split('_').first);
  final view = takesSecondDayOfVriddhi(entry.id, entry.category) ? vratView(days) : days;
  final inPakshaDays =
      view.where((d) => d.month.index == monthIndex && !d.month.isAdhika && pakshaOf(d.jainTithi) == paksha);
  return (inPakshaDays.where((d) => inPaksha(d.jainTithi) == tithi).firstOrNull ?? inPakshaDays.firstOrNull)?.date.month;
}

/// The 45-day window from 7 days before the first of [month].
Map<CivilDate, _Reading>? _monthWindow(FestivalEntry entry, List<FestivalDay> days, int year, int? month, int length) =>
    month == null ? null : _window(entry, days, CivilDate(year, month, 1).plusDays(-7), length);

/// Python's `scan_window` / `scan_parv_window`: from [anchor], each day whose
/// tithi is the next one due or a later one in [from]..[to] joins the
/// schedule, a vriddhi's second day with it; at most [reach] days on.
List<CivilDate> _scan(Map<CivilDate, _Reading> active, CivilDate anchor, int from, int to, {required int reach}) {
  final schedule = <CivilDate>[];
  var day = anchor;
  var due = from;
  while (due <= to) {
    final tithi = active[day]?.tithi;
    if (tithi != null && tithi >= due && tithi <= to) {
      schedule.add(day);
      if (active[day.next()]?.tithi == tithi) {
        day = day.next();
        schedule.add(day);
      }
      due = tithi + 1;
    }
    day = day.next();
    if (day.compareTo(anchor.plusDays(reach)) > 0) break;
  }
  return schedule;
}

/// Shukla [from]..[to] of the entry's month, as `calculate_daslakshan_vrat` /
/// `calculate_ratnatraya_vrat` schedule it: from the first [from] (kshaya: the
/// first [from] + 1), then started earlier by as many days as the schedule
/// falls short of [length].
List<CivilDate>? _shuklaSchedule(
  FestivalEntry entry,
  List<FestivalDay> days,
  int year, {
  required int from,
  required int to,
  required int length,
  required int reach,
}) {
  final name = entry.jainMonth;
  if (name == null) return null;
  final active = _monthWindow(entry, days, year, _gregorianMonth(entry, days, name, 'Shukla', from), 45);
  if (active == null) return null;
  final monthIndex = monthIndexOf(name);
  final inMonth = active.entries.where((e) => e.value.month.index == monthIndex);
  final anchor = (inMonth.where((e) => e.value.tithi == from).firstOrNull ??
          inMonth.where((e) => e.value.tithi == from + 1).firstOrNull)
      ?.key;
  if (anchor == null) return null;
  final shift = max(0, length - _scan(active, anchor, from, to, reach: reach).length);
  final schedule = _scan(active, anchor.plusDays(-shift), from - shift, to, reach: reach);
  return schedule.isEmpty ? null : schedule;
}

/// Shukla 5 to 14, ten days at least.
List<FestivalOccurrence> _daslakshan(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final schedule = _shuklaSchedule(entry, days, year, from: 5, to: 14, length: 10, reach: 20);
  if (schedule == null) return const [];
  return [_occurrence(entry, 'daslakshan_${entry.jainMonth}_$year', schedule.first, schedule.last)];
}

/// Shukla 13 to Purnima, three days at least: a Prarambh and a Purna event.
List<FestivalOccurrence> _ratnatraya(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final schedule = _shuklaSchedule(entry, days, year, from: 13, to: 15, length: 3, reach: 10);
  if (schedule == null) return const [];
  final month = entry.jainMonth!.toLowerCase();
  return [
    _occurrence(entry, 'ratnatraya_vrat_prarambh_${month}_$year', schedule.first, schedule.first),
    _occurrence(entry, 'ratnatraya_vrat_purna_${month}_$year', schedule.last, schedule.last),
  ];
}

/// A cycle's Amanta start and end months: Krishna of Purnimanta month Y is
/// Krishna of Amanta month Y-1.
const Map<String, (int, int)> _shodashkaranCycles = {
  'BHADRAPADA_ASHVINA': (4, 5),
  'MAGHA_PHALGUNA': (9, 10),
  'CHAITRA_VAISHAKHA': (11, 0),
};

const int _krishna1 = 16;

/// Krishna 1 at sunrise or at the Jain day-start.
bool _krishna1Day(_Reading? r) => r != null && (r.tithi == _krishna1 || r.sunriseTithi == _krishna1);

/// `calculate_shodashkaran_vrat`: from the first Krishna 1 (at sunrise or the
/// Jain day-start) of the start month through the next one in the end month,
/// once 28 days are in; a vriddhi of the closing Krishna 1 takes both days.
/// Without one it stops 33 days on.
List<FestivalOccurrence> _shodashkaran(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final cycle = entry.jainMonth;
  final (startMonth, endMonth) = _shodashkaranCycles[cycle] ?? (-1, -1);
  if (startMonth < 0) return const [];
  final active = _monthWindow(
      entry, days, year, _gregorianMonth(entry, days, lunarMonthNames[startMonth], 'Krishna', 1), 76);
  if (active == null) return const [];
  final start =
      active.entries.where((e) => _krishna1Day(e.value) && e.value.month.index == startMonth).firstOrNull?.key;
  if (start == null) return const [];
  return [_occurrence(entry, 'shodashkaran_${cycle}_$year', start, _shodashkaranEnd(active, start, endMonth))];
}

CivilDate _shodashkaranEnd(Map<CivilDate, _Reading> active, CivilDate start, int endMonth) {
  var counted = 1;
  var end = start;
  for (var day = start.next(); day.compareTo(start.plusDays(33)) <= 0; day = day.next()) {
    final reading = active[day];
    if (reading == null) continue;
    if (_krishna1Day(reading) && counted >= 28 && reading.month.index == endMonth) {
      return _krishna1Day(active[day.next()]) ? day.next() : day;
    }
    counted++;
    end = day;
  }
  return end;
}

/// `calculate_ravivara_vrat`: nine Sundays from the last Sunday between 1 June
/// and 15 August in Ashadha (Adhik too) whose tithi 84 minutes after sunrise
/// is Shukla. The 84 minutes are Python's; every other provider vrat reads 144.
List<FestivalOccurrence> _ravivara(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final start = days
      .where((d) =>
          d.date.compareTo(CivilDate(year, 6, 1)) >= 0 &&
          d.date.compareTo(CivilDate(year, 8, 15)) <= 0 &&
          d.date.vara == 0 &&
          d.month.index == 3 &&
          tithiAt(d.sunrise + 84 / 1440) <= 15)
      .lastOrNull
      ?.date;
  if (start == null) return const [];
  return [_occurrence(entry, 'ravivara_$year', start, start.plusDays(56))];
}

FestivalOccurrence _occurrence(FestivalEntry entry, String id, CivilDate start, CivilDate end) => FestivalOccurrence(
  id: id,
  occurrenceId: id,
  ruleId: entry.id,
  category: entry.category,
  name: entry.name,
  nameHindi: entry.nameHindi,
  start: start,
  end: end,
);
