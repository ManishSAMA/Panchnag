/// The app's one call into the engine (`PanchangEngine.day`), plus the
/// tithi-boundary note, which is a display choice rather than a calendar rule.
library;

import 'package:panchang_engine/panchang_engine.dart';

/// Plain values only, so a request can cross into a background isolate.
final class DayRequest {
  const DayRequest({
    required this.date,
    required this.lat,
    required this.lon,
    required this.timezone,
    this.rule = SunriseRule.modern,
  });

  final CivilDate date;
  final double lat;
  final double lon;
  final String timezone;
  final SunriseRule rule;

  @override
  bool operator ==(Object other) =>
      other is DayRequest &&
      other.date == date &&
      other.lat == lat &&
      other.lon == lon &&
      other.timezone == timezone &&
      other.rule == rule;

  @override
  int get hashCode => Object.hash(date, lat, lon, timezone, rule);
}

PanchangDay readDay(DayRequest request) => const PanchangEngine().day(
  location: Location(lat: request.lat, lon: request.lon, timezone: request.timezone),
  date: request.date,
  sunriseRule: request.rule,
);

/// A tithi change close to the reference instant: [isStart] when the Jain tithi
/// began shortly before it, otherwise it ends shortly after.
typedef TithiBoundary = ({DateTime at, bool isStart, Duration gap});

/// How close to the reference instant a tithi change gets a note
/// (mobile-ui-design.md §3.1; a proposal until tied to the parity tolerance).
const Duration boundaryWindow = Duration(minutes: 45);

/// The nearer of the Jain tithi's start and end, if within [boundaryWindow] of its reference instant.
TithiBoundary? tithiBoundary(JainTithi jain) {
  final near = [
    for (final (at, isStart) in [(jain.startsAt, true), (jain.endsAt, false)])
      if (at.difference(jain.reference).abs() <= boundaryWindow)
        (at: at, isStart: isStart, gap: at.difference(jain.reference).abs()),
  ]..sort((a, b) => a.gap.compareTo(b.gap));
  return near.firstOrNull;
}
