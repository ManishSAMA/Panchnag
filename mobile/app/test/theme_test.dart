import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:jainpanchang/theme/theme.dart';

// Token values are the specification: repo-root DESIGN.md, "colors" front matter
// and "Flutter mapping". Since Phase 4 (plans/panchang-section-and-pothi.md) the
// whole app wears the Pothi palette: parchment by day, navy by night.

/// WCAG 2 contrast ratio.
double contrast(Color a, Color b) {
  double channel(double c) => c <= 0.03928 ? c / 12.92 : math.pow((c + 0.055) / 1.055, 2.4).toDouble();
  double luminance(Color c) => 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
  final [high, low] = [luminance(a), luminance(b)]..sort((x, y) => y.compareTo(x));
  return (high + 0.05) / (low + 0.05);
}

void main() {
  group('light theme', () {
    final theme = navpadTheme(Brightness.light);
    final scheme = theme.colorScheme;

    test('maps the Pothi parchment roles onto the Material ColorScheme', () {
      expect(scheme.brightness, Brightness.light);
      expect(scheme.primary, const Color(0xFF243B64)); // navy
      expect(scheme.onPrimary, const Color(0xFFF1E5C8));
      expect(scheme.secondaryContainer, const Color(0xFFDFCC9F)); // pill
      expect(scheme.onSecondaryContainer, const Color(0xFF243B64)); // ink
      expect(scheme.surface, const Color(0xFFF1E5C8)); // ground: parchment
      expect(scheme.onSurface, const Color(0xFF243B64)); // ink
      expect(scheme.onSurfaceVariant, const Color(0xFF514A3C)); // ink2
      expect(scheme.outline, const Color(0xFF5C5444)); // ink3
      expect(scheme.outlineVariant, const Color(0xFFC9B98F)); // hair: the Pothi rule
      expect(scheme.surfaceContainer, const Color(0xFFE8D8B0)); // surface: deeper parchment
      expect(scheme.surfaceContainerHighest, const Color(0xFFDFCC9F)); // surface2
    });

    test('carries the softened meaning colours in the Navpad extension only', () {
      final navpad = theme.extension<Navpad>()!;

      expect(navpad.red, const Color(0xFFA33B2B));
      expect(navpad.yellow, const Color(0xFFD8AE5A));
      expect(navpad.onYellow, const Color(0xFF243B64));
      expect(navpad.green, const Color(0xFF3F6841));
      expect(navpad.navy, scheme.primary);
      expect([scheme.secondary, scheme.tertiary], isNot(contains(navpad.red)));
    });

    test('scaffold is the parchment ground', () {
      expect(theme.scaffoldBackgroundColor, const Color(0xFFF1E5C8));
    });
  });

  group('dark theme', () {
    final theme = navpadTheme(Brightness.dark);
    final scheme = theme.colorScheme;

    test('maps the Pothi navy roles', () {
      expect(scheme.brightness, Brightness.dark);
      expect(scheme.primary, const Color(0xFF2A3A60));
      expect(scheme.surface, const Color(0xFF171C29));
      expect(scheme.onSurface, const Color(0xFFF2E8D5));
      expect(scheme.secondaryContainer, const Color(0xFF2E3650));
      expect(scheme.surfaceContainer, const Color(0xFF1F2636));
      expect(scheme.outlineVariant, const Color(0xFF665B49));
      expect(theme.extension<Navpad>()!.yellow, const Color(0xFFC29845));
    });
  });

  for (final brightness in Brightness.values) {
    group('$brightness', () {
      final n = navpadTheme(brightness).extension<Navpad>()!;

      test('every text colour reads at 4.5:1 on the fills it sits on', () {
        final pairs = [
          for (final text in [n.ink, n.ink2, n.ink3])
            for (final fill in [n.ground, n.surface, n.surface2, n.pill]) (text, fill),
          // ✓ and ✕ marks are text on the page, the tiles and the list rows.
          for (final mark in [n.markGood, n.markAvoid])
            for (final fill in [n.ground, n.surface, n.surface2]) (mark, fill),
          // The light-green row of a window running now.
          for (final text in [n.ink, n.ink2, n.ink3, n.markGood, n.markAvoid]) (text, n.nowFill),
          (n.onNavy, n.navy),
          (n.onNavy2, n.navy),
          (n.onRed, n.red),
          (n.onRed2, n.red),
          (n.onYellow, n.yellow),
          (n.onYellow2, n.yellow),
          (n.onGreen, n.green),
          (n.onGreen2, n.green),
        ];
        for (final (text, fill) in pairs) {
          expect(contrast(text, fill), greaterThanOrEqualTo(4.5), reason: '$text on $fill');
        }
      });

      test('red and green marks stand out at 3:1 on the ground', () {
        expect(contrast(n.red, n.ground), greaterThanOrEqualTo(3));
        expect(contrast(n.green, n.ground), greaterThanOrEqualTo(3));
      });

      test('controls drawn straight on the page stand out from it', () {
        final theme = navpadTheme(brightness);
        const selected = {WidgetState.selected};

        // Navy is a fill colour (filled button, bands); on the dark ground it
        // would vanish, so controls without a fill of their own use ink.
        expect(contrast(theme.outlinedButtonTheme.style!.foregroundColor!.resolve({})!, n.ground), greaterThanOrEqualTo(4.5));
        expect(contrast(theme.textButtonTheme.style!.foregroundColor!.resolve({})!, n.ground), greaterThanOrEqualTo(4.5));
        expect(contrast(theme.radioTheme.fillColor!.resolve(selected)!, n.ground), greaterThanOrEqualTo(3));
        expect(contrast(theme.progressIndicatorTheme.color!, n.ground), greaterThanOrEqualTo(3));
      });

      test('the top and bottom bars stand on the same ground as the page', () {
        final theme = navpadTheme(brightness);

        expect(theme.appBarTheme.backgroundColor, n.ground);
        expect(theme.navigationBarTheme.backgroundColor, n.ground);
      });
    });
  }

  test('UI type is Mukta and display type is Tiro Devanagari Hindi', () {
    final theme = navpadTheme(Brightness.light);

    expect(theme.textTheme.bodyLarge!.fontFamily, 'Mukta');
    expect(theme.textTheme.bodyLarge!.fontSize, 17);
    expect(theme.textTheme.bodyMedium!.fontSize, 16);
    expect(NavpadType.displayHero.fontFamily, 'TiroDevanagariHindi');
    expect(NavpadType.displayHero.fontSize, 44);
  });

  test('every interactive control is at least 48 dp', () {
    expect(navpadTheme(Brightness.light).materialTapTargetSize, MaterialTapTargetSize.padded);
  });
}
