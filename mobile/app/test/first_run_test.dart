import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/app.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<SharedPreferences> preferences([Map<String, Object> saved = const {}]) async {
  SharedPreferences.setMockInitialValues(saved);
  return SharedPreferences.getInstance();
}

Future<void> launch(WidgetTester tester, SharedPreferences prefs, {Locale phone = const Locale('hi', 'IN')}) async {
  tester.platformDispatcher.localesTestValue = [phone];
  addTearDown(tester.platformDispatcher.clearLocalesTestValue);
  await tester.pumpWidget(JainPanchangApp(preferences: prefs));
  await tester.pumpAndSettle();
}

void main() {
  group('first run', () {
    testWidgets('asks for a city before anything else, with no default chosen', (tester) async {
      await launch(tester, await preferences());

      expect(find.text('अपना शहर चुनें'), findsOneWidget);
      expect(find.byType(ChoiceChip), findsNWidgets(11));
      expect(find.byType(NavigationBar), findsNothing);
      expect(
        tester.widgetList<ChoiceChip>(find.byType(ChoiceChip)).where((chip) => chip.selected),
        isEmpty,
      );
    });

    testWidgets('choosing a city opens Today there and remembers it', (tester) async {
      final prefs = await preferences();
      await launch(tester, prefs);

      await tester.tap(find.text('दिल्ली'));
      await tester.pumpAndSettle();

      expect(find.byType(NavigationBar), findsOneWidget);
      expect(find.widgetWithText(ActionChip, 'दिल्ली'), findsOneWidget);
      expect(prefs.getString('location.city'), 'delhi');
    });
  });

  testWidgets('a saved city opens straight on Today', (tester) async {
    await launch(tester, await preferences({'location.city': 'palitana'}));

    expect(find.widgetWithText(ActionChip, 'पालीताणा'), findsOneWidget);
    expect(find.text('अपना शहर चुनें'), findsNothing);
  });

  testWidgets('a saved city the app no longer knows asks again', (tester) async {
    await launch(tester, await preferences({'location.city': 'atlantis'}));

    expect(find.text('अपना शहर चुनें'), findsOneWidget);
  });

  testWidgets("Today's location chip changes the city and returns to Today", (tester) async {
    final prefs = await preferences({'location.city': 'delhi'});
    await launch(tester, prefs);

    await tester.tap(find.widgetWithText(ActionChip, 'दिल्ली'));
    await tester.pumpAndSettle();
    expect(
      tester.widget<ChoiceChip>(find.widgetWithText(ChoiceChip, 'दिल्ली')).selected,
      isTrue,
    );

    await tester.tap(find.text('मुंबई'));
    await tester.pumpAndSettle();

    expect(find.widgetWithText(ActionChip, 'मुंबई'), findsOneWidget);
    expect(prefs.getString('location.city'), 'mumbai');
  });

  testWidgets('the tabs are Today and Pachchakkhan', (tester) async {
    await launch(tester, await preferences({'location.city': 'delhi'}));

    final bar = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(bar.destinations, hasLength(2));
    expect(find.descendant(of: find.byType(NavigationBar), matching: find.text('आज')), findsOneWidget);

    await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text('पच्चक्खाण')));
    await tester.pumpAndSettle();

    expect(tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex, 1);
  });

  testWidgets('an English phone sees English', (tester) async {
    await launch(tester, await preferences(), phone: const Locale('en', 'US'));

    expect(find.text('Choose your city'), findsOneWidget);
    expect(find.text('Delhi'), findsOneWidget);
  });
}
