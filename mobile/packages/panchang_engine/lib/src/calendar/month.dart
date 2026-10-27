/// Lunar months: new moons, Sankrantis, and the Amanta and Purnimanta month
/// names (Python `panchang.py` `find_new_moon_*`, `find_sankrantis_in_range`,
/// `get_hindu_month`, `get_purnimanta_month`).
library;

import '../astro/boundary.dart';
import '../astro/sidereal.dart';
import '../panchang/elements.dart';

/// Index 0-11 matches the Sun sign the month's Sankranti enters
/// (Mesha -> Chaitra ... Meena -> Phalguna), as in Python `HINDU_MONTH_NAMES`.
const List<String> lunarMonthNames = [
  'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha', //
  'Shravana', 'Bhadrapada', 'Ashwin', 'Kartika',
  'Agrahayana', 'Pausha', 'Magha', 'Phalguna',
];

final class LunarMonth {
  const LunarMonth({required this.index, required this.isAdhika});

  final int index;

  /// An Adhik (leap) month: a lunar month with no Sankranti in it.
  final bool isAdhika;

  String get name => isAdhika ? 'Adhika ${lunarMonthNames[index]}' : lunarMonthNames[index];

  @override
  bool operator ==(Object other) => other is LunarMonth && other.index == index && other.isAdhika == isAdhika;

  @override
  int get hashCode => Object.hash(index, isAdhika);

  @override
  String toString() => name;
}

/// Elongation never grows faster than this, so stepping by remaining/16 days
/// can never pass the new moon.
const double _maxElongationRate = 16;
const double _minElongationRate = 9.5;

/// Python steps 30 s past each end before asking for the next tithi.
const double _nudgeDays = 30 / 86400;

/// First new moon (end of tithi 30) strictly after [jdUt].
double newMoonAfter(double jdUt) {
  var instant = jdUt + (360 - elongation(jdUt)) / _maxElongationRate;
  while (true) {
    final end = tithiEnd(instant);
    if (tithiAt(instant) == 30) return end;
    instant = end + _nudgeDays;
  }
}

/// Last new moon strictly before [jdUt].
double newMoonBefore(double jdUt) {
  // At least one new moon lies after this, at or before the one wanted.
  final earliest = jdUt - elongation(jdUt) / _minElongationRate - 1;
  var newMoon = newMoonAfter(earliest);
  for (var next = newMoonAfter(newMoon + 1); next < jdUt; next = newMoonAfter(next + 1)) {
    newMoon = next;
  }
  return newMoon;
}

int _sunSign(double jdUt) => siderealSunLongitude(jdUt) ~/ 30 % 12;

/// Sun signs (0-11) entered at each Sankranti in (start, end], in order.
List<int> sankrantisBetween(double start, double end) {
  final signs = <int>[];
  var instant = start;
  while (true) {
    final ingress = nextAngleBoundary(instant, siderealSunLongitude, 30, minRate: 0.95, maxRate: 1.02);
    if (ingress > end) return signs;
    signs.add((_sunSign(instant) + 1) % 12);
    instant = ingress + _nudgeDays;
  }
}

/// The Amanta month spanning [newMoon, nextNewMoon): named after the Sankranti
/// inside it, or Adhika (named after the next month's) when it has none.
LunarMonth amantaMonthBetween(double newMoon, double nextNewMoon, {required double fallbackJd}) {
  final signs = sankrantisBetween(newMoon, nextNewMoon);
  if (signs.isNotEmpty) return LunarMonth(index: signs.first, isAdhika: false);

  final following = sankrantisBetween(nextNewMoon, newMoonAfter(nextNewMoon + 1));
  final index = following.isNotEmpty ? following.first : _sunSign(fallbackJd);
  return LunarMonth(index: index, isAdhika: true);
}

/// The Amanta (new-moon to new-moon) month holding at [jdUt].
LunarMonth amantaMonth(double jdUt) {
  final newMoon = newMoonBefore(jdUt);
  return amantaMonthBetween(newMoon, newMoonAfter(newMoon + 1), fallbackJd: jdUt);
}

/// One Amanta month: [start] and [end] are consecutive new moons.
typedef LunarMonthSpan = ({double start, double end, LunarMonth month});

/// Every Amanta month overlapping [from, to), in order. Naming a month costs
/// about 40 ms, so a screen or a long run names each month once and looks
/// instants up with [amantaLookup].
List<LunarMonthSpan> lunarMonthsBetween(double from, double to) {
  final spans = <LunarMonthSpan>[];
  var newMoon = newMoonBefore(from);
  while (spans.isEmpty || spans.last.end <= to) {
    final next = newMoonAfter(newMoon + 1);
    spans.add((
      start: newMoon,
      end: next,
      month: amantaMonthBetween(newMoon, next, fallbackJd: (newMoon + next) / 2),
    ));
    newMoon = next;
  }
  return spans;
}

/// The Amanta month at an instant, read from [spans]. Throws [RangeError]
/// outside them.
LunarMonth Function(double) amantaLookup(List<LunarMonthSpan> spans) => (double jdUt) {
  var (lo, hi) = (0, spans.length - 1);
  while (lo <= hi) {
    final mid = (lo + hi) ~/ 2;
    final span = spans[mid];
    if (jdUt < span.start) {
      hi = mid - 1;
    } else if (jdUt >= span.end) {
      lo = mid + 1;
    } else {
      return span.month;
    }
  }
  throw RangeError('JD $jdUt is outside the lunar months given.');
};

/// A Krishna paksha has at most 15 tithis left (under 16.8 days) and the next
/// month lasts at least 29.2 days, so this many days on always lands in the
/// next Amanta month. Python asks for the new moon + 1 day; the month is the same.
const double _intoNextMonthDays = 17;

/// The Purnimanta month holding at [jdUt]. A Shukla paksha is named as in
/// Amanta; a Krishna paksha belongs to the month whose Shukla paksha it runs
/// into, which also carries that month's Adhik flag.
LunarMonth purnimantaMonth(double jdUt, {LunarMonth Function(double) amanta = amantaMonth}) =>
    tithiAt(jdUt) <= 15 ? amanta(jdUt) : amanta(jdUt + _intoNextMonthDays);
