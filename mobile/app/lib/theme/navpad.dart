/// Navpad Colours: the Siddhachakra's five colours, each with exactly one job.
/// The values are the repo-root DESIGN.md front matter.
library;

import 'package:flutter/material.dart';

/// The Navpad roles. The meaning colours (red, yellow, green) live only here,
/// never in the ColorScheme, so no Material widget can pick one up by accident.
@immutable
final class Navpad extends ThemeExtension<Navpad> {
  const Navpad({
    required this.ground,
    required this.surface,
    required this.surface2,
    required this.hair,
    required this.ink,
    required this.ink2,
    required this.ink3,
    required this.navy,
    required this.onNavy,
    required this.onNavy2,
    required this.red,
    required this.onRed,
    required this.onRed2,
    required this.yellow,
    required this.onYellow,
    required this.onYellow2,
    required this.green,
    required this.onGreen,
    required this.onGreen2,
    required this.pill,
  });

  static const light = Navpad(
    ground: Color(0xFFFFFFFF),
    surface: Color(0xFFF4F5F8),
    surface2: Color(0xFFE9ECF2),
    hair: Color(0xFFE1E4EB),
    ink: Color(0xFF1F2A44),
    ink2: Color(0xFF4A5570),
    ink3: Color(0xFF646D82),
    navy: Color(0xFF1F2A44),
    onNavy: Color(0xFFFFFFFF),
    onNavy2: Color(0xFFC9D0E0),
    red: Color(0xFFB3261E),
    onRed: Color(0xFFFFFFFF),
    onRed2: Color(0xFFFBE2DF),
    yellow: Color(0xFFE9B44C),
    onYellow: Color(0xFF1F2A44),
    onYellow2: Color(0xFF4A3A12),
    green: Color(0xFF2E7D4F),
    onGreen: Color(0xFFFFFFFF),
    onGreen2: Color(0xFFDDF0E3),
    pill: Color(0xFFDDE2EE),
  );

  static const dark = Navpad(
    ground: Color(0xFF0E131E),
    surface: Color(0xFF161D2B),
    surface2: Color(0xFF1E2738),
    hair: Color(0xFF283044),
    ink: Color(0xFFECEEF3),
    ink2: Color(0xFFB0B7C8),
    ink3: Color(0xFF8F98AC),
    navy: Color(0xFF2A3A60),
    onNavy: Color(0xFFFFFFFF),
    onNavy2: Color(0xFFCBD3E6),
    red: Color(0xFFC0362C),
    onRed: Color(0xFFFFFFFF),
    onRed2: Color(0xFFFCE0DC),
    yellow: Color(0xFFD4A03F),
    onYellow: Color(0xFF1F2A44),
    onYellow2: Color(0xFF3A2C0A),
    green: Color(0xFF2B7A4C),
    onGreen: Color(0xFFFFFFFF),
    onGreen2: Color(0xFFD7EFDF),
    pill: Color(0xFF2E3A57),
  );

  final Color ground, surface, surface2, hair, ink, ink2, ink3;
  final Color navy, onNavy, onNavy2;
  final Color red, onRed, onRed2;
  final Color yellow, onYellow, onYellow2;
  final Color green, onGreen, onGreen2;
  final Color pill;

  // The theme switches whole schemes (light/dark), never a partial copy.
  @override
  Navpad copyWith() => this;

  @override
  Navpad lerp(Navpad? other, double t) => other == null || t < 0.5 ? this : other;
}

/// DESIGN.md typography roles that the Material text theme has no slot for.
/// Colour comes from the context.
abstract final class NavpadType {
  static const _tiro = 'TiroDevanagariHindi';
  static const _mukta = 'Mukta';
  static const _tabular = [FontFeature.tabularFigures()];

  static const displayHero = TextStyle(fontFamily: _tiro, fontSize: 44, fontWeight: FontWeight.w400, height: 1.12);
  static const displayBrand = TextStyle(fontFamily: _tiro, fontSize: 40, fontWeight: FontWeight.w400, height: 1.15);
  static const displayBand = TextStyle(fontFamily: _tiro, fontSize: 36, fontWeight: FontWeight.w400, height: 1.1);
  static const countdown =
      TextStyle(fontFamily: _mukta, fontSize: 30, fontWeight: FontWeight.w700, height: 1.1, fontFeatures: _tabular);
  static const titleBand = TextStyle(fontFamily: _mukta, fontSize: 18, fontWeight: FontWeight.w700, height: 1.3);
  static const labelAction = TextStyle(fontFamily: _mukta, fontSize: 16, fontWeight: FontWeight.w600, height: 1.3);
}
