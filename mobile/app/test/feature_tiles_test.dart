import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:jainpanchang/features/today/feature_tiles.dart';
import 'package:jainpanchang/l10n/app_localizations.dart';
import 'package:jainpanchang/shared/navpad_icons.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:jainpanchang/theme/theme.dart';

import 'support/harness.dart';

Finder tile(String name) => find.byKey(Key('tile-$name'));

NavpadGlyph glyphIn(WidgetTester tester, Finder finder) => tester
    .widget<NavpadIcon>(
      find.descendant(of: finder, matching: find.byType(NavpadIcon)),
    )
    .glyph;

/// The tiles under a router that has, or lacks, a `/festivals` route.
Future<void> pumpTiles(
  WidgetTester tester, {
  required bool withFestivals,
}) async {
  final router = GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) =>
            Scaffold(body: FeatureTiles(onMonth: () {})),
      ),
      if (withFestivals)
        GoRoute(
          path: '/festivals',
          builder: (context, state) => const Text('festivals screen'),
        ),
    ],
  );
  addTearDown(router.dispose);
  await tester.pumpWidget(
    MaterialApp.router(
      theme: navpadTheme(Brightness.light),
      locale: const Locale('hi'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      routerConfig: router,
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'sit under the hero, above the bands, each a flat surface tile with a picture over its name',
    (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));
      final tiles = find.byType(FeatureTiles);

      expect(
        tester.getTopLeft(tiles).dy,
        greaterThan(
          tester.getBottomLeft(find.byKey(const Key('today-hero-tithi'))).dy,
        ),
      );
      expect(
        tester.getBottomLeft(tiles).dy,
        lessThanOrEqualTo(
          tester
              .getTopLeft(find.byKey(const Key('today-band-pachchakkhan')))
              .dy,
        ),
      );
      final expected = {
        'choghadiya': (NavpadGlyph.ghatika, 'चौघड़िया'),
        'pachchakkhan': (NavpadGlyph.sunpath, 'पच्चक्खाण'),
        'month': (NavpadGlyph.monthcal, 'माह'),
      };
      for (final MapEntry(key: name, value: (glyph, label))
          in expected.entries) {
        expect(glyphIn(tester, tile(name)), glyph, reason: name);
        expect(
          find.descendant(of: tile(name), matching: find.text(label)),
          findsOneWidget,
        );
        expect(tester.getSize(tile(name)).height, greaterThanOrEqualTo(76));
        final icon = find.descendant(
          of: tile(name),
          matching: find.byType(NavpadIcon),
        );
        expect(tester.getSize(icon), const Size.square(28));
        final text = find.descendant(
          of: tile(name),
          matching: find.text(label),
        );
        expect(
          tester.getTopLeft(icon).dy,
          lessThan(tester.getTopLeft(text).dy),
        );
        final box = find
            .descendant(of: tile(name), matching: find.byType(Material))
            .first;
        final material = tester.widget<Material>(box);
        final n = Theme.of(tester.element(box)).extension<Navpad>()!;
        expect(material.color, n.surface);
        expect(material.elevation, 0);
        expect(
          material.shape,
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        );
      }
    },
  );

  testWidgets('each tile is a button named for a screen reader', (
    tester,
  ) async {
    await openApp(tester, now: ist(2026, 10, 22));

    for (final label in ['चौघड़िया', 'पच्चक्खाण', 'माह']) {
      final node = tester.getSemantics(
        find.descendant(
          of: find.byType(FeatureTiles),
          matching: find.bySemanticsLabel(label),
        ),
      );
      expect(node.flagsCollection.isButton, isTrue, reason: label);
    }
  });

  testWidgets('चौघड़िया opens the Choghadiya screen', (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));

    await tester.tap(tile('choghadiya'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('choghadiya-hero')), findsOneWidget);
  });

  testWidgets('पच्चक्खाण opens the Pachchakkhan tab', (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));

    await tester.tap(tile('pachchakkhan'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('pachchakkhan-hero')), findsOneWidget);
  });

  testWidgets('माह opens the Month tab on the date shown', (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));
    await tester.tap(nav('अगला दिन'));
    await tester.pumpAndSettle();

    await tester.tap(tile('month'));
    await tester.pumpAndSettle();

    expect(find.text('अक्टूबर 2026'), findsOneWidget);
    expect(
      find.descendant(
        of: find.byKey(const Key('month-day-panel')),
        matching: find.text('शुक्रवार, 23 अक्टूबर 2026'),
      ),
      findsOneWidget,
    );
  });

  testWidgets('are in English on an English phone', (tester) async {
    await openApp(
      tester,
      now: ist(2026, 10, 22),
      phone: const Locale('en', 'US'),
    );

    for (final label in ['Choghadiya', 'Pachchakkhan', 'Month']) {
      expect(
        find.descendant(
          of: find.byType(FeatureTiles),
          matching: find.text(label),
        ),
        findsOneWidget,
      );
    }
  });

  group('पर्व सूची', () {
    testWidgets('is hidden while the app has no festivals screen', (
      tester,
    ) async {
      await pumpTiles(tester, withFestivals: false);

      expect(tile('festivals'), findsNothing);
      expect(tile('month'), findsOneWidget);
    });

    testWidgets(
      'shows the kalash and opens the festivals screen once it exists',
      (tester) async {
        await pumpTiles(tester, withFestivals: true);

        expect(glyphIn(tester, tile('festivals')), NavpadGlyph.kalash);
        expect(
          find.descendant(
            of: tile('festivals'),
            matching: find.text('पर्व सूची'),
          ),
          findsOneWidget,
        );
        final tileKeys = tester
            .widgetList<Widget>(
              find.byWidgetPredicate(
                (widget) =>
                    widget.key is ValueKey<String> &&
                    (widget.key! as ValueKey<String>).value.startsWith('tile-'),
              ),
            )
            .map((widget) => (widget.key! as ValueKey<String>).value)
            .toList();
        expect(
          tileKeys.indexOf('tile-festivals'),
          greaterThan(tileKeys.indexOf('tile-pachchakkhan')),
        );
        expect(
          tileKeys.indexOf('tile-festivals'),
          lessThan(tileKeys.indexOf('tile-month')),
        );

        await tester.tap(tile('festivals'));
        await tester.pumpAndSettle();
        expect(find.text('festivals screen'), findsOneWidget);
      },
    );
  });

  for (final scale in [1.3, 1.6]) {
    testWidgets('at ${scale}x text every label fits, unclipped', (
      tester,
    ) async {
      await openApp(tester, now: ist(2026, 10, 22), textScale: scale);

      expect(tester.takeException(), isNull);
      for (final name in ['choghadiya', 'pachchakkhan', 'month']) {
        final label = find.descendant(
          of: tile(name),
          matching: find.byType(Text),
        );
        expect(
          tester
              .getRect(tile(name))
              .contains(tester.getRect(label).bottomRight - const Offset(1, 1)),
          isTrue,
        );
      }
    });
  }
}
