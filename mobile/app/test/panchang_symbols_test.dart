import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/shared/panchang_symbols.dart';

import 'full_panchang_screen_test.dart';

Future<void> openSymbols(
  WidgetTester tester, {
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
}) async {
  await openFullPanchang(tester, phone: phone, textScale: textScale);
  await tester.tap(
    find.byTooltip(
      phone.languageCode == 'en' ? 'Symbol guide' : 'प्रतीक मार्गदर्शिका',
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'the guide contains every requested symbol group and all 38 labelled symbols',
    (tester) async {
      await openSymbols(tester, phone: const Locale('en', 'US'));

      expect(find.byKey(const Key('symbol-guide')), findsOneWidget);
      expect(find.byType(PanchangSymbol), findsNWidgets(38));
      for (final heading in [
        'Planets',
        'Zodiac signs',
        'Aspects',
        'Moon phases',
        'Eclipses',
      ]) {
        expect(find.text(heading), findsOneWidget);
      }
      expect(find.textContaining('Reference only'), findsOneWidget);
    },
  );

  testWidgets(
    'planet and zodiac names are readable without knowing the glyphs',
    (tester) async {
      await openSymbols(tester, phone: const Locale('en', 'US'));

      for (final name in [
        'Sun',
        'Moon',
        'Mercury',
        'Venus',
        'Mars',
        'Jupiter',
        'Saturn',
        'Uranus',
        'Neptune',
        'Pluto',
        "Moon’s Node",
        'Aries',
        'Taurus',
        'Gemini',
        'Cancer',
        'Leo',
        'Virgo',
        'Libra',
        'Scorpio',
        'Sagittarius',
        'Capricorn',
        'Aquarius',
        'Pisces',
      ]) {
        expect(find.text(name), findsOneWidget, reason: name);
        expect(find.bySemanticsLabel(name), findsOneWidget, reason: name);
      }
    },
  );

  testWidgets(
    'aspects include their angular distance and the phase and eclipse symbols are named',
    (tester) async {
      await openSymbols(tester, phone: const Locale('en', 'US'));

      for (final (name, degree) in [
        ('Conjunction', '0°'),
        ('Semisextile', '30°'),
        ('Semisquare', '45°'),
        ('Sextile', '60°'),
        ('Square', '90°'),
        ('Trine', '120°'),
        ('Sesquisquare', '135°'),
        ('Quincunx', '150°'),
        ('Opposition', '180°'),
      ]) {
        expect(find.text(name), findsOneWidget, reason: name);
        expect(find.text(degree), findsOneWidget, reason: degree);
      }
      for (final name in [
        'New Moon',
        'First Quarter Moon',
        'Full Moon',
        'Third Quarter Moon',
        'Solar Eclipse',
        'Lunar Eclipse',
      ]) {
        expect(find.text(name), findsOneWidget);
      }
    },
  );

  testWidgets(
    'Hindi readers receive Hindi names and the same reference-only explanation',
    (tester) async {
      await openSymbols(tester);

      expect(find.text('प्रतीक मार्गदर्शिका'), findsWidgets);
      for (final name in [
        'सूर्य',
        'चंद्रमा',
        'बुध',
        'मेष',
        'मीन',
        'अमावस्या',
        'सूर्य ग्रहण',
        'चंद्र ग्रहण',
      ]) {
        expect(find.text(name), findsOneWidget, reason: name);
      }
      expect(find.textContaining('केवल संदर्भ'), findsOneWidget);
    },
  );

  for (final scale in [1.3, 1.6, 2.0]) {
    testWidgets('symbol names and groups do not overflow at ${scale}x text', (
      tester,
    ) async {
      await openSymbols(
        tester,
        phone: const Locale('en', 'US'),
        textScale: scale,
      );
      expect(tester.takeException(), isNull);
      expect(find.byType(PanchangSymbol), findsNWidgets(38));
    });
  }

  testWidgets('the guide follows light and dark themes with contrasting ink', (
    tester,
  ) async {
    final grounds = <Color>[];
    for (final brightness in [Brightness.light, Brightness.dark]) {
      tester.platformDispatcher.platformBrightnessTestValue = brightness;
      await openSymbols(tester);
      final context = tester.element(find.byKey(const Key('symbol-guide')));
      final scaffold = tester.widget<Scaffold>(
        find.byKey(const Key('symbol-guide')),
      );
      expect(Theme.of(context).brightness, brightness);
      grounds.add(scaffold.backgroundColor!);
      for (final symbol in tester.widgetList<PanchangSymbol>(
        find.byType(PanchangSymbol),
      )) {
        expect(symbol.color, isNotNull);
        expect(symbol.color, isNot(scaffold.backgroundColor));
      }
    }
    expect(grounds.first, isNot(grounds.last));
  });
}
