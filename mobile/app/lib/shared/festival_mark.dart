import 'package:flutter/material.dart';

import '../format/festival_text.dart';
import '../l10n/app_localizations.dart';
import '../theme/navpad.dart';

String festivalKindLabel(FestivalKind kind, AppLocalizations l10n) => switch (kind) {
  FestivalKind.mahaparva => l10n.festivalMahaparva,
  FestivalKind.kalyanak => l10n.festivalKalyanak,
  FestivalKind.parva => l10n.festivalParva,
  FestivalKind.vrat => l10n.festivalVrat,
};

/// DESIGN.md's marks: a red square for mahaparva, a red ring for kalyanak, a
/// red dot for parva and a green dot for vrat; 10 dp in lists, 7 dp in the grid.
/// The words go alongside, so the mark itself is silent.
class FestivalMark extends StatelessWidget {
  const FestivalMark({super.key, required this.kind, this.size = 10});

  final FestivalKind kind;
  final double size;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final colour = kind.isVrat ? n.green : n.red;
    final decoration = switch (kind) {
      FestivalKind.mahaparva => BoxDecoration(color: colour, borderRadius: BorderRadius.circular(size / 5)),
      FestivalKind.kalyanak => BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: colour, width: size / 4),
      ),
      FestivalKind.parva || FestivalKind.vrat => BoxDecoration(shape: BoxShape.circle, color: colour),
    };
    return ExcludeSemantics(
      child: SizedBox.square(
        dimension: size,
        child: DecoratedBox(decoration: decoration),
      ),
    );
  }
}

/// A day's festival line: its mark, its name and a sub-line, with an optional
/// right-hand value.
class FestivalRow extends StatelessWidget {
  const FestivalRow({super.key, required this.line, required this.subtitle, this.value, this.onTap});

  final FestivalLine line;
  final String subtitle;
  final String? value;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final row = Container(
      constraints: const BoxConstraints(minHeight: 52),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: n.hair)),
      ),
      child: Row(
        children: [
          FestivalMark(kind: line.kind),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(line.name, style: text.bodyLarge!.copyWith(color: n.ink)),
                Text(subtitle, style: text.labelMedium!.copyWith(color: n.ink2)),
              ],
            ),
          ),
          if (value != null) ...[
            const SizedBox(width: 12),
            // Capped rather than flexible, so it never takes half the row from the name.
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 150),
              child: Text(
                value!,
                textAlign: TextAlign.end,
                style: text.bodyLarge!.copyWith(color: n.ink, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ],
      ),
    );
    return onTap == null ? row : InkWell(onTap: onTap, child: row);
  }
}
