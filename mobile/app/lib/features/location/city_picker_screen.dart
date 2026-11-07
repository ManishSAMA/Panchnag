import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/cities.dart';
import '../../location/location_store.dart';
import '../../shared/pothi_page.dart';
import 'gps_action.dart';

/// The onboarding location step: the preset cities as chips. Opened on first
/// run, and from Settings. A GPS fix is the other way to set the location.
class CityPickerScreen extends ConsumerWidget {
  const CityPickerScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final text = Theme.of(context).textTheme;
    final current = ref.watch(locationProvider);

    // From Settings the picker returns there; on first run it opens Today.
    void done() => context.canPop() ? context.pop() : context.go('/today');

    Future<void> choose(PresetCity city) async {
      await ref.read(locationProvider.notifier).choose(city);
      if (context.mounted) done();
    }

    return Scaffold(
      appBar: AppBar(automaticallyImplyLeading: context.canPop()),
      body: PothiPage(child: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 24),
          children: [
            Text(l10n.chooseCityTitle, style: text.headlineSmall),
            const SizedBox(height: 8),
            Text(
              l10n.chooseCityOffline,
              style: text.bodyMedium!.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 24),
            GpsAction(onLocated: () => context.mounted ? done() : null),
            const SizedBox(height: 24),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final city in presetCities)
                  ChoiceChip(
                    label: Text(city.nameFor(context)),
                    selected: city == current,
                    onSelected: (_) => choose(city),
                  ),
              ],
            ),
          ],
        ),
      )),
    );
  }
}
