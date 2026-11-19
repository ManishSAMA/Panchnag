import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/location/gps.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

// mobile-ui-design.md §3 · Settings, §1 (how Settings opens), §3.0 step 2 and §8 (GPS).

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

PanchangDay delhiDay(CivilDate date, {SunriseRule rule = SunriseRule.modern}) =>
    const PanchangEngine().day(location: delhiCity, date: date, sunriseRule: rule);

/// Sunrise as Today's and the Month panel's rows print it, read from the engine apart from the screen.
String sunriseTime(CivilDate date, SunriseRule rule) =>
    clockTime(cityWall(delhiDay(date, rule: rule).sunrise, 'Asia/Kolkata'), Lang.hi).time;

Future<void> openSettings(WidgetTester tester) async {
  await tester.tap(find.byTooltip('सेटिंग्स'));
  await tester.pumpAndSettle();
}

/// Scrolls Settings only when needed, so what is already on screen stays there.
Future<void> reveal(WidgetTester tester, String text) async {
  if (find.text(text).hitTestable().evaluate().isNotEmpty) return;
  await tester.scrollUntilVisible(find.text(text), 200, scrollable: find.byType(Scrollable).last);
  await tester.pumpAndSettle();
}

Future<void> tapText(WidgetTester tester, String text) async {
  await reveal(tester, text);
  await tester.tap(find.text(text));
  await tester.pumpAndSettle();
}

/// The top bar's back arrow; `pageBack` looks only for an English tooltip.
Future<void> goBack(WidgetTester tester) async {
  await tester.tap(find.byType(BackButton));
  await tester.pumpAndSettle();
}

Finder option(String label) =>
    find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is RadioListTile));

Future<void> expectChosen(WidgetTester tester, String label, {bool chosen = true}) async {
  await reveal(tester, label);
  expect(tester.getSemantics(option(label)), isSemantics(isChecked: chosen), reason: label);
}

Future<GpsOutcome> Function() gpsAnswers(GpsOutcome outcome) =>
    () async => outcome;

const nearDelhi = GpsFix(lat: 28.65, lon: 77.25, timezone: 'Asia/Kolkata');
const london = GpsFix(lat: 51.5074, lon: -0.1278, timezone: 'Europe/London');

final locationChip = find.byKey(const Key('today-location'));

