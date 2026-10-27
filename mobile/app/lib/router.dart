import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'features/location/city_picker_screen.dart';
import 'features/pachchakkhan/pachchakkhan_screen.dart';
import 'features/today/today_screen.dart';
import 'l10n/app_localizations.dart';

/// Tabs appear as their screens are built: Month and Festivals join later
/// (mobile-ui-design.md §1), never as empty placeholders.
GoRouter buildRouter({required bool hasLocation}) => GoRouter(
  initialLocation: hasLocation ? '/today' : '/location',
  routes: [
    GoRoute(path: '/location', builder: (context, state) => const CityPickerScreen()),
    StatefulShellRoute.indexedStack(
      builder: (context, state, shell) => _TabShell(shell: shell),
      branches: [
        StatefulShellBranch(
          routes: [GoRoute(path: '/today', builder: (context, state) => const TodayScreen())],
        ),
        StatefulShellBranch(
          routes: [GoRoute(path: '/pachchakkhan', builder: (context, state) => const PachchakkhanScreen())],
        ),
      ],
    ),
  ],
);

class _TabShell extends StatelessWidget {
  const _TabShell({required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: shell,
      bottomNavigationBar: DecoratedBox(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: Theme.of(context).dividerTheme.color!)),
        ),
        child: NavigationBar(
          selectedIndex: shell.currentIndex,
          onDestinationSelected: (index) => shell.goBranch(index, initialLocation: index == shell.currentIndex),
          destinations: [
            NavigationDestination(
              icon: const Icon(Icons.wb_sunny_outlined),
              selectedIcon: const Icon(Icons.wb_sunny),
              label: l10n.tabToday,
            ),
            NavigationDestination(
              icon: const Icon(Icons.schedule_outlined),
              selectedIcon: const Icon(Icons.schedule),
              label: l10n.tabPachchakkhan,
            ),
          ],
        ),
      ),
    );
  }
}
