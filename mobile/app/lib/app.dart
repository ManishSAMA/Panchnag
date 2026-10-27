import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'l10n/app_localizations.dart';
import 'location/location_store.dart';
import 'router.dart';
import 'theme/theme.dart';

/// English if the phone's first language is English, otherwise Hindi
/// (mobile-ui-design.md §1).
Locale appLocaleFor(List<Locale>? phoneLocales) =>
    phoneLocales != null && phoneLocales.isNotEmpty && phoneLocales.first.languageCode == 'en'
        ? const Locale('en')
        : const Locale('hi');

class JainPanchangApp extends StatelessWidget {
  const JainPanchangApp({super.key, required this.preferences});

  final SharedPreferences preferences;

  @override
  Widget build(BuildContext context) => ProviderScope(
    overrides: [preferencesProvider.overrideWithValue(preferences)],
    child: const _App(),
  );
}

class _App extends ConsumerStatefulWidget {
  const _App();

  @override
  ConsumerState<_App> createState() => _AppState();
}

class _AppState extends ConsumerState<_App> {
  late final GoRouter _router = buildRouter(hasLocation: ref.read(locationProvider) != null);

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    onGenerateTitle: (context) => AppLocalizations.of(context).appTitle,
    theme: navpadTheme(Brightness.light),
    darkTheme: navpadTheme(Brightness.dark),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    localeListResolutionCallback: (phoneLocales, _) => appLocaleFor(phoneLocales),
    routerConfig: _router,
  );
}
