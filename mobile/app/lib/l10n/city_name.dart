import 'package:flutter/widgets.dart';

import '../location/cities.dart';

extension CityName on PresetCity {
  String nameFor(BuildContext context) =>
      Localizations.localeOf(context).languageCode == 'en' ? nameEn : nameHi;
}
