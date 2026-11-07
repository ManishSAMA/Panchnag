import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/theme/pothi.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

final fullPage = find.byKey(const Key('full-panchang-screen'));
final fullTile = find.byKey(const Key('tile-full-panchang'));

Future<void> openFullPanchang(
  WidgetTester tester, {
  DateTime? now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
}) async {
  await openApp(
    tester,
    now: now ?? ist(2026, 10, 22),
    phone: phone,
    textScale: textScale,
  );
  await tester.ensureVisible(fullTile);
  await tester.tap(fullTile);
  await tester.pumpAndSettle();
}

PanchangDay delhiDay([CivilDate date = const CivilDate(2026, 10, 22)]) =>
    readDay(
      DayRequest(
        date: date,
        lat: 28.6139,
        lon: 77.2090,
        timezone: 'Asia/Kolkata',
      ),
    );

String shownTime(DateTime utc) =>
    clockPhrase(roundDownToMinute(cityWall(utc, 'Asia/Kolkata')), Lang.hi);

void main() {
  testWidgets(
    'Today opens the full day outside the tabs and returns to Today',
    (tester) async {
      await openFullPanchang(tester);

      expect(fullPage, findsOneWidget);
      expect(find.byType(NavigationBar), findsNothing);
      expect(find.text('पूरा पंचांग'), findsOneWidget);

      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();
      expect(fullPage, findsNothing);
      expect(fullTile, findsOneWidget);
    },
  );

  testWidgets('the tithi moon sits inside a double-ring vermilion seal', (
    tester,
  ) async {
    await openFullPanchang(tester);

    final seal = find.byKey(const Key('full-lunar-seal'));
    final context = tester.element(seal);
    final accent = Theme.of(context).extension<Pothi>()!.accent;
    final rings = [
      tester.widget<Container>(seal),
      tester.widget<Container>(
        find.descendant(of: seal, matching: find.byType(Container)),
      ),
    ];
    for (final ring in rings) {
      final decoration = ring.decoration! as BoxDecoration;
      expect(decoration.shape, BoxShape.circle);
      expect(decoration.border!.top.color, accent);
    }
  });

  testWidgets(
    'the almanac identifies the date, place, Jain tithi, both months and both samvats',
    (tester) async {
      final day = delhiDay();
      await openFullPanchang(tester);

      expect(find.text(longDate(day.date, Lang.hi)), findsOneWidget);
      expect(find.textContaining('दिल्ली'), findsWidgets);
      expect(
        tester.widget<Text>(find.byKey(const Key('full-hero-tithi'))).data,
        tithiName(day.jainTithi.index, Lang.hi),
      );
      expect(find.text(monthName(day.month, Lang.hi)), findsWidgets);
      expect(find.text(monthName(day.amantaMonth, Lang.hi)), findsWidgets);
      expect(find.text('${day.vikramSamvat}'), findsWidgets);
      expect(find.text('${day.viraNirvanaSamvat}'), findsWidgets);
      expect(find.textContaining('पूर्णिमान्त'), findsWidgets);
      expect(find.textContaining('अमान्त'), findsWidgets);
    },
  );

  testWidgets(
    'all solar, nakshatra, Jain reference and tithi-span values come from the selected engine day',
    (tester) async {
      final day = delhiDay();
      await openFullPanchang(tester);

      for (final instant in [day.sunrise, day.sunset, day.nextSunrise]) {
        expect(find.text(shownTime(instant)), findsWidgets);
      }
      expect(
        find.textContaining(nakshatraName(day.nakshatra.index, Lang.hi)),
        findsWidgets,
      );
      expect(find.textContaining('चरण ${day.nakshatra.pada}'), findsWidgets);
      expect(
        find.textContaining(shownTime(day.nakshatra.endsAt)),
        findsWidgets,
      );
      expect(find.text(shownTime(day.jainTithi.reference)), findsWidgets);
      expect(find.byKey(const Key('full-jain-tithi-start')), findsOneWidget);
      expect(find.byKey(const Key('full-jain-tithi-end')), findsOneWidget);
      for (final (index, span) in day.tithis.indexed) {
        final row = find.byKey(Key('full-tithi-span-$index'));
        expect(row, findsOneWidget);
        expect(
          find.descendant(
            of: row,
            matching: find.text(tithiName(span.index, Lang.hi)),
          ),
          findsOneWidget,
        );
        if (span.endsAt case final endsAt?) {
          expect(
            find.descendant(of: row, matching: find.text(shownTime(endsAt))),
            findsOneWidget,
          );
        }
      }
    },
  );

  testWidgets(
    'all pachchakkhan and all sixteen choghadiya values are present',
    (tester) async {
      final day = delhiDay();
      await openFullPanchang(tester);

      for (final (index, completion) in day.pachchakkhan.completions.indexed) {
        final row = find.byKey(Key('full-pachchakkhan-$index'));
        expect(row, findsOneWidget);
        expect(
          find.descendant(
            of: row,
            matching: find.text(pachchakkhanName(completion.kind, Lang.hi)),
          ),
          findsOneWidget,
        );
        expect(
          find.descendant(
            of: row,
            matching: find.text(
              clockPhrase(
                roundUpToMinute(cityWall(completion.at, 'Asia/Kolkata')),
                Lang.hi,
              ),
            ),
          ),
          findsOneWidget,
        );
      }
      expect(
        find.byKey(const Key('full-pachchakkhan-evening')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('full-pachchakkhan-parana')), findsOneWidget);
      for (final (index, slot) in day.choghadiya.indexed) {
        final row = find.byKey(Key('full-choghadiya-$index'));
        expect(row, findsOneWidget);
        expect(
          find.descendant(
            of: row,
            matching: find.text(choghadiyaName(slot.name, Lang.hi)),
          ),
          findsOneWidget,
        );
        expect(find.text(natureLabelForTest(slot.name.nature)), findsWidgets);
      }
    },
  );

  testWidgets(
    'the date navigator changes the full day and the shared selected date',
    (tester) async {
      await openFullPanchang(tester);
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();

      expect(
        find.text(longDate(const CivilDate(2026, 10, 23), Lang.hi)),
        findsOneWidget,
      );
      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();
      expect(
        find.text(longDate(const CivilDate(2026, 10, 23), Lang.hi)),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'kshaya and vriddhi remain explained instead of becoming bare flags',
    (tester) async {
      await openFullPanchang(tester, now: ist(2026, 10, 3));
      expect(find.text('क्षय तिथि'), findsOneWidget);

      await restartApp(tester, now: ist(2026, 10, 18));
      await tester.tap(fullTile);
      await tester.pumpAndSettle();
      expect(find.text('वृद्धि तिथि · पहला दिन'), findsOneWidget);
    },
  );

  testWidgets('English readers get the same complete day in English', (
    tester,
  ) async {
    final day = delhiDay();
    await openFullPanchang(tester, phone: const Locale('en', 'US'));

    expect(find.text('Full Panchang'), findsOneWidget);
    expect(
      tester.widget<Text>(find.byKey(const Key('full-hero-tithi'))).data,
      tithiName(day.jainTithi.index, Lang.en),
    );
    expect(find.text('Purnimanta month'), findsOneWidget);
    expect(find.text('Amanta month'), findsOneWidget);
    expect(find.text('Vikram Samvat'), findsOneWidget);
    expect(find.text('Vira Nirvana Samvat'), findsOneWidget);
    expect(find.text('Next sunrise'), findsOneWidget);
    expect(find.byTooltip('Symbol guide'), findsOneWidget);
  });

  testWidgets('section links move the requested almanac group into view', (
    tester,
  ) async {
    await openFullPanchang(tester);
    final link = find.widgetWithText(TextButton, 'चौघड़िया');
    await tester.ensureVisible(link);
    await tester.tap(link);
    await tester.pumpAndSettle();

    final rect = tester.getRect(find.byKey(const Key('full-choghadiya-0')));
    expect(rect.top, greaterThanOrEqualTo(0));
    expect(rect.top, lessThan(tester.getSize(fullPage).height));
  });

  testWidgets(
    'the day shows its registry festivals, including a multi-day span',
    (tester) async {
      await openFullPanchang(tester, now: ist(2026, 11, 17));

      expect(find.text('दीपावली (भगवान महावीर निर्वाण)'), findsNothing);
      expect(find.textContaining('17–24 नवंबर'), findsOneWidget);
    },
  );

  testWidgets('unsupported competitor calculations are not fabricated', (
    tester,
  ) async {
    await openFullPanchang(tester, phone: const Locale('en', 'US'));

    for (final label in [
      'Mantri Mandala',
      'Rahu Kalam',
      'Tamil Yoga',
      'Kaliyuga',
    ]) {
      expect(find.textContaining(label), findsNothing);
    }
  });

  for (final scale in [1.3, 1.6, 2.0]) {
    testWidgets('nothing overflows at ${scale}x text', (tester) async {
      await openFullPanchang(tester, textScale: scale);
      expect(tester.takeException(), isNull);
      expect(fullPage, findsOneWidget);
    });
  }

  testWidgets('every Full Panchang control is at least 48 dp and labelled', (
    tester,
  ) async {
    await openFullPanchang(tester);

    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  });
}

String natureLabelForTest(ChoghadiyaNature nature) => switch (nature) {
  ChoghadiyaNature.auspicious => 'अच्छा',
  ChoghadiyaNature.neutral => 'सामान्य',
  ChoghadiyaNature.inauspicious => 'टालें',
};
