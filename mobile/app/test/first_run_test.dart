import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/app.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/features/festivals/festival_state.dart';
import 'package:jainpanchang/features/today/today_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'support/harness.dart';

Future<SharedPreferences> preferences([Map<String, Object> saved = const {}]) async {
  SharedPreferences.setMockInitialValues(saved);
  return SharedPreferences.getInstance();
}

Future<void> launch(WidgetTester tester, SharedPreferences prefs, {Locale phone = const Locale('hi', 'IN')}) async {
  tester.platformDispatcher.localesTestValue = [phone];
  addTearDown(tester.platformDispatcher.clearLocalesTestValue);
  final now = DateTime.utc(2026, 10, 22, 5, 22);
  await tester.pumpWidget(
    JainPanchangApp(
      preferences: prefs,
      overrides: [
        clockProvider.overrideWithValue(() => now),
        nowProvider.overrideWith((ref) => Stream.value(now)),
        dayReaderProvider.overrideWithValue((request) async => readDay(request)),
        festivalReaderProvider.overrideWithValue(realFestivals),
      ],
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  group('first run', () {
    testWidgets('asks for a city before anything else, with no default chosen', (tester) async {
      await launch(tester, await preferences());

      expect(find.text('अपना शहर चुनें'), findsOneWidget);
      expect(find.byType(ChoiceChip), findsNWidgets(11));
      expect(find.byType(NavigationBar), findsNothing);
      expect(tester.widgetList<ChoiceChip>(find.byType(ChoiceChip)).where((chip) => chip.selected), isEmpty);
    });

    testWidgets('choosing a city opens Today there and remembers it', (tester) async {
      final prefs = await preferences();
      await launch(tester, prefs);

      await tester.tap(find.text('दिल्ली'));
      await tester.pumpAndSettle();

      expect(find.byType(NavigationBar), findsOneWidget);
      expect(find.widgetWithText(TextButton, 'दिल्ली'), findsOneWidget);
      expect(prefs.getString('location.city'), 'delhi');
    });
  });

  testWidgets('a saved city opens straight on Today', (tester) async {
    await launch(tester, await preferences({'location.city': 'palitana'}));

    expect(find.widgetWithText(TextButton, 'पालीताणा'), findsOneWidget);
    expect(find.text('अपना शहर चुनें'), findsNothing);
  });

  testWidgets('a saved city the app no longer knows asks again', (tester) async {
    await launch(tester, await preferences({'location.city': 'atlantis'}));

    expect(find.text('अपना शहर चुनें'), findsOneWidget);
  });

  testWidgets('the tabs are Today, Month, Muhurat and Festivals, in that order', (tester) async {
    await launch(tester, await preferences({'location.city': 'delhi'}));

    final bar = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(bar.destinations, hasLength(4));
    expect(find.descendant(of: find.byType(NavigationBar), matching: find.text('आज')), findsOneWidget);

    for (final (index, label) in [(1, 'माह'), (2, 'मुहूर्त'), (3, 'पर्व')]) {
      await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text(label)));
      await tester.pumpAndSettle();
      expect(tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex, index, reason: label);
    }
  });

  testWidgets('an English phone sees English', (tester) async {
    await launch(tester, await preferences(), phone: const Locale('en', 'US'));

    expect(find.text('Choose your city'), findsOneWidget);
    expect(find.text('Delhi'), findsOneWidget);
  });
}
