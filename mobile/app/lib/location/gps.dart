/// One GPS fix on request: no background tracking, and no network needed.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:geolocator/geolocator.dart';

sealed class GpsOutcome {
  const GpsOutcome();
}

final class GpsFix extends GpsOutcome {
  const GpsFix({required this.lat, required this.lon, required this.timezone});

  final double lat;
  final double lon;

  /// The phone's own time zone, an IANA name (mobile-ui-design.md §3.0).
  final String timezone;
}

/// The user refused location permission, now or for good.
final class GpsDenied extends GpsOutcome {
  const GpsDenied();
}

/// Location is switched off on the phone.
final class GpsOff extends GpsOutcome {
  const GpsOff();
}

/// No fix arrived in time, and the phone had no recent one.
final class GpsNoFix extends GpsOutcome {
  const GpsNoFix();
}

typedef GpsLocator = Future<GpsOutcome> Function();

final gpsLocatorProvider = Provider<GpsLocator>((ref) => locateByGps);

/// Only coarse permission is asked for: a kilometre or two moves sunrise by
/// seconds, and the prompt is gentler for elders.
Future<GpsOutcome> locateByGps() async {
  if (!await Geolocator.isLocationServiceEnabled()) return const GpsOff();
  final permission = switch (await Geolocator.checkPermission()) {
    LocationPermission.denied => await Geolocator.requestPermission(),
    final granted => granted,
  };
  if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
    return const GpsDenied();
  }
  final position = await _currentPosition() ?? await Geolocator.getLastKnownPosition();
  if (position == null) return const GpsNoFix();
  final zone = await FlutterTimezone.getLocalTimezone();
  return GpsFix(lat: position.latitude, lon: position.longitude, timezone: zone.identifier);
}

Future<Position?> _currentPosition() async {
  try {
    return await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, timeLimit: Duration(seconds: 30)),
    );
  } on TimeoutException {
    return null;
  }
}
