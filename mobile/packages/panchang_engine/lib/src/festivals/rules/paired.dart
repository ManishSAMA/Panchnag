/// Family C (plans/mobile-phase5-festivals.md §3): a Prarambh and a Purna event,
/// each on its own anchor day. Each Python rule is its own class
/// (`SaptaRishiVratFestival`, `ShraddhaVratFestival`, ...); the anchors are the
/// first or last day holding a tithi, with a fallback tithi on a kshaya.
library;

import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

const String _shukla = 'Shukla';
const String _krishna = 'Krishna';

const int _chaitra = 0, _jyeshtha = 2, _ashadha = 3, _shravana = 4, _bhadrapada = 5, _ashwin = 6, _kartika = 7;
const int _magha = 10;

/// Every family C rule type but Labdhi Vidhan Vrat (in `paryushan.dart`), by
/// registry `rule_type`.
final Map<String, FestivalRule> pairedRules = {
  'ChaitraLabdhiVidhan': _labdhiVidhan(_chaitra, 'chaitra'),
  'MaghaLabdhiVidhan': _labdhiVidhan(_magha, 'magha'),
  'SaptaRishiVrat': _saptaRishi,
  'SaptaParamsthanVrat': _saptaParamsthan,
  'RakshabandhanVrat': _rakshabandhanVrat,
  'AkshayaNidhiVrat': _akshayaNidhi,
  'AnantChaturdashiVrat': _anantChaturdashi,
  'RatnatrayaSankatHaranVrat': _ratnatrayaSankatHaran,
  'ShraddhaVrat': _shraddha,
  'NavapadOliVrat': _navapadOli,
  'MonthlyVrat': _prathamJethJinvani,
};

/// An event on the start (Prarambh) or end (Purna) day: its id is `<prefix>_<year>`.
typedef _Event = (String prefix, String category, {bool atEnd});

/// Both events, or none when either day is missing.
List<FestivalOccurrence> _pair(
  FestivalEntry entry,
  int year, {
  required CivilDate? start,
  required CivilDate? end,
  required List<_Event> events,
}) => [
  if ((start, end) case (final start?, final end?))
    for (final (prefix, category, :atEnd) in events) _occurrence(entry, '${prefix}_$year', category, atEnd ? end : start),
];

/// Purnimanta Krishna Amavasya (first; kshaya: last Krishna 14) to Shukla 4
/// (last; kshaya: last Shukla 3).
FestivalRule _labdhiVidhan(int monthIndex, String key) => (entry, days, {required year}) {
  final month = purnimantaMonthInYear(days, year, monthIndex);
  return _pair(entry, year,
      start: firstHolding(month, _krishna, 15) ?? lastHolding(month, _krishna, 14),
      end: lastHolding(month, _shukla, 4) ?? lastHolding(month, _shukla, 3),
      events: [
        ('labdhi_vidhan_start_$key', 'mahaparv_vrat', atEnd: false),
        ('labdhi_vidhan_purna_$key', 'mahaparv_vrat', atEnd: true),
      ]);
};

/// Ashadha Purnima to Shravana Krishna 5. Python runs the first Purnima through
/// the 6-ghati pull-back, a no-op on a day that already holds Purnima at the
/// Jain day-start.
List<FestivalOccurrence> _saptaRishi(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final ashadha = amantaMonthInYear(days, year, _ashadha);
  final shravana = amantaMonthInYear(days, year, _shravana);
  return _pair(entry, year,
      start: firstHolding(ashadha, _shukla, 15) ?? lastHolding(ashadha, _shukla, 14),
      end: lastHolding(shravana, _krishna, 5) ?? lastHolding(shravana, _krishna, 4),
      events: [
        ('sapta_rishi_vrat_prarambh', 'vrat', atEnd: false),
        ('sapta_rishi_vrat_nishthapan', 'vrat', atEnd: true),
      ]);
}

/// Shravana Shukla 1 to Shukla 7. A kshaya Shukla 1 falls back to the month's
/// last Amavasya (at the far end of an Amanta month, as in Python), then to the
/// day before the first Shukla 2.
List<FestivalOccurrence> _saptaParamsthan(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final shravana = amantaMonthInYear(days, year, _shravana);
  return _pair(entry, year,
      start: firstHolding(shravana, _shukla, 1) ??
          lastHolding(shravana, _krishna, 15) ??
          _dayBefore(days, firstHolding(shravana, _shukla, 2)),
      end: lastHolding(shravana, _shukla, 7) ?? lastHolding(shravana, _shukla, 6),
      events: [
        ('sapta_paramsthan_vrat_prarambh', 'vrat', atEnd: false),
        ('sapta_paramsthan_vrat_purna', 'vrat', atEnd: true),
      ]);
}

/// Shravana Shukla 13 to Purnima. A kshaya anywhere in Shukla 13-15 moves the
/// start to Shukla 12, else Shukla 13, else the day before the first of 14 and 15.
List<FestivalOccurrence> _rakshabandhanVrat(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final shravana = amantaMonthInYear(days, year, _shravana);
  CivilDate? first(int tithi) => firstHolding(shravana, _shukla, tithi);
  final anyKshaya = [13, 14, 15].any((t) => first(t) == null);
  return _pair(entry, year,
      start: anyKshaya ? first(12) ?? first(13) ?? _dayBefore(days, first(14) ?? first(15)) : first(13),
      end: lastHolding(shravana, _shukla, 15) ?? lastHolding(shravana, _shukla, 14),
      events: [
        ('rakshabandhan_vrat_prarambh', 'vrat', atEnd: false),
        ('rakshabandhan_vrat_purna', 'mahaparv', atEnd: true),
      ]);
}

