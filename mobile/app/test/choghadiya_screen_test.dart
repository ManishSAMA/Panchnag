import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/shared/navpad_icons.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

PanchangDay delhi(CivilDate date) =>
    readDay(DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'));

/// An engine instant as the screen shows it: the Delhi clock with the seconds
/// dropped, as Today shows sunrise and sunset.
String hm(DateTime utc) => clockTime(roundDownToMinute(cityWall(utc, 'Asia/Kolkata')), Lang.hi).time;

final choghadiyaTile = find.byKey(const Key('muhurat-tile-choghadiya'));
final hero = find.byKey(const Key('choghadiya-hero'));
Finder inHero(Finder finder) => find.descendant(of: hero, matching: finder);
final nowRows = find.bySemanticsLabel(RegExp(r', (अभी|now)$'));
final pastRows = find.bySemanticsLabel(RegExp(r', (बीत गया|past)$'));

Future<void> openChoghadiya(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
}) async {
  await openApp(tester, now: now, phone: phone, textScale: textScale);
  final muhurat = find.byKey(const Key('tile-muhurat'));
  await tester.ensureVisible(muhurat);
  await tester.tap(muhurat);
  await tester.pumpAndSettle();
  await tester.ensureVisible(choghadiyaTile);
  await tester.tap(choghadiyaTile);
  await tester.pumpAndSettle();
}

