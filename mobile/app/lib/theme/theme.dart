import 'package:flutter/material.dart';

import 'navpad.dart';

/// The hand-built Material theme over the Navpad roles (DESIGN.md "Flutter
/// mapping"). No seed and no dynamic colour.
ThemeData navpadTheme(Brightness brightness) {
  final n = brightness == Brightness.light ? Navpad.light : Navpad.dark;
  final scheme = ColorScheme(
    brightness: brightness,
    primary: n.navy,
    onPrimary: n.onNavy,
    secondary: n.ink2,
    onSecondary: n.ground,
    secondaryContainer: n.pill,
    onSecondaryContainer: n.ink,
    // Nothing in the build uses the error role; denied and limit states are neutral notes.
    error: n.ink,
    onError: n.ground,
    surface: n.ground,
    onSurface: n.ink,
    onSurfaceVariant: n.ink2,
    outline: n.ink3,
    outlineVariant: n.hair,
    surfaceContainerLowest: n.ground,
    surfaceContainerLow: n.surface,
    surfaceContainer: n.surface,
    surfaceContainerHigh: n.surface,
    surfaceContainerHighest: n.surface2,
    surfaceTint: Colors.transparent,
  );
  const tabular = [FontFeature.tabularFigures()];
  final text = const TextTheme(
    headlineSmall: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, height: 1.25),
    titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, height: 1.3),
    titleMedium: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, height: 1.3),
    bodyLarge: TextStyle(fontSize: 17, fontWeight: FontWeight.w400, height: 1.35, fontFeatures: tabular),
    bodyMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, height: 1.45, fontFeatures: tabular),
    labelLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.3),
    labelMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, height: 1.3),
    labelSmall: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, height: 1.3),
  ).apply(fontFamily: 'Mukta', bodyColor: n.ink, displayColor: n.ink);

  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    textTheme: text,
    fontFamily: 'Mukta',
    scaffoldBackgroundColor: n.ground,
    materialTapTargetSize: MaterialTapTargetSize.padded,
    extensions: [n],
    dividerTheme: DividerThemeData(color: n.hair, thickness: 1, space: 1),
    appBarTheme: AppBarTheme(
      backgroundColor: n.ground,
      foregroundColor: n.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      toolbarHeight: 64,
      titleTextStyle: text.headlineSmall,
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 80,
      backgroundColor: n.surface,
      elevation: 0,
      indicatorColor: n.pill,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => text.labelSmall!.copyWith(color: states.contains(WidgetState.selected) ? n.ink : n.ink2),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(size: 24, color: states.contains(WidgetState.selected) ? n.ink : n.ink2),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: n.ground,
      selectedColor: n.pill,
      checkmarkColor: n.ink,
      labelStyle: text.labelLarge,
      side: BorderSide(color: n.ink3),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(20))),
      padding: const EdgeInsets.symmetric(horizontal: 8),
    ),
  );
}
