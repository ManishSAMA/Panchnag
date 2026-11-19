import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import 'features/choghadiya/choghadiya_screen.dart';
import 'features/festivals/festivals_screen.dart';
import 'features/full_panchang/full_panchang_screen.dart';
import 'features/full_panchang/symbol_guide_screen.dart';
import 'features/location/city_picker_screen.dart';
import 'features/month/month_screen.dart';
import 'features/muhurat/muhurat_grid.dart';
import 'features/muhurat/muhurat_screen.dart';
import 'features/pachchakkhan/pachchakkhan_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/today/today_screen.dart';
import 'l10n/app_localizations.dart';
import 'shared/navpad_icons.dart';

/// Tabs appear as their screens are built (mobile-ui-design.md §1), never as
/// an empty placeholder.
GoRouter buildRouter({required bool hasLocation}) {
  final root = GlobalKey<NavigatorState>();
  return GoRouter(
    navigatorKey: root,
    initialLocation: hasLocation ? '/today' : '/location',
    routes: [
      GoRoute(
        path: '/location',
        builder: (context, state) => const CityPickerScreen(),
      ),
      GoRoute(path: '/choghadiya', pageBuilder: choghadiyaPage),
      // Pushed over the tabs, so Back returns to the screen it opened from.
      GoRoute(
        path: '/pachchakkhan',
        builder: (context, state) => const PachchakkhanScreen(),
      ),
      GoRoute(
        path: '/full-panchang',
        builder: (context, state) => const FullPanchangScreen(),
      ),
      GoRoute(
        path: '/panchang-symbols',
        builder: (context, state) => const SymbolGuideScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => _TabShell(shell: shell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/today',
                builder: (context, state) => const TodayScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/month',
                builder: (context, state) => const MonthScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/muhurat',
                builder: (context, state) => const MuhuratScreen(),
                routes: [
                  GoRoute(
                    path: ':kind',
                    // Over the tabs, as Choghadiya is, so Back returns to where it
                    // opened from: the grid, or Full Panchang's मुहूर्त group.
                    parentNavigatorKey: root,
                    redirect: (context, state) =>
                        MuhuratKind.fromSlug(state.pathParameters['kind']!) ==
                            null
                        ? '/muhurat'
                        : null,
                    builder: (context, state) => MuhuratDetailScreen(
                      kind: MuhuratKind.fromSlug(
                        state.pathParameters['kind']!,
                      )!,
                    ),
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/festivals',
                builder: (context, state) => const FestivalsScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
}

/// Back on a tab with nothing left to pop: another tab goes to आज; on आज the
/// first push asks for a second within 2 s, which closes the app (user
/// 2026-11-19: Back must never leave the app by surprise).
class _TabShell extends StatefulWidget {
  const _TabShell({required this.shell});

  final StatefulNavigationShell shell;

  @override
  State<_TabShell> createState() => _TabShellState();
}

class _TabShellState extends State<_TabShell> {
  static const _exitWindow = Duration(seconds: 2);

  Timer? _exitArmed;

  @override
  void dispose() {
    _exitArmed?.cancel();
    super.dispose();
  }

  void _onBack() {
    if (widget.shell.currentIndex != 0) {
      widget.shell.goBranch(0);
      return;
    }
    if (_exitArmed?.isActive ?? false) {
      SystemNavigator.pop();
      return;
    }
    _exitArmed = Timer(_exitWindow, () {});
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context).pressBackAgainToExit),
          duration: _exitWindow,
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final shell = widget.shell;
    final l10n = AppLocalizations.of(context);
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _onBack();
      },
      child: Scaffold(
        body: shell,
        bottomNavigationBar: DecoratedBox(
          decoration: BoxDecoration(
            border: Border(
              top: BorderSide(color: Theme.of(context).dividerTheme.color!),
            ),
          ),
          child: NavigationBar(
            selectedIndex: shell.currentIndex,
            onDestinationSelected: (index) => shell.goBranch(
              index,
              initialLocation: index == shell.currentIndex,
            ),
            destinations: [
              NavigationDestination(
                icon: const NavpadIcon(NavpadGlyph.sunrise),
                label: l10n.tabToday,
              ),
              NavigationDestination(
                icon: const NavpadIcon(NavpadGlyph.monthcal),
                label: l10n.tabMonth,
              ),
              NavigationDestination(
                icon: const NavpadIcon(NavpadGlyph.abhijit),
                label: l10n.muhuratTitle,
              ),
              NavigationDestination(
                icon: const NavpadIcon(NavpadGlyph.kalash),
                label: l10n.tabFestivals,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