/// Delhi, Thursday 22 Oct 2026. Thursday's day slots run Shubh, Rog, Udveg, Char,
/// Labh, Amrit, Kaal, Shubh and its night slots Labh, Udveg, Shubh, Amrit, Char,
/// Rog, Kaal, Labh (choghadiya_service.py), so at 10:52 Char (neutral) is the
/// fourth day slot and Labh (good) comes next.
void main() {
  final oct22 = delhi(const CivilDate(2026, 10, 22));
  final char = oct22.choghadiya[3];

  testWidgets('opens from the Muhurat grid, outside the tabs, with a back arrow', (tester) async {
    await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));

    expect(hero, findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);

    await tester.tap(find.byType(BackButton));
    await tester.pumpAndSettle();
    expect(hero, findsNothing);
    expect(choghadiyaTile, findsOneWidget);
  });

  testWidgets('the hero leads with the ghatika', (tester) async {
    await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));
    expect(tester.widget<NavpadIcon>(inHero(find.byType(NavpadIcon))).glyph, NavpadGlyph.ghatika);
  });

  group('the hero', () {
    testWidgets('names the current slot, its quality and range, and counts down to its end', (tester) async {
      final now = ist(2026, 10, 22, 10, 52);
      await openChoghadiya(tester, now: now);

      expect(inHero(find.text('चर')), findsOneWidget);
      expect(inHero(find.text('– सामान्य · सुबह ${hm(char.start)}–दोपहर ${hm(char.end)} · फिर लाभ')), findsOneWidget);
      expect(inHero(find.text(countdownClock(char.end.difference(now)))), findsOneWidget);
    });

    testWidgets('shows how much of the slot has passed', (tester) async {
      final now = ist(2026, 10, 22, 10, 52);
      await openChoghadiya(tester, now: now);

      final bar = tester.widget<LinearProgressIndicator>(inHero(find.byType(LinearProgressIndicator)));
      final share = now.difference(char.start).inMicroseconds / char.end.difference(char.start).inMicroseconds;
      expect(bar.value, closeTo(share, 1e-6));
    });

    testWidgets('is a live region for screen readers', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));

      final semantics = tester.getSemantics(hero);
      expect(semantics.flagsCollection.isLiveRegion, isTrue);
      expect(semantics.label, startsWith('चर, – सामान्य · '));
    });

    testWidgets("the countdown reaches 0 at the next slot's start", (tester) async {
      await openChoghadiya(tester, now: char.end.subtract(const Duration(milliseconds: 500)));

      expect(inHero(find.text('चर')), findsOneWidget);
      expect(inHero(find.text('0:01')), findsOneWidget);
    });

    testWidgets("at the next slot's start, that slot is current with its whole length to run", (tester) async {
      final labh = oct22.choghadiya[4];
      await openChoghadiya(tester, now: char.end);

      expect(inHero(find.text('लाभ')), findsOneWidget);
      expect(inHero(find.text(countdownClock(labh.end.difference(labh.start)))), findsOneWidget);
    });

    testWidgets('is in English on an English phone', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52), phone: const Locale('en', 'US'));

      expect(find.text('Choghadiya'), findsOneWidget);
      expect(inHero(find.text('Char')), findsOneWidget);
      expect(inHero(find.text('– Neutral · ${hm(char.start)} AM–${hm(char.end)} PM · then Labh')), findsOneWidget);
    });
  });

  group('the lists', () {
    testWidgets('give 8 day and 8 night slots with their quality and times', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));

      expect(find.text('दिन'), findsOneWidget);
      expect(find.text('रात'), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^(उद्वेग|चर|लाभ|अमृत|काल|शुभ|रोग) [✓–✕] ')), findsNWidgets(16));
      expect(find.bySemanticsLabel(RegExp('^चर – सामान्य सुबह ${hm(char.start)}–दोपहर ${hm(char.end)}')), findsOne);
      expect(find.bySemanticsLabel(RegExp(r'^लाभ ✓ अच्छा ')), findsNWidgets(3));
    });

    testWidgets('colour the ✓ of a good slot green and the ✕ of a bad one red, until it is past', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));
      final n = Theme.of(tester.element(find.byType(Scaffold).last)).extension<Navpad>()!;

      for (final (glyph, colour) in [('✓', n.markGood), ('✕', n.markAvoid)]) {
        final colours = [for (final e in find.text(glyph).evaluate()) (e.widget as Text).style?.color];
        expect(colours, contains(colour), reason: glyph);
        expect(colours.toSet().difference({colour, n.ink3}), isEmpty, reason: '$glyph: only its colour, or muted when past');
      }
    });

    testWidgets('fill the current row light green, as every window running now is', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));
      final n = Theme.of(tester.element(find.byType(Scaffold).last)).extension<Navpad>()!;
      final current = find.descendant(of: nowRows, matching: find.byType(Container)).first;

      expect((tester.widget<Container>(current).decoration! as BoxDecoration).color, n.nowFill);
    });

    testWidgets('mark the current row and mute the past ones', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));

      expect(nowRows, findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^चर .*, अभी$')), findsOneWidget);
      expect(pastRows, findsNWidgets(3));
    });

    for (final (label, now) in [
      ('at sunrise', oct22.sunrise),
      ('on a slot boundary', char.end),
      ('just before sunset', oct22.sunset.subtract(const Duration(seconds: 1))),
      ('at sunset', oct22.sunset),
      ('late at night', ist(2026, 10, 22, 23, 30)),
      ('after midnight, before the next sunrise', ist(2026, 10, 23, 5, 0)),
    ]) {
      testWidgets('exactly one row is current $label', (tester) async {
        await openChoghadiya(tester, now: now);

        expect(nowRows, findsOneWidget);
        expect(hero, findsOneWidget);
      });
    }

    testWidgets('on another day nothing is current, nothing is past and there is no countdown', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();

      expect(hero, findsNothing);
      expect(nowRows, findsNothing);
      expect(pastRows, findsNothing);
      expect(find.bySemanticsLabel(RegExp(r'^(उद्वेग|चर|लाभ|अमृत|काल|शुभ|रोग) [✓–✕] ')), findsNWidgets(16));
    });

    testWidgets("the date is Today's: moving it here moves Today", (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();
      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();

      expect(find.text('शुक्रवार, 23 अक्टूबर 2026'), findsOneWidget);
    });

    testWidgets("before sunrise, the list is yesterday's and a note says so", (tester) async {
      final now = ist(2026, 10, 22, 5, 0);
      await openChoghadiya(tester, now: now);

      expect(find.text('सूर्योदय से पहले'), findsOneWidget);
      expect(find.textContaining('सुबह ${hm(oct22.sunrise)} के सूर्योदय तक'), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r'^उद्वेग .*, अभी$')), findsOneWidget);
      expect(find.text('गुरुवार, 22 अक्टूबर 2026'), findsOneWidget);
    });

    testWidgets('a footnote explains how the slots are made', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));

      expect(find.textContaining('आठ बराबर भागों'), findsOneWidget);
    });
  });

  for (final scale in [1.3, 1.6, 2.0]) {
    testWidgets('nothing overflows on the Choghadiya screen at ${scale}x text', (tester) async {
      await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52), textScale: scale);

      expect(tester.takeException(), isNull);
      expect(hero, findsOneWidget);
    });
  }

  testWidgets('every Choghadiya control is at least 48 dp', (tester) async {
    await openChoghadiya(tester, now: ist(2026, 10, 22, 10, 52));

    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  });
}
