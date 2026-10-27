/// The quick-pick cities (mobile-app-flutter.md §1). They are the parity
/// fixtures' core locations, so the engine is verified at every one.
library;

final class PresetCity {
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
  final double lat;
  final double lon;
  final String timezone;
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
