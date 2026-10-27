import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/cities.dart';
import '../../location/location_store.dart';

/// The onboarding location step: the preset cities as chips. Opened on first
/// run, and from Today's location chip. GPS joins in a later build.
class CityPickerScreen extends ConsumerWidget {
  const CityPickerScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final text = Theme.of(context).textTheme;
    final current = ref.watch(locationProvider);

    Future<void> choose(PresetCity city) async {
      await ref.read(locationProvider.notifier).choose(city);
      if (context.mounted) context.go('/today');
    }

    return Scaffold(
      appBar: AppBar(automaticallyImplyLeading: context.canPop()),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 24),
          children: [
            Text(l10n.chooseCityTitle, style: text.headlineSmall),
            const SizedBox(height: 8),
            Text(l10n.chooseCityOffline, style: text.bodyMedium!.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
            const SizedBox(height: 24),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final city in presetCities)
                  ChoiceChip(
                    label: Text(city.nameFor(context)),
                    selected: city.id == current?.id,
                    onSelected: (_) => choose(city),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
