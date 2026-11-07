import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/features/today/feature_tiles.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/shared/panchang_symbols.dart';
import 'package:jainpanchang/theme/pothi.dart';

import 'support/harness.dart';
import 'support/section_lines.dart';

final card = find.byKey(const Key('today-panchang-card'));
final fullButton = find.byKey(const Key('today-full-panchang'));

void main() {
  group("Today's Panchang card (plans/panchang-section-and-pothi.md)", () {
    testWidgets(
      'sits under the hero and above the feature tiles, under a red ruled heading',
      (tester) async {
        await openApp(tester, now: ist(2026, 10, 22));

        expect(
          tester.getTopLeft(card).dy,
          greaterThan(
            tester.getBottomLeft(find.byKey(const Key('today-hero-tithi'))).dy,
          ),
        );
        expect(
          tester.getBottomLeft(card).dy,
          lessThanOrEqualTo(tester.getTopLeft(find.byType(FeatureTiles)).dy),
        );
        final heading = find.descendant(
          of: card,
          matching: find.text('आज का पंचांग'),
        );
        expect(heading, findsOneWidget);
        final pothi = Theme.of(tester.element(card)).extension<Pothi>()!;
        expect(tester.widget<Text>(heading).style!.color, pothi.accent);
      },
    );

    testWidgets(
      'shows the Jain tithi, the nakshatra with its pada and signs, the yoga and the karana, each with its end, and the weekday',
      (tester) async {
        final day = delhiDay();
        final section = delhiSection();
        await openApp(tester, now: ist(2026, 10, 22));

        String until(DateTime utc) => '${shownEnd(utc, day.date, Lang.hi)} तक';
        expect(
          lineText(tester, 'today-panchang-tithi'),
          '${tithiName(day.jainTithi.index, Lang.hi)} ${until(day.jainTithi.endsAt)}',
        );
        expect(
          lineText(tester, 'today-panchang-nakshatra'),
          '${nakshatraName(day.nakshatra.index, Lang.hi)} (चरण ${day.nakshatra.pada}) ${until(day.nakshatra.endsAt)}',
        );
        expect(
          find.descendant(
            of: line('today-panchang-nakshatra'),
            matching: find.byType(PanchangSymbol),
          ),
          findsNWidgets(nakshatraRashis(day.nakshatra.index).length),
        );
        final yoga = section.yogas.first;
        expect(
          lineText(tester, 'today-panchang-yoga'),
          '${yogaName(yoga.index, Lang.hi)} ${until(yoga.endsAt)}',
        );
        final karana = section.karanas.first;
        expect(
          lineText(tester, 'today-panchang-karana'),
          '${karanaName(karana.index, Lang.hi)} ${until(karana.endsAt)}',
        );
        expect(
          lineText(tester, 'today-panchang-vara'),
          weekdayName(day.date, Lang.hi),
        );
      },
    );

    testWidgets('its button opens Full Panchang', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      expect(
        find.descendant(
          of: fullButton,
          matching: find.text('पूरा पंचांग देखें'),
        ),
        findsOneWidget,
      );
      // An icon, not "→": Mukta has no arrow glyph.
      expect(
        find.descendant(
          of: fullButton,
          matching: find.byIcon(Icons.arrow_forward),
        ),
        findsOneWidget,
      );
      expect(tester.getSize(fullButton).height, greaterThanOrEqualTo(48));
      await tester.ensureVisible(fullButton);
      await tester.tap(fullButton);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('full-panchang-screen')), findsOneWidget);
    });

    testWidgets('on another date the heading drops "today"', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      await tester.tap(find.widgetWithIcon(IconButton, Icons.chevron_right));
      await tester.pumpAndSettle();

      expect(
        find.descendant(of: card, matching: find.text('पंचांग')),
        findsOneWidget,
      );
      expect(find.text('आज का पंचांग'), findsNothing);
    });

    testWidgets('English readers get the card in English', (tester) async {
      await openApp(
        tester,
        now: ist(2026, 10, 22),
        phone: const Locale('en', 'US'),
      );

      expect(
        find.descendant(of: card, matching: find.text("Today's Panchang")),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: fullButton,
          matching: find.text('See full Panchang'),
        ),
        findsOneWidget,
      );
      expect(lineText(tester, 'today-panchang-tithi'), contains('until '));
    });
  });
}
