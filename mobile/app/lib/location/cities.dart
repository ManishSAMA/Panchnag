/// The quick-pick cities (mobile-app-flutter.md §1). They are the parity
/// fixtures' core locations, so the engine is verified at every one.
library;

import 'dart:math' as math;

/// Where the panchang is calculated: a preset city or a GPS fix.
sealed class Place {
  const Place();

  double get lat;
  double get lon;

  /// An IANA name, such as 'Asia/Kolkata'.
  String get timezone;
}

final class PresetCity extends Place {
  const PresetCity({
    required this.id,
    required this.nameHi,
    required this.nameEn,
    required this.lat,
    required this.lon,
    required this.timezone,
  });

  /// The parity fixture slug, also the saved setting.
  final String id;
  final String nameHi;
  final String nameEn;
  @override
  final double lat;
  @override
  final double lon;
  @override
  final String timezone;
}

/// A GPS fix, in the time zone the phone was set to when it was taken
/// (mobile-ui-design.md §3.0). A fix outside India is accepted.
final class GpsPlace extends Place {
  const GpsPlace({required this.lat, required this.lon, required this.timezone});

  @override
  final double lat;
  @override
  final double lon;
  @override
  final String timezone;

  /// The preset city it is named after, if one is close enough; offline there is no other name for it.
  PresetCity? get near => nearestCity(lat: lat, lon: lon);
}

const List<PresetCity> presetCities = [
  PresetCity(id: 'delhi', nameHi: 'दिल्ली', nameEn: 'Delhi', lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
  PresetCity(
    id: 'ahmedabad',
    nameHi: 'अहमदाबाद',
    nameEn: 'Ahmedabad',
    lat: 23.0225,
    lon: 72.5714,
    timezone: 'Asia/Kolkata',
  ),
  PresetCity(id: 'mumbai', nameHi: 'मुंबई', nameEn: 'Mumbai', lat: 19.0760, lon: 72.8777, timezone: 'Asia/Kolkata'),
  PresetCity(id: 'surat', nameHi: 'सूरत', nameEn: 'Surat', lat: 21.1702, lon: 72.8311, timezone: 'Asia/Kolkata'),
  PresetCity(
    id: 'palitana',
    nameHi: 'पालीताणा',
    nameEn: 'Palitana',
    lat: 21.5222,
    lon: 71.8237,
    timezone: 'Asia/Kolkata',
  ),
  PresetCity(id: 'jaipur', nameHi: 'जयपुर', nameEn: 'Jaipur', lat: 26.9124, lon: 75.7873, timezone: 'Asia/Kolkata'),
  PresetCity(id: 'udaipur', nameHi: 'उदयपुर', nameEn: 'Udaipur', lat: 24.5854, lon: 73.7125, timezone: 'Asia/Kolkata'),
  PresetCity(id: 'indore', nameHi: 'इंदौर', nameEn: 'Indore', lat: 22.7196, lon: 75.8577, timezone: 'Asia/Kolkata'),
  PresetCity(id: 'kolkata', nameHi: 'कोलकाता', nameEn: 'Kolkata', lat: 22.5726, lon: 88.3639, timezone: 'Asia/Kolkata'),
  PresetCity(
    id: 'bengaluru',
    nameHi: 'बेंगलुरु',
    nameEn: 'Bengaluru',
    lat: 12.9716,
    lon: 77.5946,
    timezone: 'Asia/Kolkata',
  ),
  PresetCity(id: 'chennai', nameHi: 'चेन्नई', nameEn: 'Chennai', lat: 13.0827, lon: 80.2707, timezone: 'Asia/Kolkata'),
];

PresetCity? presetCityById(String id) {
  for (final city in presetCities) {
    if (city.id == id) return city;
  }
  return null;
}

/// How far a GPS fix may be from a preset city and still be called "near" it.
const int nearCityKm = 50;

/// The closest preset city within [nearCityKm] of a point, if any.
PresetCity? nearestCity({required double lat, required double lon}) {
  final (distance, city) = presetCities
      .map((c) => (_kmBetween(lat, lon, c.lat, c.lon), c))
      .reduce((a, b) => a.$1 <= b.$1 ? a : b);
  return distance <= nearCityKm ? city : null;
}

/// Great-circle distance on a spherical Earth (haversine).
double _kmBetween(double lat1, double lon1, double lat2, double lon2) {
  double rad(double degrees) => degrees * math.pi / 180;
  final dLat = rad(lat2 - lat1);
  final dLon = rad(lon2 - lon1);
  final h = math.pow(math.sin(dLat / 2), 2) + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.pow(math.sin(dLon / 2), 2);
  return 2 * 6371.0 * math.asin(math.sqrt(h));
}
