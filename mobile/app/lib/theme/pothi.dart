import 'package:flutter/material.dart';

@immutable
final class Pothi extends ThemeExtension<Pothi> {
  const Pothi({
    required this.ground,
    required this.ink,
    required this.secondary,
    required this.accent,
    required this.rule,
  });

  static const light = Pothi(
    ground: Color(0xFFF1E5C8),
    ink: Color(0xFF243B64),
    secondary: Color(0xFF514A3C),
    accent: Color(0xFFA33B2B),
    rule: Color(0xFFC9B98F),
  );

  static const dark = Pothi(
    ground: Color(0xFF171C29),
    ink: Color(0xFFF2E8D5),
    secondary: Color(0xFFC9BFA9),
    accent: Color(0xFFE8957F),
    rule: Color(0xFF665B49),
  );

  final Color ground, ink, secondary, accent, rule;

  @override
  Pothi copyWith() => this;

  @override
  Pothi lerp(Pothi? other, double t) => other == null || t < 0.5 ? this : other;
}
