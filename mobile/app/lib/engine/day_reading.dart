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

/// A day's Panchang section (yoga, karana, Rashis, gata), read apart from
/// the day so the Month tab never pays for it.
final class SectionRequest {
  const SectionRequest(this.day);

  final DayRequest day;

  @override
  bool operator ==(Object other) => other is SectionRequest && other.day == day;

  @override
  int get hashCode => day.hashCode;
}

PanchangSection readSection(SectionRequest request) => const PanchangEngine().section(
  location: Location(lat: request.day.lat, lon: request.day.lon, timezone: request.day.timezone),
  date: request.day.date,
  sunriseRule: request.day.rule,
);

/// A day's Muhurat windows and yogas, read apart from the day, as the
/// section is.
final class MuhuratRequest {
  const MuhuratRequest(this.day);

  final DayRequest day;

  @override
  bool operator ==(Object other) => other is MuhuratRequest && other.day == day;

  @override
  int get hashCode => Object.hash(MuhuratRequest, day);
}

PanchangMuhurat readMuhurat(MuhuratRequest request) => const PanchangEngine().muhurat(
  location: Location(lat: request.day.lat, lon: request.day.lon, timezone: request.day.timezone),
  date: request.day.date,
  sunriseRule: request.day.rule,
);

/// Every day of a Gregorian month, for the Month tab; plain values, like [DayRequest].
final class MonthRequest {
  const MonthRequest({
    required this.year,
    required this.month,
    required this.lat,
    required this.lon,
    required this.timezone,
    this.rule = SunriseRule.modern,
  });

  final int year;
  final int month;
  final double lat;
  final double lon;
  final String timezone;
  final SunriseRule rule;

  @override
  bool operator ==(Object other) =>
      other is MonthRequest &&
      other.year == year &&
      other.month == month &&
      other.lat == lat &&
      other.lon == lon &&
      other.timezone == timezone &&
      other.rule == rule;

  @override
  int get hashCode => Object.hash(year, month, lat, lon, timezone, rule);
}

List<PanchangDay> readMonth(MonthRequest request) => const PanchangEngine().month(
  location: Location(lat: request.lat, lon: request.lon, timezone: request.timezone),
  year: request.year,
  month: request.month,
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