/// Shravana Shukla 10 to Bhadrapada Krishna 10.
List<FestivalOccurrence> _akshayaNidhi(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final shravana = amantaMonthInYear(days, year, _shravana);
  final bhadrapada = amantaMonthInYear(days, year, _bhadrapada);
  return _pair(entry, year,
      start: firstHolding(shravana, _shukla, 10) ?? lastHolding(shravana, _shukla, 9),
      end: lastHolding(bhadrapada, _krishna, 10) ?? lastHolding(bhadrapada, _krishna, 9),
      events: [
        ('akshaya_nidhi_vrat_prarambh', 'vrat', atEnd: false),
        ('akshaya_nidhi_vrat_purna', 'vrat', atEnd: true),
      ]);
}

/// Bhadrapada Shukla 11 to Shukla 14.
List<FestivalOccurrence> _anantChaturdashi(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final bhadrapada = amantaMonthInYear(days, year, _bhadrapada);
  return _pair(entry, year,
      start: firstHolding(bhadrapada, _shukla, 11) ?? lastHolding(bhadrapada, _shukla, 10),
      end: lastHolding(bhadrapada, _shukla, 14) ?? lastHolding(bhadrapada, _shukla, 13),
      events: [
        ('anant_vrat_prarambh', 'vrat', atEnd: false),
        ('anant_chaturdashi_purna', 'mahaparv', atEnd: true),
      ]);
}

/// Bhadrapada Shukla 13 to Purnima, for two vrats at once.
List<FestivalOccurrence> _ratnatrayaSankatHaran(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final bhadrapada = amantaMonthInYear(days, year, _bhadrapada);
  return _pair(entry, year,
      start: firstHolding(bhadrapada, _shukla, 13) ?? lastHolding(bhadrapada, _shukla, 12),
      end: lastHolding(bhadrapada, _shukla, 15) ?? lastHolding(bhadrapada, _shukla, 14),
      events: [
        ('ratnatraya_vrat_prarambh', 'mahaparv_vrat', atEnd: false),
        ('sankat_haran_vrat_prarambh', 'vrat', atEnd: false),
        ('ratnatraya_vrat_purna', 'mahaparv_vrat', atEnd: true),
        ('sankat_haran_vrat_purna', 'vrat', atEnd: true),
      ]);
}

/// Ashwin Shukla 1 (kshaya: Ashwin's last Amavasya) to Kartika Krishna 1
/// (kshaya: Ashwin's last Purnima).
List<FestivalOccurrence> _shraddha(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final ashwin = amantaMonthInYear(days, year, _ashwin);
  final kartika = amantaMonthInYear(days, year, _kartika);
  return _pair(entry, year,
      start: firstHolding(ashwin, _shukla, 1) ?? lastHolding(ashwin, _krishna, 15),
      end: lastHolding(kartika, _krishna, 1) ?? lastHolding(ashwin, _shukla, 15),
      events: [
        ('shraddha_vrat_prarambh', 'vrat', atEnd: false),
        ('shraddha_vrat_purna', 'vrat', atEnd: true),
      ]);
}

/// Shukla 7 to Purnima in Chaitra and in Ashwin, each season on its own.
List<FestivalOccurrence> _navapadOli(FestivalEntry entry, List<FestivalDay> days, {required int year}) => [
  for (final (monthIndex, season) in const [(_chaitra, 'chaitra'), (_ashwin, 'ashwin')])
    ...() {
      final month = amantaMonthInYear(days, year, monthIndex);
      return _pair(entry, year,
          start: firstHolding(month, _shukla, 7) ?? lastHolding(month, _shukla, 6),
          end: lastHolding(month, _shukla, 15) ?? lastHolding(month, _shukla, 14),
          events: [
            ('navapad_oli_vrat_prarambh_$season', 'mahaparv_vrat', atEnd: false),
            ('navapad_oli_vrat_purna_$season', 'mahaparv_vrat', atEnd: true),
          ]);
    }(),
];

/// Python `MonthlyVrat`, which only the Pratham Jeth Jinvani entry uses: it
/// reads Jyeshtha whatever the entry's month. Jyeshtha Krishna 1 (kshaya: the
/// day before the month's first day) and Shukla Purnima (kshaya: the last
/// Shukla 14) are each emitted when found, named after the entry.
List<FestivalOccurrence> _prathamJethJinvani(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final jyeshtha = amantaMonthInYear(days, year, _jyeshtha);
  if (jyeshtha.isEmpty) return const [];
  final start = firstHolding(jyeshtha, _krishna, 1) ?? _dayBefore(days, jyeshtha.first.date);
  final end = lastHolding(jyeshtha, _shukla, 15) ?? lastHolding(jyeshtha, _shukla, 14);
  return [
    if (start != null) _occurrence(entry, '${entry.id}_start_$year', 'monthly_vrat', start),
    if (end != null) _occurrence(entry, '${entry.id}_end_$year', 'monthly_vrat', end),
  ];
}

/// Python's `snapshots[index - 1]`: the day before [date] in the window, or
/// [date] itself when it is the window's first day.
CivilDate? _dayBefore(List<FestivalDay> days, CivilDate? date) {
  if (date == null) return null;
  return days.first.date == date ? date : date.previous();
}

FestivalOccurrence _occurrence(FestivalEntry entry, String id, String category, CivilDate date) => FestivalOccurrence(
  id: id,
  occurrenceId: id,
  ruleId: entry.id,
  category: category,
  name: entry.name,
  nameHindi: entry.nameHindi,
  start: date,
  end: date,
);
