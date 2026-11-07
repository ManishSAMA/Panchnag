import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/shared/panchang_symbols.dart';
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

PanchangSection delhiSection([
  CivilDate date = const CivilDate(2026, 10, 22),
]) => readSection(
  SectionRequest(
    DayRequest(
      date: date,
      lat: 28.6139,
      lon: 77.2090,
      timezone: 'Asia/Kolkata',
    ),
  ),
);

/// The end of a section line as shown: the time, dated when off the day.
String shownEnd(DateTime utc, CivilDate day, Lang lang) => instantPhrase(
  roundDownToMinute(cityWall(utc, 'Asia/Kolkata')),
  day: day,
  lang: lang,
);

Finder line(String key) => find.byKey(Key(key));

String lineText(WidgetTester tester, String key) => tester
    .widget<RichText>(
      find.descendant(of: line(key), matching: find.byType(RichText)).first,
    )
    .text
    .toPlainText(includePlaceholders: false)
    // Section lines glue times together with non-breaking spaces.
    .replaceAll('\u00A0', ' ');

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

  group('the पंचांग section (plans/panchang-section-and-pothi.md)', () {
    testWidgets('comes first, before the sun and moon times', (tester) async {
      await openFullPanchang(tester);

      final section = find.byKey(const Key('full-panchang-section'));
      expect(section, findsOneWidget);
      expect(
        tester.getRect(section).top,
        lessThan(tester.getRect(find.text('सूर्योदय').first).top),
      );
    });

    testWidgets(
      'lists the Jain tithi, nakshatra and yoga each with the next, every karana and the weekday',
      (tester) async {
        final day = delhiDay();
        final reading = delhiSection();
        final date = day.date;
        await openFullPanchang(tester);

        void expectLine(String key, String name, DateTime? until) {
          final text = lineText(tester, key);
          expect(text, contains(name));
          if (until != null) {
            expect(text, contains('${shownEnd(until, date, Lang.hi)} तक'));
          }
        }

        expectLine(
          'section-tithi-0',
          tithiName(day.jainTithi.index, Lang.hi),
          day.jainTithi.endsAt,
        );
        expectLine(
          'section-tithi-1',
          tithiName(reading.nextTithi.index, Lang.hi),
          reading.nextTithi.endsAt,
        );
        expectLine(
          'section-nakshatra-0',
          nakshatraName(day.nakshatra.index, Lang.hi),
          day.nakshatra.endsAt,
        );
        expectLine(
          'section-nakshatra-1',
          nakshatraName(reading.nextNakshatra.index, Lang.hi),
          reading.nextNakshatra.endsAt,
        );
        for (final (k, yoga) in reading.yogas.indexed) {
          expectLine(
            'section-yoga-$k',
            yogaName(yoga.index, Lang.hi),
            yoga.endsAt,
          );
        }
        for (final (k, karana) in reading.karanas.indexed) {
          expectLine(
            'section-karana-$k',
            karanaName(karana.index, Lang.hi),
            karana.endsAt,
          );
        }
        expect(line('section-karana-${reading.karanas.length}'), findsNothing);
        expect(lineText(tester, 'section-vara'), weekdayName(date, Lang.hi));
      },
    );

    testWidgets(
      'a nakshatra carries the zodiac sign of each Rashi it falls in, sized to the text',
      (tester) async {
        final day = delhiDay();
        await openFullPanchang(tester);

        final glyphs = find.descendant(
          of: line('section-nakshatra-0'),
          matching: find.byType(PanchangSymbol),
        );
        expect(
          glyphs,
          findsNWidgets(nakshatraRashis(day.nakshatra.index).length),
        );
        final fontSize = Theme.of(tester.element(glyphs.first))
            .textTheme
            .bodyLarge!
            .fontSize!;
        expect(
          tester.getSize(glyphs.first).height,
          inInclusiveRange(fontSize, fontSize * 1.3),
        );
      },
    );

    testWidgets(
      'then the month, paksha, gata and the three samvats, then the Moon and Sun Rashis',
      (tester) async {
        final day = delhiDay();
        final reading = delhiSection();
        await openFullPanchang(tester);

        expect(
          lineText(tester, 'section-month'),
          monthName(day.month, Lang.hi),
        );
        expect(
          lineText(tester, 'section-paksha'),
          pakshaName(day.jainTithi.index, Lang.hi),
        );
        expect(
          lineText(tester, 'section-gata'),
          gataText(reading.gata, Lang.hi),
        );
        expect(lineText(tester, 'section-vikram'), '${day.vikramSamvat}');
        expect(
          lineText(tester, 'section-vira-nirvana'),
          '${day.viraNirvanaSamvat}',
        );
        expect(lineText(tester, 'section-shaka'), '${day.shakaSamvat}');
        final [moon, nextMoon] = reading.moonRashis;
        expect(
          lineText(tester, 'section-moon-rashi-0'),
          '${rashiName(moon.index, Lang.hi)} ${shownEnd(moon.endsAt, day.date, Lang.hi)} तक',
        );
        expect(
          lineText(tester, 'section-moon-rashi-1'),
          rashiName(nextMoon.index, Lang.hi),
        );
        expect(
          lineText(tester, 'section-sun-rashi-0'),
          contains(rashiName(reading.sunRashis.first.index, Lang.hi)),
        );
      },
    );

    testWidgets(
      'times are slightly bold and the connective word is quieter than the name',
      (tester) async {
        await openFullPanchang(tester);

        final text = tester
            .widget<RichText>(
              find
                  .descendant(
                    of: line('section-tithi-0'),
                    matching: find.byType(RichText),
                  )
                  .first,
            )
            .text;
        final spans = <TextSpan>[];
        text.visitChildren((span) {
          if (span is TextSpan && span.text != null) spans.add(span);
          return true;
        });
        final pothi = Theme.of(tester.element(line('section-tithi-0')))
            .extension<Pothi>()!;
        final until = spans.singleWhere((s) => s.text!.trim() == 'तक');
        final time = spans.singleWhere((s) => s.text!.contains(':'));
        final name = spans.first;
        expect(until.style!.color, pothi.secondary);
        expect(name.style?.color ?? pothi.ink, pothi.ink);
        expect(time.style!.fontWeight, FontWeight.w600);
      },
    );

    testWidgets(
      'English names the Rashis with their western signs and counts the gata in days',
      (tester) async {
        final reading = delhiSection();
        await openFullPanchang(tester, phone: const Locale('en', 'US'));

        expect(
          lineText(tester, 'section-gata'),
          gataText(reading.gata, Lang.en),
        );
        expect(
          lineText(tester, 'section-gata'),
          contains('day ${reading.gata.day}'),
        );
        expect(lineText(tester, 'section-moon-rashi-0'), contains('('));
        expect(lineText(tester, 'section-tithi-0'), contains('until '));
      },
    );
  });

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
    expect(find.text('Vikram Samvat'), findsWidgets);
    expect(find.text('Vira Nirvana Samvat'), findsWidgets);
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
