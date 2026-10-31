import 'package:flutter/material.dart';

import '../format/festival_text.dart';
import '../theme/navpad.dart';
import 'navpad_icons.dart';

/// Each festival kind's picture, so the shape says what the colour says.
NavpadGlyph festivalGlyph(FestivalKind kind) => switch (kind) {
  FestivalKind.mahaparva => NavpadGlyph.kalash,
  FestivalKind.kalyanak => NavpadGlyph.kalyanak,
  FestivalKind.parva => NavpadGlyph.dhvaja,
  FestivalKind.vrat => NavpadGlyph.diya,
};

/// A festival's mark: its picture in red, or green for a vrat. With [badge] it
/// sits in a 32 dp circle tinted with the same colour, as in lists. The words
/// go alongside, so the mark itself is silent.
class FestivalIcon extends StatelessWidget {
  const FestivalIcon({super.key, required this.kind, this.size = 24, this.strokeWidth = 1.8, this.badge = false});

  final FestivalKind kind;
  final double size, strokeWidth;
  final bool badge;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final colour = kind.isVrat ? n.green : n.red;
    final icon = NavpadIcon(festivalGlyph(kind), size: size, color: colour, strokeWidth: strokeWidth);
    if (!badge) return icon;
    return Container(
      width: 32,
      height: 32,
      alignment: Alignment.center,
      decoration: BoxDecoration(shape: BoxShape.circle, color: colour.withAlpha(0x14)),
      child: icon,
    );
  }
}
