import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'cities.dart';

/// Overridden in main with the loaded instance, so reads are synchronous.
final preferencesProvider = Provider<SharedPreferences>(
  (ref) => throw StateError('preferencesProvider must be overridden with the loaded SharedPreferences.'),
);

const _cityKey = 'location.city';
const _gpsLatKey = 'location.gps.lat';
const _gpsLonKey = 'location.gps.lon';
const _gpsZoneKey = 'location.gps.timezone';

/// The chosen place, or null until the user picks one: the app never assumes a
/// location (PRODUCT.md principle 4).
final locationProvider = NotifierProvider<LocationNotifier, Place?>(LocationNotifier.new);

final class LocationNotifier extends Notifier<Place?> {
  @override
  Place? build() {
    final prefs = ref.read(preferencesProvider);
    final city = prefs.getString(_cityKey);
    if (city != null) return presetCityById(city);
    final (lat, lon, zone) = (prefs.getDouble(_gpsLatKey), prefs.getDouble(_gpsLonKey), prefs.getString(_gpsZoneKey));
    return lat == null || lon == null || zone == null ? null : GpsPlace(lat: lat, lon: lon, timezone: zone);
  }

  Future<void> choose(Place place) async {
    state = place;
    final prefs = ref.read(preferencesProvider);
    switch (place) {
      case PresetCity(:final id):
        await Future.wait([
          prefs.setString(_cityKey, id),
          for (final key in [_gpsLatKey, _gpsLonKey, _gpsZoneKey]) prefs.remove(key),
        ]);
      case GpsPlace(:final lat, :final lon, :final timezone):
        await Future.wait([
          prefs.remove(_cityKey),
          prefs.setDouble(_gpsLatKey, lat),
          prefs.setDouble(_gpsLonKey, lon),
          prefs.setString(_gpsZoneKey, timezone),
        ]);
    }
  }
}
