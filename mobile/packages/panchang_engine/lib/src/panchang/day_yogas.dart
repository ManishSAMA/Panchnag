/// The day's yogas, as the Muhurat section's Yoga screen reads them (Python
/// `yoga_service.detect_all_yogas_for_day` and `yoga_engine`): the Dainika
/// yogas of weekday + tithi / nakshatra, the Aanandadi yoga of each Moon
/// nakshatra, Ravi Yoga and Jwalamukhi. The rule tables come from
/// `yoga_rules.py` through `yoga_rules.g.dart`.
library;

import 'dart:convert';
import 'dart:math' as math;

import 'yoga_rules.g.dart';

enum DayYogaKind { dainika, aanandadi, ravi, jwalamukhi }

enum YogaNature { shubh, ashubh }

/// A tithi or nakshatra within the day, in UT Julian Days.
typedef Segment = ({int index, double start, double end});

typedef JdDayYoga = ({
  DayYogaKind kind,
  String name,
  YogaNature nature,
  double start,
  double end,
  bool isNullified,
  bool cancelled,
  bool diminished,
  ({double start, double end})? varjya,
});

/// Python steps 30 s past each end before reading the next element.
const double _nudgeDays = 30 / 86400;

/// Every element from [sunrise] to [nextSunrise], each from the previous
/// one's end (the first from sunrise) to its own, the last cut at [nextSunrise].
List<Segment> daySegments(double sunrise, double nextSunrise, int Function(double) at, double Function(double) end) {
  final segments = <Segment>[];
  var (start, probe) = (sunrise, sunrise);
  while (start < nextSunrise) {
    final ends = end(probe);
    segments.add((index: at(probe), start: start, end: math.min(ends, nextSunrise)));
    (start, probe) = (ends, ends + _nudgeDays);
  }
  return segments;
}

final class _DainikaRule {
  _DainikaRule(Map<String, Object?> json)
    : name = json['name']! as String,
      nature = YogaNature.values.byName(json['nature']! as String),
      trigger = json['trigger']! as String,
      varaMap = {
        for (final MapEntry(:key, :value) in (json['vara_map']! as Map<String, Object?>).entries)
          int.parse(key): value is List ? value.cast<int>().toSet() : const <int>{},
      },
      tithiValues = ((json['tithi_values'] ?? const <Object?>[]) as List<Object?>).cast<int>().toSet(),
      nakshatraValues = ((json['nakshatra_values'] ?? const <Object?>[]) as List<Object?>).cast<int>().toSet();

  final String name, trigger;
  final YogaNature nature;

  /// Weekday (0 = Sunday) to the tithis or nakshatras it takes; a
  /// tithi_and_nakshatra rule names only its weekdays.
  final Map<int, Set<int>> varaMap;
  final Set<int> tithiValues, nakshatraValues;
}

final class _AanandadiYoga {
  _AanandadiYoga(Map<String, Object?> json)
    : name = json['name']! as String,
      nature = YogaNature.values.byName(json['nature']! as String),
      varjyaMinutes = switch (json['varjya']) {
        [final int ghati, final int pala] => ghati * 24 + pala * 24 / 60,
        _ => null,
      };

  final String name;
  final YogaNature nature;

  /// Minutes from the yoga's start to avoid (1 ghati = 24 min, 1 pala = 24 s);
  /// null for none and for a whole-day varjya, as Python's muhurat day reads it.
  final double? varjyaMinutes;
}

final _rules = jsonDecode(yogaRulesJson) as Map<String, Object?>;
final _dainikaRules = [for (final r in (_rules['dainika']! as List<Object?>)) _DainikaRule(r! as Map<String, Object?>)];
final _aanandadiYogas = [
  for (final y in (_rules['aanandadi']! as List<Object?>)) _AanandadiYoga(y! as Map<String, Object?>),
];

/// The yogas whose time overlap makes an inauspicious yoga harmless.
const _supremeYogas = {'Guru Pushya Amrit', 'Ravi Pushya Amrit', 'Sarvartha Siddhi', 'Amrit Siddhi'};

/// Sun-to-Moon nakshatra counts that make Ravi Yoga (Ruchika Publications, p. 112).
const _raviYogaDistances = {4, 6, 9, 10, 13, 20};

/// On a Sunday the Moon in Ashlesha or Magha turns Ravi Yoga into these.
const _sundayRaviExceptions = {9: 'Vajra Yog', 10: 'Mudgar Yog'};

/// (tithi 1-30, nakshatra) pairs that make Jwalamukhi.
const _jwalamukhiPairs = {(1, 19), (5, 2), (8, 3), (9, 4), (10, 9)};

