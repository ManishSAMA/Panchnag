import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../shared/navpad_icons.dart';
import '../../theme/navpad.dart';

/// Today's feature tiles under the hero, so a new reader sees what the app can
/// do. Flat `surface` tiles with 12 dp corners: DESIGN.md's one
/// exception to "no cards". The festivals tile waits until a `/festivals`
/// route exists, so it never opens onto nothing.
class FeatureTiles extends StatelessWidget {
  const FeatureTiles({super.key, required this.onMonth});

  /// Month opens on the date Today shows, which only Today knows.
  final VoidCallback onMonth;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final router = GoRouter.of(context);
    final hasFestivals = router.configuration
        .findMatch(Uri.parse('/festivals'))
        .isNotEmpty;
    final tiles = [
      _Tile(
        key: const Key('tile-choghadiya'),
        glyph: NavpadGlyph.ghatika,
        label: l10n.choghadiyaTitle,
        onTap: () => context.push('/choghadiya'),
      ),
      _Tile(
        key: const Key('tile-pachchakkhan'),
        glyph: NavpadGlyph.sunpath,
        label: l10n.tabPachchakkhan,
        onTap: () => context.go('/pachchakkhan'),
      ),
      if (hasFestivals)
        _Tile(
          key: const Key('tile-festivals'),
          glyph: NavpadGlyph.kalash,
          label: l10n.tileFestivals,
          onTap: () => context.go('/festivals'),
        ),
      _Tile(
        key: const Key('tile-month'),
        glyph: NavpadGlyph.monthcal,
        label: l10n.tabMonth,
        onTap: onMonth,
      ),
    ];
    // Three columns at ordinary text and two at enlarged text keep every label readable;
    // four tiles sit two by two, so none is left alone on a row.
    // Android scales text non-linearly, so measure at the label's own 14 sp.
    final scale = MediaQuery.textScalerOf(context).scale(14) / 14;
    final perRow = scale >= 1.3 || tiles.length == 4 ? 2 : 3;
    final rows = [
      for (var i = 0; i < tiles.length; i += perRow)
        tiles.sublist(i, (i + perRow).clamp(0, tiles.length)),
    ];
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 2, 12, 16),
      child: Column(
        spacing: 8,
        children: [
          for (final row in rows)
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 8,
                children: [
                  for (final tile in row) Expanded(child: tile),
                  // A short last row keeps the tiles above it in their columns.
                  for (var i = row.length; i < perRow; i++)
                    const Expanded(child: SizedBox()),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  const _Tile({
    super.key,
    required this.glyph,
    required this.label,
    required this.onTap,
  });

  final NavpadGlyph glyph;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    return Semantics(
      button: true,
      label: label,
      excludeSemantics: true,
      child: Material(
        color: n.surface,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: n.hair)),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 76),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 6),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                spacing: 5,
                children: [
                  NavpadIcon(glyph, size: 28, color: n.ink),
                  Text(
                    label,
                    textAlign: TextAlign.center,
                    style: text.labelLarge!.copyWith(
                      color: n.ink,
                      fontSize: 14,
                      height: 1.15,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