void main() {
  final oct22 = ist(2026, 10, 22);

  group('Settings opens', () {
    for (final tab in ['आज', 'माह', 'मुहूर्त']) {
      testWidgets('from the gear on the $tab tab, and Back returns to it', (tester) async {
        await openApp(tester, now: oct22);
        if (tab != 'आज') await openTab(tester, tab);

        await openSettings(tester);
        expect(find.text('स्थान'), findsOneWidget);

        await goBack(tester);
        expect(find.byType(NavigationBar), findsOneWidget);
      });
    }

    testWidgets('from the gear on Pachchakkhan, and Back returns to it', (tester) async {
      await openApp(tester, now: oct22);
      final tile = find.byKey(const Key('tile-pachchakkhan'));
      await tester.ensureVisible(tile);
      await tester.tap(tile);
      await tester.pumpAndSettle();

      await openSettings(tester);
      expect(find.text('स्थान'), findsOneWidget);

      await goBack(tester);
      expect(find.descendant(of: find.byType(AppBar), matching: find.text('पच्चक्खाण')), findsOneWidget);
    });

    testWidgets("from Today's location chip, showing the city, its coordinates and time zone", (tester) async {
      await openApp(tester, now: oct22);

      await tester.tap(locationChip);
      await tester.pumpAndSettle();

      expect(find.text('दिल्ली'), findsOneWidget);
      expect(find.text('28.61° N, 77.21° E · Asia/Kolkata'), findsOneWidget);
    });
  });

  group('location', () {
    testWidgets('a city picked from Settings returns to Settings and moves Today there', (tester) async {
      await openApp(tester, now: oct22);
      await openSettings(tester);

      await tapText(tester, 'शहर चुनें');
      await tester.tap(find.widgetWithText(ChoiceChip, 'मुंबई'));
      await tester.pumpAndSettle();

      expect(find.text('19.08° N, 72.88° E · Asia/Kolkata'), findsOneWidget);
      await goBack(tester);
      expect(find.descendant(of: locationChip, matching: find.text('मुंबई')), findsOneWidget);
    });

    testWidgets('a GPS fix near a preset city is named after it, and survives a restart', (tester) async {
      await openApp(tester, now: oct22, gps: gpsAnswers(nearDelhi));
      await openSettings(tester);

      await tapText(tester, 'GPS से पता लगाएँ');

      expect(find.text('दिल्ली के पास'), findsOneWidget);
      expect(find.text('28.65° N, 77.25° E · Asia/Kolkata'), findsOneWidget);

      await restartApp(tester, now: oct22);
      expect(find.descendant(of: locationChip, matching: find.text('दिल्ली के पास')), findsOneWidget);
    });

    testWidgets('a GPS fix outside India is accepted, in the time zone the phone reports', (tester) async {
      // 22 Oct 2026 10:52 IST is 06:22 in London, before its sunrise: still the 22nd there.
      await openApp(tester, now: oct22, gps: gpsAnswers(london));
      await openSettings(tester);

      await tapText(tester, 'GPS से पता लगाएँ');
      expect(find.text('मेरा स्थान'), findsOneWidget);
      expect(find.text('51.51° N, 0.13° W · Europe/London'), findsOneWidget);

      await goBack(tester);
      expect(find.descendant(of: locationChip, matching: find.text('मेरा स्थान')), findsOneWidget);
      expect(find.byKey(const Key('today-hero-tithi')), findsOneWidget);
      final londonSunrise = const PanchangEngine()
          .day(
            location: const Location(lat: 51.5074, lon: -0.1278, timezone: 'Europe/London'),
            date: const CivilDate(2026, 10, 22),
          )
          .sunrise;
      expect(find.text(clockTime(cityWall(londonSunrise, 'Europe/London'), Lang.hi).time), findsOneWidget);
    });

    testWidgets('GPS denied in Settings leaves an inline note and the location unchanged', (tester) async {
      await openApp(tester, now: oct22, gps: gpsAnswers(const GpsDenied()));
      await openSettings(tester);

      await tapText(tester, 'GPS से पता लगाएँ');

      expect(find.textContaining('स्थान की अनुमति नहीं मिली'), findsOneWidget);
      expect(find.text('दिल्ली'), findsOneWidget);
    });

    testWidgets('GPS off on the phone says so', (tester) async {
      await openApp(tester, now: oct22, gps: gpsAnswers(const GpsOff()));
      await openSettings(tester);

      await tapText(tester, 'GPS से पता लगाएँ');

      expect(find.textContaining('फ़ोन का लोकेशन बंद है'), findsOneWidget);
    });

    testWidgets('on first run, GPS denied keeps the city chips usable', (tester) async {
      await openApp(tester, now: oct22, saved: const {}, gps: gpsAnswers(const GpsDenied()));

      await tapText(tester, 'GPS से पता लगाएँ');
      expect(find.textContaining('स्थान की अनुमति नहीं मिली'), findsOneWidget);

      await tester.tap(find.widgetWithText(ChoiceChip, 'दिल्ली'));
      await tester.pumpAndSettle();
      expect(find.byType(NavigationBar), findsOneWidget);
    });

    testWidgets('on first run, a GPS fix opens Today there', (tester) async {
      await openApp(tester, now: oct22, saved: const {}, gps: gpsAnswers(nearDelhi));

      await tapText(tester, 'GPS से पता लगाएँ');

      expect(find.descendant(of: locationChip, matching: find.text('दिल्ली के पास')), findsOneWidget);
    });
  });

  group('tradition', () {
    testWidgets('starts on Murtipujak Tapagachchha', (tester) async {
      await openApp(tester, now: oct22);
      await openSettings(tester);

      await expectChosen(tester, 'मूर्तिपूजक तपागच्छ');
      await expectChosen(tester, 'स्थानकवासी', chosen: false);
    });

    testWidgets("is saved as the profile's string ID and survives a restart", (tester) async {
      await openApp(tester, now: oct22);
      await openSettings(tester);

      await tapText(tester, 'स्थानकवासी');

      final prefs = await restartApp(tester, now: oct22);
      // The festival port reads this ID (FESTIVAL_PROFILES in festival_service.py).
      expect(prefs.getString('settings.tradition'), 'shwetambar_sthanakvasi');
      await openSettings(tester);
      await expectChosen(tester, 'स्थानकवासी');
    });
  });

  group('language', () {
    testWidgets('follows the phone until overridden, and the override survives a restart', (tester) async {
      await openApp(tester, now: oct22);
      await openSettings(tester);
      await expectChosen(tester, 'फ़ोन के अनुसार');

      await tapText(tester, 'English');
      expect(find.text('Settings'), findsOneWidget);

      await restartApp(tester, now: oct22);
      expect(find.descendant(of: find.byType(NavigationBar), matching: find.text('Today')), findsOneWidget);
    });

    testWidgets('"same as phone" goes back to the phone\'s language', (tester) async {
      await openApp(tester, now: oct22, phone: const Locale('en', 'US'));
      await tester.tap(find.byTooltip('Settings'));
      await tester.pumpAndSettle();

      await tapText(tester, 'हिन्दी');
      expect(find.text('सेटिंग्स'), findsOneWidget);
      await tapText(tester, 'फ़ोन के अनुसार');
      expect(find.text('Settings'), findsOneWidget);
    });
  });

  group('month system', () {
    // 3 Oct 2026 is in Krishna paksha, where the two systems name different months.
    const oct3 = CivilDate(2026, 10, 3);
    final purnimanta = monthName(delhiDay(oct3).month, Lang.hi);
    final amanta = monthName(delhiDay(oct3).amantaMonth, Lang.hi);

    testWidgets('Amanta renames a Krishna paksha month on Today, live and after a restart', (tester) async {
      expect(amanta, isNot(purnimanta));
      await openApp(tester, now: ist(2026, 10, 3));
      expect(find.textContaining('$purnimanta · ', findRichText: true), findsOneWidget);

      await openSettings(tester);
      await expectChosen(tester, 'पूर्णिमान्त');
      await tapText(tester, 'अमान्त');
      await goBack(tester);

      expect(find.textContaining('$amanta · ', findRichText: true), findsOneWidget);
      expect(find.textContaining('$purnimanta · ', findRichText: true), findsNothing);

      await restartApp(tester, now: ist(2026, 10, 3));
      expect(find.textContaining('$amanta · ', findRichText: true), findsOneWidget);
    });

    testWidgets("Amanta renames the month in the Month tab's day panel", (tester) async {
      await openApp(tester, now: ist(2026, 10, 3));
      await openTab(tester, 'माह');
      final panel = find.byKey(const Key('month-day-panel'));
      expect(find.descendant(of: panel, matching: find.text(purnimanta)), findsOneWidget);

      await openSettings(tester);
      await tapText(tester, 'अमान्त');
      await goBack(tester);

      expect(find.descendant(of: panel, matching: find.text(amanta)), findsOneWidget);
    });
  });

  group('sunrise rule', () {
    const oct22Date = CivilDate(2026, 10, 22);
    final modern = sunriseTime(oct22Date, SunriseRule.modern);
    final traditional = sunriseTime(oct22Date, SunriseRule.traditional);

    testWidgets("Traditional moves Today's sunrise, live and after a restart", (tester) async {
      expect(traditional, isNot(modern));
      await openApp(tester, now: oct22);
      expect(find.text(modern), findsOneWidget);

      await openSettings(tester);
      await expectChosen(tester, 'आधुनिक');
      await tapText(tester, 'पारंपरिक');
      await goBack(tester);

      expect(find.text(traditional), findsOneWidget);
      expect(find.text(modern), findsNothing);

      await restartApp(tester, now: oct22);
      expect(find.text(traditional), findsOneWidget);
    });

    testWidgets("Traditional moves the Month tab's sunrise", (tester) async {
      await openApp(tester, now: oct22);
      await openTab(tester, 'माह');
      final panel = find.byKey(const Key('month-day-panel'));
      expect(find.descendant(of: panel, matching: find.textContaining(modern)), findsOneWidget);

      await openSettings(tester);
      await tapText(tester, 'पारंपरिक');
      await goBack(tester);

      expect(find.descendant(of: panel, matching: find.textContaining(traditional)), findsOneWidget);
    });

    testWidgets('Traditional moves the Choghadiya slots, which start at sunrise', (tester) async {
      // Choghadiya rows drop the seconds, so read the start as they print it.
      String firstSlotStart(SunriseRule rule) =>
          clockTime(roundDownToMinute(cityWall(delhiDay(oct22Date, rule: rule).sunrise, 'Asia/Kolkata')), Lang.hi).time;
      expect(firstSlotStart(SunriseRule.traditional), isNot(firstSlotStart(SunriseRule.modern)));
      await openApp(tester, now: oct22);
      await openSettings(tester);
      await tapText(tester, 'पारंपरिक');
      await goBack(tester);

      for (final key in ['tile-muhurat', 'muhurat-tile-choghadiya']) {
        await tester.ensureVisible(find.byKey(Key(key)));
        await tester.tap(find.byKey(Key(key)));
        await tester.pumpAndSettle();
      }

      // Thursday's first day slot is Shubh.
      expect(find.bySemanticsLabel(RegExp('^शुभ ✓ अच्छा सुबह ${firstSlotStart(SunriseRule.traditional)}–')), findsOneWidget);
    });
  });

  group('accessibility at text scale 1.3', () {
    for (final (name, phone) in const [('Hindi', Locale('hi', 'IN')), ('English', Locale('en', 'US'))]) {
      testWidgets('every Settings control is at least 48 dp and labelled ($name)', (tester) async {
        await openApp(tester, now: oct22, phone: phone, textScale: 1.3, gps: gpsAnswers(const GpsDenied()));
        await tester.tap(find.byTooltip(phone.languageCode == 'en' ? 'Settings' : 'सेटिंग्स'));
        await tester.pumpAndSettle();
        await tester.tap(find.text(phone.languageCode == 'en' ? 'Find by GPS' : 'GPS से पता लगाएँ'));
        await tester.pumpAndSettle();

        final list = find.byType(Scrollable).first;
        for (var page = 0; page < 6; page++) {
          await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
          await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
          await tester.drag(list, const Offset(0, -500));
          await tester.pumpAndSettle();
        }
      });
    }

    testWidgets('the first-run picker with its GPS action is too', (tester) async {
      await openApp(tester, now: oct22, textScale: 1.3, saved: const {}, gps: gpsAnswers(const GpsDenied()));
      await tester.tap(find.text('GPS से पता लगाएँ'));
      await tester.pumpAndSettle();

      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
      await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    });
  });
}