({double start, double end})? _overlap(Segment a, Segment b) {
  final start = math.max(a.start, b.start), end = math.min(a.end, b.end);
  return end > start ? (start: start, end: end) : null;
}

typedef _Match = ({String name, YogaNature nature, double start, double end});

List<_Match> _matchDainika(int vara, List<Segment> tithis, List<Segment> nakshatras) => [
  for (final rule in _dainikaRules)
    if (rule.varaMap[vara] case final allowed?)
      ...switch (rule.trigger) {
        'tithi_and_nakshatra' => [
          for (final t in tithis.where((t) => rule.tithiValues.contains(t.index)))
            for (final n in nakshatras.where((n) => rule.nakshatraValues.contains(n.index)))
              if (_overlap(t, n) case final o?) (name: rule.name, nature: rule.nature, start: o.start, end: o.end),
        ],
        'tithi' => [
          for (final t in tithis.where((t) => allowed.contains(t.index)))
            (name: rule.name, nature: rule.nature, start: t.start, end: t.end),
        ],
        _ => [
          for (final n in nakshatras.where((n) => allowed.contains(n.index)))
            (name: rule.name, nature: rule.nature, start: n.start, end: n.end),
        ],
      },
];

bool _overlapsAny(_Match yoga, List<_Match> windows) =>
    windows.any((w) => yoga.start < w.end && w.start < yoga.end);

/// The Aanandadi yoga (1-28) of a Moon nakshatra on a weekday: Abhijit takes
/// place 22 in the 28-nakshatra count, so Shravana (22) on shift up one.
int aanandadiIndex(int nakshatra, int vara) {
  final n28 = nakshatra <= 21 ? nakshatra : nakshatra + 1;
  final y = (n28 - vara * 4) % 28;
  return y == 0 ? 28 : y;
}

/// Every yoga of the day in Python's order: Dainika, Aanandadi, Ravi, Jwalamukhi.
List<JdDayYoga> dayYogas({
  required int vara,
  required List<Segment> tithis,
  required List<Segment> nakshatras,
  required int sunNakshatra,
}) {
  final dainika = _matchDainika(vara, tithis, nakshatras);
  final hasSarvartha = dainika.any((m) => m.name == 'Sarvartha Siddhi');
  bool cancelled(_Match m) => m.name == 'Dusht Tithi' && hasSarvartha;
  final activeDusht = dainika.any((m) => m.name == 'Dusht Tithi' && !cancelled(m));
  final supreme = [for (final m in dainika) if (_supremeYogas.contains(m.name) && !cancelled(m)) m];
  bool nullified(_Match m) => m.nature == YogaNature.ashubh && !cancelled(m) && _overlapsAny(m, supreme);

  JdDayYoga yoga(DayYogaKind kind, _Match m, {bool isNullified = false, bool isCancelled = false, bool isDiminished = false, double? varjyaMinutes}) => (
    kind: kind,
    name: m.name,
    nature: m.nature,
    start: m.start,
    end: m.end,
    isNullified: isNullified,
    cancelled: isCancelled,
    diminished: isDiminished,
    varjya: varjyaMinutes == null ? null : (start: m.start, end: m.start + varjyaMinutes / 1440),
  );

  return [
    for (final m in dainika)
      yoga(
        DayYogaKind.dainika,
        m,
        isNullified: nullified(m),
        isCancelled: cancelled(m),
        isDiminished: m.name == 'Amrit Siddhi' && activeDusht && !hasSarvartha,
      ),
    for (final n in nakshatras)
      if (_aanandadiYogas[aanandadiIndex(n.index, vara) - 1] case final a)
        yoga(
          DayYogaKind.aanandadi,
          (name: a.name, nature: a.nature, start: n.start, end: n.end),
          isNullified: nullified((name: a.name, nature: a.nature, start: n.start, end: n.end)),
          varjyaMinutes: a.varjyaMinutes,
        ),
    for (final n in nakshatras)
      if (_raviYogaDistances.contains((n.index - sunNakshatra) % 27 + 1))
        yoga(DayYogaKind.ravi, switch (vara == 0 ? _sundayRaviExceptions[n.index] : null) {
          final exception? => (name: 'Ravi Yoga ($exception)', nature: YogaNature.ashubh, start: n.start, end: n.end),
          null => (name: 'Ravi Yoga', nature: YogaNature.shubh, start: n.start, end: n.end),
        }),
    for (final t in tithis)
      for (final n in nakshatras)
        if (_jwalamukhiPairs.contains((t.index, n.index)))
          if (_overlap(t, n) case final o?)
            yoga(DayYogaKind.jwalamukhi, (name: 'Jwalamukhi', nature: YogaNature.ashubh, start: o.start, end: o.end)),
  ];
}
