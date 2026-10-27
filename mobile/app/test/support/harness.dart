/// The whole app on a phone-sized view, with a fixed clock and the real engine
/// read on the test's own isolate.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/app.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/features/today/today_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

const istOffset = Duration(hours: 5, minutes: 30);

/// A wall-clock time in Delhi as a UTC instant.
DateTime ist(int year, int month, int day, [int hour = 10, int minute = 52]) =>
    DateTime.utc(year, month, day, hour, minute).subtract(istOffset);

Future<void> openApp(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
}) async {
  SharedPreferences.setMockInitialValues({'location.city': 'delhi'});
  final prefs = await SharedPreferences.getInstance();
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = 2.75;
  tester.platformDispatcher.localesTestValue = [phone];
  tester.platformDispatcher.textScaleFactorTestValue = textScale;
  addTearDown(tester.view.reset);
  addTearDown(tester.platformDispatcher.clearAllTestValues);

  await tester.pumpWidget(
    JainPanchangApp(
      preferences: prefs,
      overrides: [
        clockProvider.overrideWithValue(() => now),
        nowProvider.overrideWith((ref) => Stream.value(now)),
        // The real engine, on the test's own isolate.
        dayReaderProvider.overrideWithValue((request) async => readDay(request)),
      ],
    ),
  );
  await tester.pumpAndSettle();
}

Finder nav(String tooltip) => find.byTooltip(tooltip);
