/// The app's call into the festival engine (`PanchangEngine.festivals`), kept
/// per isolate: a year costs about a second or more on a phone.
library;

import 'package:panchang_engine/panchang_engine.dart';

/// Plain values only, so a request can cross into a background isolate.
final class FestivalRequest {
  const FestivalRequest({
    required this.year,
    required this.lat,
    required this.lon,
    required this.timezone,
    required this.profile,
    this.rule = SunriseRule.modern,
  });

  final int year;
  final double lat;
  final double lon;
  final String timezone;

  /// A registry profile id (`Tradition.id`).
  final String profile;
  final SunriseRule rule;

  @override
  bool operator ==(Object other) =>
      other is FestivalRequest &&
      other.year == year &&
      other.lat == lat &&
      other.lon == lon &&
      other.timezone == timezone &&
      other.profile == profile &&
      other.rule == rule;

  @override
  int get hashCode => Object.hash(year, lat, lon, timezone, profile, rule);
}

/// The memory cache of plans/mobile-app-flutter.md §1a; a disk cache joins with reminders.
final Map<FestivalRequest, List<FestivalOccurrence>> _years = {};

List<FestivalOccurrence> readFestivals(FestivalRequest request, {required FestivalRegistry registry}) =>
    _years[request] ??= List.unmodifiable(
      const PanchangEngine().festivals(
        location: Location(lat: request.lat, lon: request.lon, timezone: request.timezone),
        year: request.year,
        profile: request.profile,
        registry: registry,
        sunriseRule: request.rule,
      ),
    );
