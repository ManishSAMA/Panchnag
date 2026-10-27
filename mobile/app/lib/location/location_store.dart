import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'cities.dart';

/// Overridden in main with the loaded instance, so reads are synchronous.
final preferencesProvider = Provider<SharedPreferences>(
  (ref) => throw StateError('preferencesProvider must be overridden with the loaded SharedPreferences.'),
);

const _cityKey = 'location.city';

/// The chosen city, or null until the user picks one: the app never assumes a
/// location (PRODUCT.md principle 4).
final locationProvider = NotifierProvider<LocationNotifier, PresetCity?>(LocationNotifier.new);

final class LocationNotifier extends Notifier<PresetCity?> {
  @override
  PresetCity? build() {
    final saved = ref.read(preferencesProvider).getString(_cityKey);
    return saved == null ? null : presetCityById(saved);
  }

  Future<void> choose(PresetCity city) async {
    state = city;
    await ref.read(preferencesProvider).setString(_cityKey, city.id);
  }
}
