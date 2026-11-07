import 'package:flutter/material.dart';

import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../shared/panchang_symbols.dart';
import '../../theme/pothi.dart';

class SymbolGuideScreen extends StatelessWidget {
  const SymbolGuideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final groups = [
      (PanchangSymbolGroup.planets, l10n.symbolPlanets),
      (PanchangSymbolGroup.zodiac, l10n.symbolZodiac),
      (PanchangSymbolGroup.aspects, l10n.symbolAspects),
      (PanchangSymbolGroup.moonPhases, l10n.symbolMoonPhases),
      (PanchangSymbolGroup.eclipses, l10n.symbolEclipses),
    ];
    return Scaffold(
      key: const Key('symbol-guide'),
      backgroundColor: p.ground,
      appBar: AppBar(
        backgroundColor: p.ground,
        foregroundColor: p.ink,
        title: Text(l10n.symbolGuide),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              l10n.symbolsReferenceOnly,
              style: Theme.of(context).textTheme.bodyMedium!
                  .copyWith(color: p.secondary),
            ),
            for (final (group, title) in groups) ...[
              Padding(
                padding: const EdgeInsets.only(top: 26, bottom: 7),
                child: Semantics(
                  header: true,
                  child: Text(
                    title,
                    style: TextStyle(
                      fontFamily: 'TiroDevanagariHindi',
                      fontSize: 24,
                      color: p.accent,
                    ),
                  ),
                ),
              ),
              Container(height: 2, color: p.accent),
              LayoutBuilder(
                builder: (context, constraints) {
                  final scale = MediaQuery.textScalerOf(context).scale(16) / 16;
                  final columns = constraints.maxWidth >= 500 && scale < 1.3
                      ? 2
                      : 1;
                  final width = constraints.maxWidth / columns;
                  return Wrap(
                    children: [
                      for (final glyph in PanchangGlyph.values.where(
                        (g) => panchangSymbolGroup(g) == group,
                      ))
                        SizedBox(
                          width: width,
                          child: _SymbolRow(glyph: glyph, lang: lang),
                        ),
                    ],
                  );
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SymbolRow extends StatelessWidget {
  const _SymbolRow({required this.glyph, required this.lang});

  final PanchangGlyph glyph;
  final Lang lang;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final name = panchangSymbolName(glyph, lang);
    final degrees = panchangAspectDegrees(glyph);
    return Semantics(
      container: true,
      label: name,
      excludeSemantics: true,
      child: Container(
        constraints: const BoxConstraints(minHeight: 66),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 9),
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: p.rule)),
        ),
        child: Row(
          children: [
            PanchangSymbol(glyph, color: p.ink),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: Theme.of(context).textTheme.bodyLarge!
                        .copyWith(color: p.ink),
                  ),
                  if (lang == Lang.hi)
                    Text(
                      panchangSymbolName(glyph, Lang.en),
                      style: Theme.of(context).textTheme.labelMedium!
                          .copyWith(color: p.secondary),
                    ),
                ],
              ),
            ),
            if (degrees != null)
              Text(
                degrees,
                style: Theme.of(context).textTheme.labelLarge!
                    .copyWith(color: p.accent),
              ),
          ],
        ),
      ),
    );
  }
}
