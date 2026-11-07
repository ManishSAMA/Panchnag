import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:jainpanchang/features/choghadiya/choghadiya_band.dart';
import 'package:jainpanchang/shared/date_navigator.dart';
import 'package:jainpanchang/shared/navpad_widgets.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:jainpanchang/theme/pothi.dart';

import 'support/harness.dart';

// Phase 4 of plans/panchang-section-and-pothi.md: every screen but the Month
// grid is a Pothi leaf, its stitched margin running down the left edge.

Finder get _stitch => find.byKey(const Key('pothi-stitch'));

Future<void> _open(WidgetTester tester, String path) async {
  await openApp(tester, now: ist(2026, 11, 7));
  final router = GoRouter.of(tester.element(find.byType(Scaffold).first));
  if (const ['/today', '/month', '/pachchakkhan', '/festivals'].contains(path)) {
    router.go(path);
  } else {
    router.push(path);
  }
  // The festivals tab spins while its year arrives, so settle by pumping.
  for (var i = 0; i < 20; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

void main() {
  for (final path in [
    '/today',
    '/pachchakkhan',
    '/festivals',
    '/choghadiya',
    '/full-panchang',
    '/panchang-symbols',
    '/settings',
    '/location',
  ]) {
    testWidgets('$path has the stitched margin', (tester) async {
      await _open(tester, path);

      expect(_stitch, findsOneWidget);
    });
  }

  testWidgets('the stitch runs the full height of the page body', (tester) async {
    await _open(tester, '/today');

    final scaffold = tester.getRect(find.byType(Scaffold).first);
    final bar = tester.getRect(find.byType(AppBar).first);
    final stitch = tester.getRect(_stitch);

    expect(stitch.left, scaffold.left);
    expect(stitch.top, bar.bottom);
    expect(stitch.height, greaterThan(scaffold.height / 2));
  });

  testWidgets('content starts to the right of the stitch', (tester) async {
    await _open(tester, '/today');

    for (final content in [find.byType(DateNavigator), find.byType(ChoghadiyaBand)]) {
      expect(tester.getTopLeft(content).dx, greaterThanOrEqualTo(22));
    }
  });

  testWidgets('the Month grid keeps its full width, with no stitch', (tester) async {
    await _open(tester, '/month');

    expect(_stitch, findsNothing);
  });

  group('section headings are Pothi headings', () {
    for (final path in ['/today', '/pachchakkhan', '/choghadiya', '/settings']) {
      testWidgets('$path: red Tiro titles over a 2 dp red rule, with no hairline doubling it', (tester) async {
        await _open(tester, path);

        final headings = find.byType(SectionHeading);
        expect(headings, findsWidgets);
        final accent = Theme.of(tester.element(headings.first)).extension<Pothi>()!.accent;
        for (final heading in headings.evaluate().map((e) => e.widget as SectionHeading)) {
          final title = tester.widget<Text>(find.descendant(of: find.byWidget(heading), matching: find.text(heading.title)));
          expect(title.style!.color, accent, reason: heading.title);
          expect(title.style!.fontFamily, NavpadType.displayGroup.fontFamily, reason: heading.title);
          final rule = find.descendant(
            of: find.byWidget(heading),
            matching: find.byWidgetPredicate((w) => w is Container && w.color == accent),
          );
          expect(tester.widget<Container>(rule).constraints!.maxHeight, 2, reason: heading.title);
        }
        expect(find.byType(ListTop), findsNothing);
      });
    }

    testWidgets("a heading's link still opens its screen", (tester) async {
      await _open(tester, '/today');

      final link = find.descendant(of: find.byType(SectionHeading), matching: find.byType(TextButton));
      await tester.ensureVisible(link);
      await tester.tap(link);
      await tester.pumpAndSettle();

      expect(GoRouter.of(tester.element(find.byType(Scaffold).first)).state.matchedLocation, '/pachchakkhan');
    });
  });
}
