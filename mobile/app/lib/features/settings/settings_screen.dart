import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../../shared/navpad_widgets.dart';
import '../../theme/navpad.dart';
import '../location/gps_action.dart';

/// Settings (mobile-ui-design.md §3 · Settings). Each choice applies at once
/// to the open tabs. The theme joins with dark mode (Phase 6), reminders and
/// crash reports in Phase 7.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final place = ref.watch(locationProvider)!;
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.settings)),
      body: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          SectionHeading(title: l10n.settingsLocation),
          ListTile(
            leading: const Icon(Icons.place_outlined),
            title: Text(place.nameFor(context)),
            subtitle: Text(place.coordinatesLine),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 4, 18, 0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const GpsAction(),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => context.push('/location'),
                  style: OutlinedButton.styleFrom(minimumSize: const Size(48, 48)),
                  icon: const Icon(Icons.location_city),
                  label: Text(l10n.chooseCity),
                ),
              ],
            ),
          ),
          SectionHeading(title: l10n.settingsTradition),
          _Choices(
            provider: traditionProvider,
            options: [
              (Tradition.tapagachchha, l10n.tapagachchha, null),
              (Tradition.sthanakvasi, l10n.sthanakvasi, null),
              (Tradition.terapanthi, l10n.terapanthi, null),
            ],
          ),
          _Help(l10n.traditionHelp),
          SectionHeading(title: l10n.settingsLanguage),
          _Choices(
            provider: languageProvider,
            // Each language is named in its own script, so either reader finds theirs.
            options: [
              (LanguageChoice.phone, l10n.languagePhone, null),
              (LanguageChoice.hi, 'हिन्दी', null),
              (LanguageChoice.en, 'English', null),
            ],
          ),
          SectionHeading(title: l10n.settingsMonthSystem),
          _Choices(
            provider: monthSystemProvider,
            options: [
              (MonthSystem.purnimanta, l10n.purnimanta, l10n.purnimantaHelp),
              (MonthSystem.amanta, l10n.amanta, l10n.amantaHelp),
            ],
          ),
          SectionHeading(title: l10n.settingsSunrise),
          _Choices(
            provider: sunriseRuleProvider,
            options: [
              (SunriseRule.modern, l10n.sunriseModern, l10n.sunriseModernHelp),
              (SunriseRule.traditional, l10n.sunriseTraditional, l10n.sunriseTraditionalHelp),
            ],
          ),
          _Help(l10n.sunriseHelp),
          SectionHeading(title: l10n.settingsAbout),
          for (final line in [l10n.aboutOffline, l10n.aboutRange, l10n.aboutFontSize])
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 4, 18, 4),
              child: Text(line, style: text.bodyLarge!.copyWith(color: n.ink2)),
            ),
        ],
      ),
    );
  }
}

/// A setting's options as radios: (value, label, optional subtitle).
class _Choices<T extends Enum> extends ConsumerWidget {
  const _Choices({required this.provider, required this.options});

  final NotifierProvider<EnumSetting<T>, T> provider;
  final List<(T, String, String?)> options;

  @override
  Widget build(BuildContext context, WidgetRef ref) => RadioGroup<T>(
    groupValue: ref.watch(provider),
    onChanged: (value) {
      if (value != null) ref.read(provider.notifier).choose(value);
    },
    child: Column(
      children: [
        for (final (value, label, subtitle) in options)
          RadioListTile<T>(value: value, title: Text(label), subtitle: subtitle == null ? null : Text(subtitle)),
      ],
    ),
  );
}

class _Help extends StatelessWidget {
  const _Help(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(18, 2, 18, 0),
    child: Text(
      text,
      style: Theme.of(context).textTheme.bodyMedium!.copyWith(color: Theme.of(context).extension<Navpad>()!.ink2),
    ),
  );
}
