import 'package:flutter/widgets.dart';

import '../location/cities.dart';
import 'app_localizations.dart';

extension CityName on PresetCity {
  String nameFor(BuildContext context) => Localizations.localeOf(context).languageCode == 'en' ? nameEn : nameHi;
}

extension PlaceName on Place {
  /// A GPS fix has no name offline, so it borrows a close preset city's.
  String nameFor(BuildContext context) => switch (this) {
    final PresetCity city => city.nameFor(context),
    GpsPlace(near: final city?) => AppLocalizations.of(context).nearCity(city.nameFor(context)),
    GpsPlace() => AppLocalizations.of(context).myLocation,
  };

  /// '28.61° N, 77.21° E · Asia/Kolkata'; numerals stay Latin in Hindi too (mobile-ui-design.md §1).
  String get coordinatesLine {
    String part(double value, String positive, String negative) =>
        '${value.abs().toStringAsFixed(2)}° ${value < 0 ? negative : positive}';
    return '${part(lat, 'N', 'S')}, ${part(lon, 'E', 'W')} · $timezone';
  }
}
