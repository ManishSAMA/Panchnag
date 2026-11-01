/// How the engine's festivals read on Today and Month: the mark each registry
/// category gets, the lines shown for a date, and the upcoming dates.
library;

import 'package:panchang_engine/panchang_engine.dart';

import 'panchang_text.dart';

/// DESIGN.md's four marks, in the order a cell and a list show them.
enum FestivalKind {
  mahaparva,
  kalyanak,
  parva,
  vrat;

  /// Green rather than red: Today's vrat band, not its parva band.
  bool get isVrat => this == vrat;
}

const _kalyanak = {'kalyanak', 'janam_kalyanak'};
const _mahaparva = {'mahaparv', 'festival', 'utsav'};
const _vrat = {'vrat', 'monthly_vrat', 'tap_vrat', 'parva_vrat', 'mahaparv_vrat'};
const _parva = {'parva', 'jayanti', 'punyatithi', 'punya_tithi', 'shastra', 'auspicious', 'poojan', 'parv_vidhi'};

/// The categories [kindOf] maps on purpose; any other falls back to a parva dot.
const namedCategories = {..._kalyanak, ..._mahaparva, ..._vrat, ..._parva};

/// Every vrat goes green, Navapad Oli and the Namokar chain included, so the
/// mahaparva square stays rare (decided 2026-10-31).
FestivalKind kindOf(String category) => switch (category) {
  _ when _kalyanak.contains(category) => FestivalKind.kalyanak,
  _ when _mahaparva.contains(category) => FestivalKind.mahaparva,
  _ when _vrat.contains(category) => FestivalKind.vrat,
  _ => FestivalKind.parva,
};

List<FestivalOccurrence> festivalsOn(Iterable<FestivalOccurrence> festivals, CivilDate date) => [
  for (final f in festivals)
    if (f.start.compareTo(date) <= 0 && f.end.compareTo(date) >= 0) f,
];

String festivalName(FestivalOccurrence f, Lang lang) =>
    lang == Lang.hi && f.nameHindi.isNotEmpty ? f.nameHindi : f.name;

typedef FestivalLine = ({String name, FestivalKind kind, CivilDate start, CivilDate end});

/// Registry entries that name one event, one per school or source. On a date
/// they share they make one line, named after [shown] when it is there
/// (decided 2026-10-31). The display alone merges them, so the engine keeps
/// matching the Python reference.
const sameEvents = <({String shown, Set<String> also})>[
  (
    shown: 'diwali',
    also: {
      'mahavir_nirvana_deepavali',
      'kartika_amavasya_mahavira_nirvana',
      'shri_mahavir_swami_ji___moksha_kalyanak__the_nirvana_liberation_of_lord_mahavira__celebrated_as_jain_diwali',
      'shri_mahavira_ji___liberation_kalyanak_15_vrindavan_uttarapurana_ashadhara',
    },
  ),
  (shown: 'raksha_bandhan', also: {'rakshabandhan_vrat', 'shravana_purnima_rakshabandhan'}),
  (shown: 'shri_parshvanath_ji___birth_kalyanak_11_vrindavan_uttarapurana_ashadhara', also: {'parshvanath_jayanti'}),
];

final _groupOf = {
  for (final group in sameEvents)
    for (final rule in {group.shown, ...group.also}) rule: group.shown,
};

/// One line per event: an entry's events share its name until Phase 6 titles
/// them, and [sameEvents] joins entries. By kind, then in the engine's order.
List<FestivalLine> festivalLines(Iterable<FestivalOccurrence> festivals, Lang lang) {
  final byEvent = <String, List<FestivalOccurrence>>{};
  for (final f in festivals) {
    (byEvent[_groupOf[f.ruleId] ?? festivalName(f, lang)] ??= []).add(f);
  }
  final lines = [for (final same in byEvent.values) _lineOf(same, lang)].indexed.toList()
    ..sort(
      (a, b) => switch (a.$2.kind.index.compareTo(b.$2.kind.index)) {
        0 => a.$1.compareTo(b.$1),
        final byKind => byKind,
      },
    );
  return [for (final (_, line) in lines) line];
}

FestivalLine _lineOf(List<FestivalOccurrence> same, Lang lang) {
  final named = same.firstWhere((f) => _groupOf[f.ruleId] == f.ruleId, orElse: () => same.first);
  final kind = same.map((f) => kindOf(f.category)).reduce((a, b) => a.index <= b.index ? a : b);
  return (name: festivalName(named, lang), kind: kind, start: named.start, end: named.end);
}

/// A Month cell has room for three marks.
List<FestivalKind> cellMarks(List<FestivalLine> lines) => {for (final line in lines) line.kind}.take(3).toList();

typedef FestivalDate = ({CivilDate date, List<FestivalLine> lines});

/// The next [count] dates after [after] on which a parva, kalyanak or mahaparva
/// starts. Vrats are left out: they fall on nearly every date. [festivals] come
/// in date order, as `PanchangEngine.festivals` returns them.
List<FestivalDate> upcomingFestivals(
  Iterable<FestivalOccurrence> festivals, {
  required CivilDate after,
  required Lang lang,
  int count = 4,
}) {
  final starting = <CivilDate, List<FestivalOccurrence>>{};
  for (final f in festivals) {
    if (f.start.compareTo(after) > 0 && !kindOf(f.category).isVrat) (starting[f.start] ??= []).add(f);
  }
  return [for (final date in starting.keys.take(count)) (date: date, lines: festivalLines(starting[date]!, lang))];
}

/// The Festivals tab's chips: every mark, or one.
enum FestivalFilter {
  all(null),
  mahaparva(FestivalKind.mahaparva),
  kalyanak(FestivalKind.kalyanak),
  parva(FestivalKind.parva),
  vrat(FestivalKind.vrat);

  const FestivalFilter(this.kind);

  final FestivalKind? kind;

  bool shows(FestivalKind kind) => this.kind == null || this.kind == kind;
}

/// The Festivals tab's dates from [from] on: each festival on its first day,
/// a span already under way on [from] itself. A merged event is filed under
/// its line's mark, so a filter never shows a line under a mark it lacks.
List<FestivalDate> festivalDates(
  Iterable<FestivalOccurrence> festivals, {
  required CivilDate from,
  required Lang lang,
  FestivalFilter filter = FestivalFilter.all,
}) {
  final byDate = <CivilDate, List<FestivalOccurrence>>{};
  for (final f in festivals) {
    if (f.end.compareTo(from) >= 0) (byDate[f.start.compareTo(from) < 0 ? from : f.start] ??= []).add(f);
  }
  final dates = byDate.keys.toList()..sort((a, b) => a.compareTo(b));
  return [
    for (final date in dates)
      if (festivalLines(byDate[date]!, lang).where((l) => filter.shows(l.kind)).toList() case final lines
          when lines.isNotEmpty)
        (date: date, lines: lines),
  ];
}

String dateRange(CivilDate start, CivilDate end, Lang lang) => start.month == end.month
    ? '${start.day}–${shortDate(end, lang)}'
    : '${shortDate(start, lang)} – ${shortDate(end, lang)}';
