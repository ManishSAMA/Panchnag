import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:jainpanchang/engine/day_reading.dart';
import 'package:panchang_engine/src/time/civil_day.dart';

import 'support/harness.dart';

Future<void> openPachchakkhan(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
}) async {
  await openApp(tester, now: now, phone: phone, textScale: textScale);
  await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text(tabName(phone))));
  await tester.pumpAndSettle();
}

String tabName(Locale phone) => phone.languageCode == 'en' ? 'Pachchakkhan' : 'पच्चक्खाण';

final hero = find.byKey(const Key('pachchakkhan-hero'));
final quietHero = find.byKey(const Key('pachchakkhan-all-done'));

Finder inHero(Finder finder) => find.descendant(of: hero, matching: finder);

/// 23 Oct 2026's Navkarsi in Delhi as the engine gives it, rounded up to the minute.
String navkarsi23Oct() {
  final at = readDay(
    const DayRequest(date: CivilDate(2026, 10, 23), lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
  ).pachchakkhan.first.at.add(istOffset);
  expect(at.second + at.millisecond, isNot(0), reason: 'rounding up must change the minute');
  final up = at.add(const Duration(minutes: 1));
  return '${up.hour}:${up.minute.toString().padLeft(2, '0')}';
}

/// Delhi, 22 Oct 2026 (modern sunrise): sunrise 06:26:12 and sunset 17:44:47, so the
/// completions fall at 07:14:12, 09:15:50, 10:40:40, 12:05:29 and 14:55:08, and are
/// shown rounded up: 7:15, 9:16, 10:41, 12:06 and 2:56. Sunset is shown rounded down, 5:44.
void main() {
  group('the hero on today', () {
    testWidgets('names the next pachchakkhan, when it may be completed and a live countdown', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

      expect(inHero(find.text('पुरिमड्ढ')), findsOneWidget);
      expect(inHero(find.text('अगला पच्चक्खाण · 12:06 के बाद पार सकते हैं')), findsOneWidget);
      expect(inHero(find.textContaining(RegExp(r'^1:13:\d\d$'))), findsOneWidget);
    });

    testWidgets('before sunrise, Navkarsi is next', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 5, 0));

      expect(inHero(find.text('नवकारसी')), findsOneWidget);
      expect(inHero(find.text('अगला पच्चक्खाण · 7:15 के बाद पार सकते हैं')), findsOneWidget);
    });

    testWidgets('after Avaddh, it counts down to sunset for the evening pachchakkhan', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 16, 30));

      expect(inHero(find.text('चौविहार')), findsOneWidget);
      expect(inHero(find.text('सूर्यास्त से पहले · शाम 5:44')), findsOneWidget);
      expect(inHero(find.textContaining(RegExp(r'^1:14:\d\d$'))), findsOneWidget);
    });

    testWidgets('after sunset, a quiet row gives tomorrow\'s Navkarsi and there is no yellow', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 18, 30));

      expect(hero, findsNothing);
      expect(
        find.descendant(of: quietHero, matching: find.text('आज के सभी समय हो गए · कल नवकारसी सुबह ${navkarsi23Oct()}')),
        findsOneWidget,
      );
      expect(find.bySemanticsLabel(RegExp(r', अगला$')), findsNothing);
    });

    testWidgets('is in English on an English phone', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52), phone: const Locale('en', 'US'));

      expect(inHero(find.text('Purimaddh')), findsOneWidget);
      expect(inHero(find.text('Next pachchakkhan · can be completed after 12:06')), findsOneWidget);
    });
  });

  testWidgets('another day has no hero, no yellow and no done or next rows', (tester) async {
    await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));
    await tester.tap(nav('अगला दिन'));
    await tester.pumpAndSettle();

    expect(find.text('शुक्रवार, 23 अक्टूबर 2026'), findsOneWidget);
    expect(hero, findsNothing);
    expect(quietHero, findsNothing);
    expect(find.bySemanticsLabel(RegExp(r', (हो गया|अगला|बाकी)$')), findsNothing);
    expect(find.bySemanticsLabel(RegExp(r'^नवकारसी ')), findsOneWidget);
  });

  testWidgets('shares its date with Today', (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));
    await tester.tap(nav('अगला दिन'));
    await tester.pumpAndSettle();
    await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text('पच्चक्खाण')));
    await tester.pumpAndSettle();

    expect(find.text('शुक्रवार, 23 अक्टूबर 2026'), findsOneWidget);
  });

  testWidgets('the header gives the city, sunrise and sunset', (tester) async {
    await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

    expect(find.text('दिल्ली · सूर्योदय सुबह 6:26 · सूर्यास्त शाम 5:44'), findsOneWidget);
  });

  group('the completion times', () {
    testWidgets('each row gives its rule and its time, rounded up', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

      expect(find.text('पारने का समय'), findsOneWidget);
      for (final (name, rule, time) in [
        ('नवकारसी', 'सूर्योदय + 48 मि', '7:15'),
        ('पोरसी', 'दिन का ¼', '9:16'),
        ('साढ़-पोरसी', 'दिन का ⅜', '10:41'),
        ('पुरिमड्ढ', 'दिन का ½', '12:06'),
        ('अवड्ढ', 'दिन का ¾', '2:56'),
      ]) {
        expect(find.bySemanticsLabel(RegExp('^$name $time, ')), findsOneWidget, reason: name);
        expect(find.text(rule), findsOneWidget, reason: name);
      }
    });

    testWidgets('mark the passed ones done and the coming one next', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

      for (final name in ['नवकारसी', 'पोरसी', 'साढ़-पोरसी']) {
        expect(find.bySemanticsLabel(RegExp('^$name .*, हो गया\$')), findsOneWidget, reason: name);
      }
      expect(find.bySemanticsLabel('पुरिमड्ढ 12:06, अगला'), findsOneWidget);
      expect(find.bySemanticsLabel('अवड्ढ 2:56, बाकी'), findsOneWidget);
    });
  });

  group('the evening pachchakkhans', () {
    const evening = 'चौविहार · तिविहार · दुविहार';

    testWidgets('share one row at sunset, rounded down', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

      expect(find.text('सूर्यास्त से पहले'), findsOneWidget);
      expect(find.bySemanticsLabel('$evening 5:44, बाकी'), findsOneWidget);
    });

    testWidgets('are next after Avaddh and done after sunset', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 16, 30));
      expect(find.bySemanticsLabel('$evening 5:44, अगला'), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^अवड्ढ .*, हो गया$')), findsOneWidget);
    });
  });

  testWidgets('the other pachchakkhans have no clock time of their own, except the parana', (tester) async {
    await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

    expect(find.text('अन्य'), findsOneWidget);
    expect(find.text('मुट्ठीसहियं'), findsOneWidget);
    expect(find.text('कोई तय समय नहीं'), findsOneWidget);
    expect(find.text('एकासणा · बियासणा'), findsOneWidget);
    expect(find.text('ऊपर के किसी समय के साथ'), findsOneWidget);
    expect(find.text('आयंबिल · उपवास'), findsOneWidget);
    expect(find.text('23 अक्टूबर, सुबह ${navkarsi23Oct()}'), findsOneWidget);
  });

  for (final scale in [1.3, 1.6, 2.0]) {
    testWidgets('nothing overflows at ${scale}x text', (tester) async {
      await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52), textScale: scale);

      expect(tester.takeException(), isNull);
      expect(hero, findsOneWidget);
    });
  }

  testWidgets('every Pachchakkhan control is at least 48 dp', (tester) async {
    await openPachchakkhan(tester, now: ist(2026, 10, 22, 10, 52));

    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  });
}
