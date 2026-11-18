/// The whole app on a phone-sized view, with a fixed clock and the real engine
/// read on the test's own isolate.
library;

import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/app.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/engine/festival_reading.dart';
import 'package:jainpanchang/features/festivals/festival_state.dart';
import 'package:jainpanchang/features/month/month_state.dart';
import 'package:jainpanchang/features/muhurat/muhurat_state.dart';
import 'package:jainpanchang/features/share/share_button.dart';
import 'package:jainpanchang/features/today/today_state.dart';
import 'package:jainpanchang/location/gps.dart';
import 'package:panchang_engine/panchang_engine.dart';
import 'package:shared_preferences/shared_preferences.dart';

const istOffset = Duration(hours: 5, minutes: 30);

/// A wall-clock time in Delhi as a UTC instant.
DateTime ist(int year, int month, int day, [int hour = 10, int minute = 52]) =>
    DateTime.utc(year, month, day, hour, minute).subtract(istOffset);

/// The bundled registry, read once per test file.
final testRegistry = FestivalRegistry.fromJson(File('assets/festival_registry.json').readAsStringSync());

/// The real festival engine on the test's own isolate; [readFestivals] keeps
/// each year, so a test file computes it once.
Future<List<FestivalOccurrence>> realFestivals(FestivalRequest request) async =>
    readFestivals(request, registry: testRegistry);

/// A reader that answers only when the test lets it, as a slow phone would.
final class HeldFestivals {
  final requests = <FestivalRequest>[];
  final _held = <Completer<List<FestivalOccurrence>>>[];

  Future<List<FestivalOccurrence>> call(FestivalRequest request) {
    requests.add(request);
    final answer = Completer<List<FestivalOccurrence>>();
    _held.add(answer);
    return answer.future;
  }

  void release() {
    for (final (i, answer) in _held.indexed) {
      answer.complete(readFestivals(requests[i], registry: testRegistry));
    }
    _held.clear();
  }
}

/// Tests that never tap share get a share sheet that fails if they do.
Future<void> noShare(SharedDay day) async => throw StateError('This test did not expect a share.');

/// Tests that never tap the GPS action get one that fails if they do.
Future<GpsOutcome> noGps() async => throw StateError('This test did not expect a GPS request.');

Future<SharedPreferences> openApp(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
  Size screen = const Size(1080, 2400),
  Map<String, Object> saved = const {'location.city': 'delhi'},
  GpsLocator gps = noGps,
  FestivalReader festivals = realFestivals,
  Sharer sharer = noShare,
}) async {
  SharedPreferences.resetStatic();
  SharedPreferences.setMockInitialValues(saved);
  tester.view.physicalSize = screen;
  tester.view.devicePixelRatio = 2.75;
  tester.platformDispatcher.localesTestValue = [phone];
  tester.platformDispatcher.textScaleFactorTestValue = textScale;
  addTearDown(tester.view.reset);
  addTearDown(tester.platformDispatcher.clearAllTestValues);
  return _pumpApp(tester, now: now, gps: gps, festivals: festivals, sharer: sharer);
}

/// A cold start: a fresh app reading back only what the last run saved.
Future<SharedPreferences> restartApp(WidgetTester tester, {required DateTime now, GpsLocator gps = noGps}) async {
  await tester.pumpWidget(const SizedBox());
  SharedPreferences.resetStatic();
  return _pumpApp(tester, now: now, gps: gps, festivals: realFestivals, sharer: noShare);
}

Future<SharedPreferences> _pumpApp(
  WidgetTester tester, {
  required DateTime now,
  required GpsLocator gps,
  required FestivalReader festivals,
  required Sharer sharer,
}) async {
  final prefs = await SharedPreferences.getInstance();
  await tester.pumpWidget(
    JainPanchangApp(
      key: UniqueKey(),
      preferences: prefs,
      overrides: [
        clockProvider.overrideWithValue(() => now),
        nowProvider.overrideWith((ref) => Stream.value(now)),
        // The real engine, on the test's own isolate.
        dayReaderProvider.overrideWithValue((request) async => readDay(request)),
        sectionReaderProvider.overrideWithValue((request) async => readSection(request)),
        muhuratReaderProvider.overrideWithValue((request) async => readMuhurat(request)),
        monthReaderProvider.overrideWithValue((request) async => readMonth(request)),
        festivalReaderProvider.overrideWithValue(festivals),
        gpsLocatorProvider.overrideWithValue(gps),
        sharerProvider.overrideWithValue(sharer),
      ],
    ),
  );
  await tester.pumpAndSettle();
  return prefs;
}

Finder nav(String tooltip) => find.byTooltip(tooltip);

Future<void> openTab(WidgetTester tester, String label) async {
  await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text(label)));
  await tester.pumpAndSettle();
}
