import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:jainpanchang/theme/theme.dart';

// Token values are the specification: repo-root DESIGN.md, "colors" front matter
// and "Flutter mapping".
void main() {
  group('light theme', () {
    final theme = navpadTheme(Brightness.light);
    final scheme = theme.colorScheme;

    test('maps the Navpad roles onto the Material ColorScheme', () {
      expect(scheme.brightness, Brightness.light);
      expect(scheme.primary, const Color(0xFF1F2A44)); // navy
      expect(scheme.onPrimary, const Color(0xFFFFFFFF));
      expect(scheme.secondaryContainer, const Color(0xFFDDE2EE)); // pill
      expect(scheme.onSecondaryContainer, const Color(0xFF1F2A44)); // ink
      expect(scheme.surface, const Color(0xFFFFFFFF)); // ground
      expect(scheme.onSurface, const Color(0xFF1F2A44)); // ink
      expect(scheme.onSurfaceVariant, const Color(0xFF4A5570)); // ink2
      expect(scheme.outline, const Color(0xFF646D82)); // ink3
      expect(scheme.outlineVariant, const Color(0xFFE1E4EB)); // hair
      expect(scheme.surfaceContainer, const Color(0xFFF4F5F8)); // surface
      expect(scheme.surfaceContainerHighest, const Color(0xFFE9ECF2)); // surface2
    });

    test('carries the meaning colours in the Navpad extension only', () {
      final navpad = theme.extension<Navpad>()!;

      expect(navpad.red, const Color(0xFFB3261E));
      expect(navpad.yellow, const Color(0xFFE9B44C));
      expect(navpad.onYellow, const Color(0xFF1F2A44));
      expect(navpad.green, const Color(0xFF2E7D4F));
      expect(navpad.navy, scheme.primary);
      expect([scheme.secondary, scheme.tertiary], isNot(contains(navpad.red)));
    });

    test('scaffold is the white ground', () {
      expect(theme.scaffoldBackgroundColor, const Color(0xFFFFFFFF));
    });
  });

  group('dark theme', () {
    final theme = navpadTheme(Brightness.dark);
    final scheme = theme.colorScheme;

    test('maps the dark Navpad roles', () {
      expect(scheme.brightness, Brightness.dark);
      expect(scheme.primary, const Color(0xFF2A3A60));
      expect(scheme.surface, const Color(0xFF0E131E));
      expect(scheme.onSurface, const Color(0xFFECEEF3));
      expect(scheme.secondaryContainer, const Color(0xFF2E3A57));
      expect(scheme.surfaceContainer, const Color(0xFF161D2B));
      expect(scheme.outlineVariant, const Color(0xFF283044));
      expect(theme.extension<Navpad>()!.yellow, const Color(0xFFD4A03F));
    });
  });

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
