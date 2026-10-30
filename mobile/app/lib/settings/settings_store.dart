/// The Settings choices (mobile-ui-design.md §3 · Settings), each persisted
/// and read synchronously at start, so the first frame already uses them.
library;

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../location/location_store.dart';

/// The three Shwetambar profiles, saved by the registry's string ID so more
/// traditions can join later; the festival port reads [id].
enum Tradition {
  tapagachchha('shwetambar_murtipujak_tapagachchha'),
  sthanakvasi('shwetambar_sthanakvasi'),
  terapanthi('shwetambar_terapanthi');

  const Tradition(this.id);

  final String id;
}

/// [phone] follows the phone's language (`appLocaleFor`).
enum LanguageChoice {
  phone(null),
  hi(Locale('hi')),
  en(Locale('en'));

  const LanguageChoice(this.locale);

  final Locale? locale;
}

/// Whether a Krishna paksha belongs to the month ending at the full moon
/// after it (Purnimanta) or at the new moon (Amanta).
enum MonthSystem { purnimanta, amanta }

LunarMonth lunarMonthOf(PanchangDay day, MonthSystem system) => switch (system) {
  MonthSystem.purnimanta => day.month,
  MonthSystem.amanta => day.amantaMonth,
};

final traditionProvider = NotifierProvider<EnumSetting<Tradition>, Tradition>(
  () => EnumSetting('settings.tradition', Tradition.values, Tradition.tapagachchha, id: (t) => t.id),
);

final languageProvider = NotifierProvider<EnumSetting<LanguageChoice>, LanguageChoice>(
  () => EnumSetting('settings.language', LanguageChoice.values, LanguageChoice.phone),
);

final monthSystemProvider = NotifierProvider<EnumSetting<MonthSystem>, MonthSystem>(
  () => EnumSetting('settings.monthSystem', MonthSystem.values, MonthSystem.purnimanta),
);

/// Modern is the default (mobile-ui-design.md §3 · Settings).
final sunriseRuleProvider = NotifierProvider<EnumSetting<SunriseRule>, SunriseRule>(
  () => EnumSetting('settings.sunriseRule', SunriseRule.values, SunriseRule.modern),
);

/// One saved choice from a fixed set. An unknown saved value, say from a
/// newer app version, falls back to the default.
final class EnumSetting<T extends Enum> extends Notifier<T> {
  EnumSetting(this._key, this._values, this._fallback, {String Function(T)? id}) : _id = id ?? ((v) => v.name);

  final String _key;
  final List<T> _values;
  final T _fallback;
  final String Function(T) _id;

  @override
  T build() {
    final saved = ref.read(preferencesProvider).getString(_key);
    return _values.where((v) => _id(v) == saved).firstOrNull ?? _fallback;
  }

  Future<void> choose(T value) async {
    state = value;
    await ref.read(preferencesProvider).setString(_key, _id(value));
  }
}
