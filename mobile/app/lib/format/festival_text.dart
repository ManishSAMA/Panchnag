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

/// One line per name, since a rule's events share their entry's name until
/// Phase 6 titles them; by kind, then in the engine's order.
List<FestivalLine> festivalLines(Iterable<FestivalOccurrence> festivals, Lang lang) {
  final byName = <String, FestivalLine>{};
  for (final f in festivals) {
    byName.putIfAbsent(
      festivalName(f, lang),
      () => (name: festivalName(f, lang), kind: kindOf(f.category), start: f.start, end: f.end),
    );
  }
  final lines = byName.values.indexed.toList()
    ..sort(
      (a, b) => switch (a.$2.kind.index.compareTo(b.$2.kind.index)) {
        0 => a.$1.compareTo(b.$1),
        final byKind => byKind,
      },
    );
  return [for (final (_, line) in lines) line];
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

String dateRange(CivilDate start, CivilDate end, Lang lang) => start.month == end.month
    ? '${start.day}–${shortDate(end, lang)}'
    : '${shortDate(start, lang)} – ${shortDate(end, lang)}';
