import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/harness.dart';

/// The tabs and the Back key (plans/muhurat-tab-and-back.md, user 2026-11-19):
/// मुहूर्त is the third tab in place of पच्चक्खाण; Back goes back one screen,
/// to आज from another tab, and closes the app only on a second push on आज.

final bar = find.byType(NavigationBar);
Finder inBar(String label) => find.descendant(of: bar, matching: find.text(label));
final grid = find.byKey(const Key('muhurat-tile-rahu-kaal'));
final pachchakkhanTitle = find.descendant(of: find.byType(AppBar), matching: find.text('पच्चक्खाण'));
const exitHint = 'बाहर जाने के लिए फिर से वापस दबाएँ';

int selectedTab(WidgetTester tester) => tester.widget<NavigationBar>(bar).selectedIndex;

/// Records each time the app asks Android to close it.
List<String> watchExit(WidgetTester tester) {
  final calls = <String>[];
  tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
    calls.add(call.method);
    return null;
  });
  addTearDown(() => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, null));
  return calls;
}

int exits(List<String> calls) => calls.where((m) => m == 'SystemNavigator.pop').length;

Future<void> pressBack(WidgetTester tester) async {
  await tester.binding.handlePopRoute();
  await tester.pumpAndSettle();
}

Future<void> openToday(WidgetTester tester) => openApp(tester, now: ist(2026, 11, 7, 10, 0));

Future<void> tapTile(WidgetTester tester, String key) async {
  final tile = find.byKey(Key(key));
  await tester.ensureVisible(tile);
  await tester.tap(tile);
  await tester.pumpAndSettle();
}

void main() {
  group('the tab bar', () {
    testWidgets('is आज, माह, मुहूर्त, पर्व', (tester) async {
      await openToday(tester);

      final labels = [
        for (final d in tester.widget<NavigationBar>(bar).destinations) (d as NavigationDestination).label,
      ];
      expect(labels, ['आज', 'माह', 'मुहूर्त', 'पर्व']);
      expect(inBar('पच्चक्खाण'), findsNothing);
    });

    testWidgets('मुहूर्त opens the Muhurat grid with the bar still below it', (tester) async {
      await openToday(tester);
      await openTab(tester, 'मुहूर्त');

      expect(grid, findsOneWidget);
      expect(selectedTab(tester), 2);
    });

    testWidgets("Today's मुहूर्त tile opens the मुहूर्त tab", (tester) async {
      await openToday(tester);
      await tapTile(tester, 'tile-muhurat');

      expect(grid, findsOneWidget);
      expect(selectedTab(tester), 2);
    });

    testWidgets("Today's पच्चक्खाण tile opens Pachchakkhan over Today, and Back returns", (tester) async {
      await openToday(tester);
      await tapTile(tester, 'tile-pachchakkhan');
      expect(pachchakkhanTitle, findsOneWidget);

      await pressBack(tester);
      expect(pachchakkhanTitle, findsNothing);
      expect(find.byKey(const Key('today-panchang-card')), findsOneWidget);
    });

    testWidgets("the yellow band opens Pachchakkhan over Today, and Back returns", (tester) async {
      await openToday(tester);
      final band = find.byKey(const Key('today-band-pachchakkhan'));
      await tester.ensureVisible(band);
      await tester.tap(band);
      await tester.pumpAndSettle();
      expect(pachchakkhanTitle, findsOneWidget);

      await pressBack(tester);
      expect(find.byKey(const Key('today-panchang-card')), findsOneWidget);
    });
  });

  group('Back', () {
    testWidgets('on a Muhurat detail goes back to the grid', (tester) async {
      final calls = watchExit(tester);
      await openToday(tester);
      await openTab(tester, 'मुहूर्त');
      await tester.tap(grid);
      await tester.pumpAndSettle();
      expect(grid, findsNothing);

      await pressBack(tester);
      expect(grid, findsOneWidget);
      expect(exits(calls), 0);
    });

    testWidgets('on a Muhurat detail opened from Full Panchang goes back to Full Panchang', (tester) async {
      final calls = watchExit(tester);
      await openToday(tester);
      final pill = find.byKey(const Key('today-full-panchang'));
      await tester.ensureVisible(pill);
      await tester.tap(pill);
      await tester.pumpAndSettle();
      final tile = find.byKey(const Key('muhurat-tile-abhijit'));
      await tester.scrollUntilVisible(tile, 300, scrollable: find.byType(Scrollable).first);
      await tester.tap(tile);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('full-panchang-screen')), findsNothing);

      await pressBack(tester);
      expect(find.byKey(const Key('full-panchang-screen')), findsOneWidget);
      expect(exits(calls), 0);
    });

    for (final tab in ['माह', 'मुहूर्त', 'पर्व']) {
      testWidgets('on the $tab tab goes to आज, not out of the app', (tester) async {
        final calls = watchExit(tester);
        await openToday(tester);
        await openTab(tester, tab);

        await pressBack(tester);
        expect(selectedTab(tester), 0);
        expect(exits(calls), 0);
      });
    }

    testWidgets('once on आज keeps the app open and says to push again', (tester) async {
      final calls = watchExit(tester);
      await openToday(tester);

      await pressBack(tester);
      expect(find.text(exitHint), findsOneWidget);
      expect(exits(calls), 0);
    });

    testWidgets('twice on आज closes the app', (tester) async {
      final calls = watchExit(tester);
      await openToday(tester);

      await tester.binding.handlePopRoute();
      await tester.pump(const Duration(milliseconds: 500));
      await pressBack(tester);
      expect(exits(calls), 1);
    });

    testWidgets('a second push after 2 s asks again, and does not close', (tester) async {
      final calls = watchExit(tester);
      await openToday(tester);

      await pressBack(tester);
      await tester.pump(const Duration(seconds: 3));
      await pressBack(tester);
      expect(exits(calls), 0);
      expect(find.text(exitHint), findsOneWidget);
    });

    testWidgets('says it in English on an English phone', (tester) async {
      watchExit(tester);
      await openApp(tester, now: ist(2026, 11, 7, 10, 0), phone: const Locale('en', 'US'));

      await pressBack(tester);
      expect(find.text('Press back again to exit'), findsOneWidget);
    });
  });
}
