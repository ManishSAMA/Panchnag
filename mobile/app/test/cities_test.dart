import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/location/cities.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

// The preset cities are the core of the parity tests (mobile-app-flutter.md §1),
// so every one must be a location the Dart engine is verified at.
List<Map<String, Object?>> parityLocations() {
  final manifest = jsonDecode(
    File('../packages/panchang_engine/test/fixtures/core/manifest.json').readAsStringSync(),
  ) as Map<String, Object?>;
  return (manifest['locations']! as List<Object?>).cast<Map<String, Object?>>();
}

void main() {
  test('are the 11 cities of the plan, in its order', () {
    expect(presetCities.map((c) => c.nameEn), [
      'Delhi', 'Ahmedabad', 'Mumbai', 'Surat', 'Palitana', 'Jaipur', //
      'Udaipur', 'Indore', 'Kolkata', 'Bengaluru', 'Chennai',
    ]);
  });

  test('each sits exactly on a parity-verified location', () {
    final verified = {for (final l in parityLocations()) l['slug']: l};

    for (final city in presetCities) {
      final location = verified[city.id];
      expect(location, isNotNull, reason: city.id);
      expect((city.lat, city.lon, city.timezone), (location!['lat'], location['lon'], location['timezone']));
    }
  });

  test('ids are unique and look up their own city', () {
    expect(presetCities.map((c) => c.id).toSet(), hasLength(presetCities.length));
    for (final city in presetCities) {
      expect(presetCityById(city.id), same(city));
    }
    expect(presetCityById('atlantis'), isNull);
  });

  test('each has a Hindi name and a known time zone', () {
    tzdata.initializeTimeZones();
    for (final city in presetCities) {
      expect(city.nameHi, matches(RegExp(r'^[ऀ-ॿ ]+$')), reason: city.id);
      expect(() => tz.getLocation(city.timezone), returnsNormally);
    }
  });

  group('the preset city near a GPS fix', () {
    test('is each city at its own coordinates', () {
      for (final city in presetCities) {
        expect(nearestCity(lat: city.lat, lon: city.lon), same(city), reason: city.id);
      }
    });

    test('is the closest of two nearby cities', () {
      // Surat (21.17, 72.83) and Palitana (21.52, 71.82): a point just east of Surat.
      expect(nearestCity(lat: 21.17, lon: 72.95)?.id, 'surat');
    });

    test('holds within $nearCityKm km and not beyond', () {
      // One degree of latitude is about 111 km.
      final delhi = presetCityById('delhi')!;
      expect(nearestCity(lat: delhi.lat + 0.4, lon: delhi.lon)?.id, 'delhi');
      expect(nearestCity(lat: delhi.lat + 0.5, lon: delhi.lon), isNull);
    });

    test('is none for a fix outside India', () {
      expect(nearestCity(lat: 51.5074, lon: -0.1278), isNull);
    });
  });
}
