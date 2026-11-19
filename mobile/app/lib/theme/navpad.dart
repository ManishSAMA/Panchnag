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
    required this.markGood,
    required this.markAvoid,
    required this.nowFill,
  });

  static const light = Navpad(
    ground: Color(0xFFF1E5C8),
    surface: Color(0xFFE8D8B0),
    surface2: Color(0xFFDFCC9F),
    hair: Color(0xFFC9B98F),
    ink: Color(0xFF243B64),
    ink2: Color(0xFF514A3C),
    ink3: Color(0xFF5C5444),
    navy: Color(0xFF243B64),
    onNavy: Color(0xFFF1E5C8),
    onNavy2: Color(0xFFC9D0E0),
    red: Color(0xFFA33B2B),
    onRed: Color(0xFFFFF6E8),
    onRed2: Color(0xFFF3D6CC),
    yellow: Color(0xFFD8AE5A),
    onYellow: Color(0xFF243B64),
    onYellow2: Color(0xFF4A3A12),
    green: Color(0xFF3F6841),
    onGreen: Color(0xFFFFF6E8),
    onGreen2: Color(0xFFDCE9D6),
    pill: Color(0xFFDFCC9F),
    markGood: Color(0xFF2F5A33),
    markAvoid: Color(0xFF962F22),
    nowFill: Color(0xFFD6E6CC),
  );

  static const dark = Navpad(
    ground: Color(0xFF171C29),
    surface: Color(0xFF1F2636),
    surface2: Color(0xFF283044),
    hair: Color(0xFF665B49),
    ink: Color(0xFFF2E8D5),
    ink2: Color(0xFFC9BFA9),
    ink3: Color(0xFFADA48F),
    navy: Color(0xFF2A3A60),
    onNavy: Color(0xFFF2E8D5),
    onNavy2: Color(0xFFCBD3E6),
    red: Color(0xFFAD4639),
    onRed: Color(0xFFFFF4EF),
    onRed2: Color(0xFFF7E4DD),
    yellow: Color(0xFFC29845),
    onYellow: Color(0xFF171C29),
    onYellow2: Color(0xFF3A2C0A),
    green: Color(0xFF47784F),
    onGreen: Color(0xFFF6FBF4),
    onGreen2: Color(0xFFEAF2E6),
    pill: Color(0xFF2E3650),
    markGood: Color(0xFF8CC796),
    markAvoid: Color(0xFFEE8B78),
    nowFill: Color(0xFF24392B),
  );

  final Color ground, surface, surface2, hair, ink, ink2, ink3;
  final Color navy, onNavy, onNavy2;
  final Color red, onRed, onRed2;
  final Color yellow, onYellow, onYellow2;
  final Color green, onGreen, onGreen2;
  final Color pill;

  /// ✓ and ✕ as text on the page: green and red, deep by day and light by
  /// night, so each reads at 4.5:1 where the fills [green] and [red] do not.
  final Color markGood, markAvoid;

  /// A light green behind the row or tile of a window running now, edged in
  /// [markGood]. The word "अभी" goes with it, so it never rests on colour.
  final Color nowFill;

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
  static const countdown = TextStyle(
    fontFamily: _mukta,
    fontSize: 30,
    fontWeight: FontWeight.w700,
    height: 1.1,
    fontFeatures: _tabular,
  );
  static const displayMonth = TextStyle(fontFamily: _tiro, fontSize: 26, fontWeight: FontWeight.w400, height: 1.2);
  static const displayHeading = TextStyle(fontFamily: _tiro, fontSize: 24, fontWeight: FontWeight.w400, height: 1.2);
  static const displayGroup = TextStyle(fontFamily: _tiro, fontSize: 22, fontWeight: FontWeight.w400, height: 1.2);
  static const cellDay = TextStyle(
    fontFamily: _mukta,
    fontSize: 19,
    fontWeight: FontWeight.w600,
    height: 1.1,
    fontFeatures: _tabular,
  );
  static const cellTithi = TextStyle(fontFamily: _mukta, fontSize: 12, fontWeight: FontWeight.w400, height: 1.2);
  static const cellFlag = TextStyle(fontFamily: _mukta, fontSize: 11, fontWeight: FontWeight.w700, height: 1.1);
  static const titleBand = TextStyle(fontFamily: _mukta, fontSize: 18, fontWeight: FontWeight.w700, height: 1.3);
  static const labelAction = TextStyle(fontFamily: _mukta, fontSize: 16, fontWeight: FontWeight.w600, height: 1.3);
}
