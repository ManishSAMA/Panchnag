import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/shared/date_navigator.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

final calendar = find.byTooltip('तारीख चुनें');
final dialog = find.byType(DatePickerDialog);

/// Opens [path] on 7 Nov 2026: a tab with go, any other screen with push.
Future<void> openAt(WidgetTester tester, String path, {Locale phone = const Locale('hi', 'IN')}) async {
  await openApp(tester, now: ist(2026, 11, 7, 10, 0), phone: phone);
  final router = GoRouter.of(tester.element(find.byType(Scaffold).first));
  if (const ['/today', '/month', '/pachchakkhan', '/festivals'].contains(path)) {
    router.go(path);
  } else {
    router.push(path);
  }
  for (var i = 0; i < 20; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// Picks [day] of the month the picker shows, then confirms.
Future<void> pickDay(WidgetTester tester, int day) async {
  await tester.tap(find.descendant(of: dialog, matching: find.text('$day')).first);
  await tester.pumpAndSettle();
  final ok = MaterialLocalizations.of(tester.element(dialog)).okButtonLabel;
  await tester.tap(find.descendant(of: dialog, matching: find.text(ok)));
  await tester.pumpAndSettle();
}

String shownDate(WidgetTester tester) =>
    longDate(tester.widget<DateNavigator>(find.byType(DateNavigator)).date, Lang.hi);

void main() {
  group('the calendar button', () {
    for (final path in ['/today', '/pachchakkhan', '/choghadiya', '/muhurat', '/muhurat/rahu-kaal', '/full-panchang']) {
      testWidgets('is in the top bar of $path', (tester) async {
        await openAt(tester, path);

        expect(find.descendant(of: find.byType(AppBar), matching: calendar), findsOneWidget);
      });
    }

    for (final path in ['/month', '/festivals']) {
      testWidgets('is not on $path, which has no date row', (tester) async {
        await openAt(tester, path);

        expect(calendar, findsNothing);
      });
    }

    testWidgets('opens the phone calendar on the date shown, within the years the app covers', (tester) async {
      await openAt(tester, '/today');
      await tester.tap(calendar);
      await tester.pumpAndSettle();

      final picker = tester.widget<DatePickerDialog>(dialog);
      expect(picker.initialDate, DateTime(2026, 11, 7));
      expect(picker.firstDate, DateTime(2016, 1, 1));
      expect(picker.lastDate, DateTime(2040, 12, 31));
      expect(picker.currentDate, DateTime(2026, 11, 7));
    });

    testWidgets('a picked date shows on this screen and on every other one', (tester) async {
      await openAt(tester, '/today');
      await tester.tap(calendar);
      await tester.pumpAndSettle();
      await pickDay(tester, 23);

      expect(shownDate(tester), longDate(const CivilDate(2026, 11, 23), Lang.hi));

      GoRouter.of(tester.element(find.byType(Scaffold).first)).go('/pachchakkhan');
      await tester.pumpAndSettle();
      expect(shownDate(tester), longDate(const CivilDate(2026, 11, 23), Lang.hi));
    });

    testWidgets('a picked date moves a Muhurat screen too', (tester) async {
      await openAt(tester, '/muhurat');
      await tester.tap(calendar);
      await tester.pumpAndSettle();
      await pickDay(tester, 2);

      expect(shownDate(tester), longDate(const CivilDate(2026, 11, 2), Lang.hi));
    });

    testWidgets('cancel keeps the date', (tester) async {
      await openAt(tester, '/today');
      await tester.tap(calendar);
      await tester.pumpAndSettle();
      final cancel = MaterialLocalizations.of(tester.element(dialog)).cancelButtonLabel;
      await tester.tap(find.descendant(of: dialog, matching: find.text(cancel)));
      await tester.pumpAndSettle();

      expect(shownDate(tester), longDate(const CivilDate(2026, 11, 7), Lang.hi));
    });

    testWidgets('is named in English on an English phone', (tester) async {
      await openAt(tester, '/today', phone: const Locale('en', 'US'));

      expect(find.byTooltip('Pick a date'), findsOneWidget);
    });
  });

  testWidgets('a push on the date in the date row also opens the calendar', (tester) async {
    await openAt(tester, '/today');
    final date = find.descendant(
      of: find.byType(DateNavigator),
      matching: find.text(longDate(const CivilDate(2026, 11, 7), Lang.hi)),
    );
    await tester.ensureVisible(date);
    await tester.tap(date);
    await tester.pumpAndSettle();

    expect(dialog, findsOneWidget);
  });
}
