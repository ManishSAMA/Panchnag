import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../l10n/app_localizations.dart';

/// The gear in each tab's top bar (mobile-ui-design.md §1).
class SettingsButton extends StatelessWidget {
  const SettingsButton({super.key});

  @override
  Widget build(BuildContext context) => IconButton(
    icon: const Icon(Icons.settings_outlined),
    tooltip: AppLocalizations.of(context).settings,
    onPressed: () => context.push('/settings'),
  );
}
