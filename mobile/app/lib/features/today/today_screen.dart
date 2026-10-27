import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/location_store.dart';

class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final city = ref.watch(locationProvider)!;
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 12,
        title: Semantics(
          hint: AppLocalizations.of(context).changeCity,
          child: ActionChip(
            avatar: const Icon(Icons.place_outlined),
            label: Text(city.nameFor(context)),
            onPressed: () => context.push('/location'),
          ),
        ),
      ),
    );
  }
}
