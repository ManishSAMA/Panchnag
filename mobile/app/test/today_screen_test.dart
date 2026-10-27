import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/features/today/today_state.dart';
import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:panchang_engine/src/time/civil_day.dart';

import 'support/harness.dart';

String heroTithi(WidgetTester tester) => tester.widget<Text>(find.byKey(const Key('today-hero-tithi'))).data!;

/// The Jain tithi straight from the engine, independent of the screen's own reading.
int engineJainTithi(CivilDate date) {
  const delhi = (lat: 28.6139, lon: 77.2090);
  final rise = sunrise(civilDayAnchor(date, 'Asia/Kolkata'), delhi.lat, delhi.lon, SunriseRule.modern);
  return tithiAt(rise + jainTithiOffsetDays);
}

void main() {
  group('the hero', () {
    testWidgets('shows the Jain tithi, its month and both samvats', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      expect(engineJainTithi(const CivilDate(2026, 10, 22)), 11);
      expect(heroTithi(tester), 'शुक्ल एकादशी');
      expect(find.textContaining('आश्विन', findRichText: true), findsWidgets);
      expect(find.textContaining('फिर शुक्ल द्वादशी', findRichText: true), findsOneWidget);
      expect(find.textContaining('वीर नि. सं. 2552 · वि. सं. 2083', findRichText: true), findsOneWidget);
    });

    testWidgets('shows the tithi at sunrise + 2 h 24 min, not the sunrise tithi', (tester) async {
      // 3 Oct 2026: Krishna Saptami holds at sunrise and ends before the reference instant.
      await openApp(tester, now: ist(2026, 10, 3));

      expect(engineJainTithi(const CivilDate(2026, 10, 3)), 23);
      expect(heroTithi(tester), 'कृष्ण अष्टमी');
    });

    testWidgets('is in English on an English phone', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22), phone: const Locale('en', 'US'));

      expect(heroTithi(tester), 'Shukla Ekadashi');
      expect(find.textContaining('VNS 2552 · VS 2083', findRichText: true), findsOneWidget);
    });
  });

  group('the date navigator', () {
    testWidgets('shows the full date and that it is today', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      expect(find.text('गुरुवार, 22 अक्टूबर 2026'), findsOneWidget);
      expect(find.widgetWithText(ActionChip, 'आज'), findsNothing);
    });

    testWidgets('moves a day at a time and offers a way back to today', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();
      expect(find.text('शुक्रवार, 23 अक्टूबर 2026'), findsOneWidget);

      await tester.tap(find.widgetWithText(ActionChip, 'आज'));
      await tester.pumpAndSettle();
      expect(find.text('गुरुवार, 22 अक्टूबर 2026'), findsOneWidget);

      await tester.tap(nav('पिछला दिन'));
      await tester.pumpAndSettle();
      expect(find.text('बुधवार, 21 अक्टूबर 2026'), findsOneWidget);
    });

    testWidgets('stops at 31 Dec 2040', (tester) async {
      await openApp(tester, now: ist(2040, 12, 31));

      expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.chevron_right)).onPressed, isNull);
      expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.chevron_left)).onPressed, isNotNull);
    });

    testWidgets('stops at 1 Jan 2016', (tester) async {
      await openApp(tester, now: ist(2016, 1, 1));

      expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.chevron_left)).onPressed, isNull);
    });
  });

  group('pachchakkhan on today', () {
    // Mockup board 1 (Delhi, 22 Oct 2026, 10:52): sunrise 06:26:12, sunset 17:44:41,
    // so Purimaddh (the midpoint) is 12:05:26, shown rounded up as 12:06.
    testWidgets('the yellow band names the next one with its time and countdown', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      expect(find.text('अगला: पुरिमड्ढ'), findsOneWidget);
      expect(find.text('12:06 · 1 घं 14 मि में'), findsOneWidget);
    });

    testWidgets('the rows mark the passed times done and the coming one next', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      for (final name in ['नवकारसी', 'पोरसी', 'साढ़-पोरसी']) {
        expect(find.bySemanticsLabel(RegExp('^$name .*, हो गया\$')), findsOneWidget, reason: name);
      }
      expect(find.bySemanticsLabel(RegExp(r'^पुरिमड्ढ 12:06, अगला')), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^अवड्ढ .*, बाकी$')), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^चौविहार 5:44, बाकी$')), findsOneWidget);
    });

    testWidgets('after Avaddh the band counts down to sunset for Chauvihar, which is next', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22, 16, 30));

      expect(find.text('अगला: चौविहार'), findsOneWidget);
      expect(find.text('सूर्यास्त से पहले'), findsOneWidget);
      expect(find.text('5:44 · 1 घं 15 मि में'), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^चौविहार 5:44, अगला$')), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^अवड्ढ .*, हो गया$')), findsOneWidget);
    });

    testWidgets('after sunset there is no band and nothing is next', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22, 18, 30));

      expect(find.textContaining('अगला:'), findsNothing);
      expect(find.bySemanticsLabel(RegExp(r', अगला')), findsNothing);
      expect(find.bySemanticsLabel(RegExp(r'^चौविहार 5:44, हो गया$')), findsOneWidget);
    });

    testWidgets('another day has no yellow and no done or next rows', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();

      expect(find.textContaining('अगला:'), findsNothing);
      expect(find.bySemanticsLabel(RegExp(r', (हो गया|अगला)')), findsNothing);
      expect(find.bySemanticsLabel(RegExp(r'^नवकारसी ')), findsOneWidget);
    });

    testWidgets('the band opens the Pachchakkhan tab', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      await tester.tap(find.text('अगला: पुरिमड्ढ'));
      await tester.pumpAndSettle();

      expect(tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex, 1);
    });
  });

  testWidgets("today's times list sunrise, sunset and the nakshatra with its pada", (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));

    expect(find.text('सूर्योदय'), findsOneWidget);
    expect(find.text('सूर्यास्त'), findsOneWidget);
    expect(find.textContaining(RegExp(r'^शतभिषा \(चरण [1-4]\), फिर पूर्वा भाद्रपद$')), findsOneWidget);
  });

  group('notes', () {
    testWidgets('vriddhi, first day (18 Oct 2026)', (tester) async {
      await openApp(tester, now: ist(2026, 10, 18));

      expect(find.text('वृद्धि तिथि · पहला दिन'), findsOneWidget);
    });

    testWidgets('vriddhi, second day (19 Oct 2026)', (tester) async {
      await openApp(tester, now: ist(2026, 10, 19));

      expect(find.text('वृद्धि तिथि · दूसरा दिन'), findsOneWidget);
    });

    testWidgets('kshaya names the lost tithi (3 Oct 2026)', (tester) async {
      await openApp(tester, now: ist(2026, 10, 3));

      expect(find.text('क्षय तिथि'), findsOneWidget);
      expect(find.textContaining('कृष्ण सप्तमी'), findsOneWidget);
      expect(find.textContaining('कृष्ण षष्ठी के बाद सीधे कृष्ण अष्टमी'), findsOneWidget);
    });

    testWidgets('a tithi change near the reference instant (27 Nov 2026)', (tester) async {
      await openApp(tester, now: ist(2026, 11, 27));

      expect(find.text('तिथि बदलने का समय पास है'), findsOneWidget);
    });

    testWidgets('an ordinary day has none (22 Oct 2026)', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      expect(find.byKey(const Key('today-note')), findsNothing);
    });
  });

  for (final scale in [1.3, 1.6]) {
    testWidgets('nothing overflows at ${scale}x text on a busy day', (tester) async {
      await openApp(tester, now: ist(2026, 11, 27), textScale: scale);

      expect(tester.takeException(), isNull);
      expect(heroTithi(tester), isNotEmpty);
    });
  }

  testWidgets('every Today control is at least 48 dp', (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));

    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  });

  test('the reader runs off the UI isolate by default', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final reading = await container.read(dayReaderProvider)(
      const DayRequest(date: CivilDate(2026, 10, 22), lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
    );

    expect(reading.jainTithi, 11);
  });
}
