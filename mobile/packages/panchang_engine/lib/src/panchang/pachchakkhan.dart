/// Pachchakkhan times from the day's sunrise and sunset. Dart only: the Python
/// engine has no pachchakkhan, so these are checked by their defining rules
/// (plans/mobile-ui-design.md §3 · Pachchakkhan).
library;

/// The pachchakkhans that may be completed only after a clock time.
enum TimedPachchakkhan { navkarsi, porsi, sadhPorsi, purimaddh, avaddh }

/// Navkarsi is a fixed 48 minutes (2 ghati); the others are fractions of the
/// sunrise-to-sunset day.
const double _navkarsiDays = 48 / 1440;
const Map<TimedPachchakkhan, double> _dayFractions = {
  TimedPachchakkhan.porsi: 1 / 4,
  TimedPachchakkhan.sadhPorsi: 3 / 8,
  TimedPachchakkhan.purimaddh: 1 / 2,
  TimedPachchakkhan.avaddh: 3 / 4,
};

typedef Completion = ({TimedPachchakkhan kind, double at});

/// One day's pachchakkhan instants (Julian Days, UT). Rounding to the minute
/// is the formatter's job.
final class PachchakkhanTimes {
  const PachchakkhanTimes({required this.completions, required this.evening, required this.parana});

  /// The five completion times in order; each may be completed from its instant on.
  final List<Completion> completions;

  /// Chauvihar, Tivihar and Duvihar must be taken before this instant: sunset.
  final double evening;

  /// Ayambil and Upvas are completed at the next day's Navkarsi.
  final double parana;

  /// The first pachchakkhan still ahead of [now], or null once Avaddh has passed.
  TimedPachchakkhan? nextAt(double now) {
    for (final completion in completions) {
      if (completion.at > now) return completion.kind;
    }
    return null;
  }
}

PachchakkhanTimes pachchakkhanTimes({required double sunrise, required double sunset, required double nextSunrise}) {
  double into(double fraction) => sunrise + (sunset - sunrise) * fraction;
  return PachchakkhanTimes(
    completions: [
      (kind: TimedPachchakkhan.navkarsi, at: sunrise + _navkarsiDays),
      for (final MapEntry(:key, :value) in _dayFractions.entries) (kind: key, at: into(value)),
    ],
    evening: sunset,
    parana: nextSunrise + _navkarsiDays,
  );
}
