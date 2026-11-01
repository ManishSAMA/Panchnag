import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'features/choghadiya/choghadiya_screen.dart';
import 'features/festivals/festivals_screen.dart';
import 'features/location/city_picker_screen.dart';
import 'features/month/month_screen.dart';
import 'features/pachchakkhan/pachchakkhan_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/today/today_screen.dart';
import 'l10n/app_localizations.dart';
import 'shared/navpad_icons.dart';

/// Tabs appear as their screens are built (mobile-ui-design.md §1), never as
/// an empty placeholder.
GoRouter buildRouter({required bool hasLocation}) => GoRouter(
  initialLocation: hasLocation ? '/today' : '/location',
  routes: [
    GoRoute(path: '/location', builder: (context, state) => const CityPickerScreen()),
    GoRoute(path: '/choghadiya', pageBuilder: choghadiyaPage),
    GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
    StatefulShellRoute.indexedStack(
      builder: (context, state, shell) => _TabShell(shell: shell),
      branches: [
        StatefulShellBranch(
          routes: [GoRoute(path: '/today', builder: (context, state) => const TodayScreen())],
        ),
        StatefulShellBranch(
          routes: [GoRoute(path: '/month', builder: (context, state) => const MonthScreen())],
        ),
        StatefulShellBranch(
          routes: [GoRoute(path: '/pachchakkhan', builder: (context, state) => const PachchakkhanScreen())],
        ),
        StatefulShellBranch(
          routes: [GoRoute(path: '/festivals', builder: (context, state) => const FestivalsScreen())],
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
            NavigationDestination(icon: const NavpadIcon(NavpadGlyph.sunrise), label: l10n.tabToday),
            NavigationDestination(icon: const NavpadIcon(NavpadGlyph.monthcal), label: l10n.tabMonth),
            NavigationDestination(icon: const NavpadIcon(NavpadGlyph.sunpath), label: l10n.tabPachchakkhan),
            NavigationDestination(icon: const NavpadIcon(NavpadGlyph.kalash), label: l10n.tabFestivals),
          ],
        ),
      ),
    );
  }
}
