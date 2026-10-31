import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/shared/moon_phase.dart';
import 'package:jainpanchang/shared/navpad_icons.dart';
import 'package:jainpanchang/shared/navpad_widgets.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

Future<void> openMonth(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
  Size screen = const Size(1080, 2400),
}) async {
  await openApp(tester, now: now, phone: phone, textScale: textScale, screen: screen);
  await tester.tap(
    find.descendant(of: find.byType(NavigationBar), matching: find.text(phone.languageCode == 'en' ? 'Month' : 'माह')),
  );
  await tester.pumpAndSettle();
}

Finder cell(CivilDate date) => find.byKey(Key('month-cell-${date.iso}'));
Finder inCell(CivilDate date, Finder finder) => find.descendant(of: cell(date), matching: finder);
final panel = find.byKey(const Key('month-day-panel'));
Finder inPanel(Finder finder) => find.descendant(of: panel, matching: finder);

Future<void> tapDay(WidgetTester tester, CivilDate date) async {
  await tester.ensureVisible(cell(date));
  await tester.tap(cell(date));
  await tester.pumpAndSettle();
}

/// The Jain tithi of each day from the day before [first] to the day after
/// [last], read one day at a time, apart from the screen.
Map<CivilDate, int> jainTithis(CivilDate first, CivilDate last) {
  final before = DateTime.utc(first.year, first.month, first.day - 1);
  return {
    for (var d = CivilDate(before.year, before.month, before.day); d.compareTo(last.next()) <= 0; d = d.next())
      d: const PanchangEngine().day(location: delhiCity, date: d).jainTithi.index,
  };
}

CivilDate previousDay(CivilDate d) {
  final p = DateTime.utc(d.year, d.month, d.day - 1);
  return CivilDate(p.year, p.month, p.day);
}

final october2026 = [for (var d = const CivilDate(2026, 10, 1); d.month == 10; d = d.next()) d];

void main() {
  group('the header', () {
    testWidgets('opens on the city\'s current month, with the lunar months it spans and VS', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      expect(find.text('अक्टूबर 2026'), findsOneWidget);
      expect(find.text('आश्विन – कार्तिक · वि. सं. 2083'), findsOneWidget);
    });

    testWidgets('the arrows move a month at a time', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      await tester.tap(nav('अगला माह'));
      await tester.pumpAndSettle();
      expect(find.text('नवंबर 2026'), findsOneWidget);

      await tester.tap(nav('पिछला माह'));
      await tester.tap(nav('पिछला माह'));
      await tester.pumpAndSettle();
      expect(find.text('सितंबर 2026'), findsOneWidget);
    });

    testWidgets('away from the current month, "आज" brings it back', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      expect(find.widgetWithText(OutlinedButton, 'आज'), findsNothing);

      await tester.tap(nav('अगला माह'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(OutlinedButton, 'आज'));
      await tester.pumpAndSettle();

      expect(find.text('अक्टूबर 2026'), findsOneWidget);
      expect(inPanel(find.text('गुरुवार, 22 अक्टूबर 2026')), findsOneWidget);
    });

    testWidgets('stops at December 2040', (tester) async {
      await openMonth(tester, now: ist(2040, 12, 31));

      expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.chevron_right).first).onPressed, isNull);
      expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.chevron_left).first).onPressed, isNotNull);
    });

    testWidgets('stops at January 2016', (tester) async {
      await openMonth(tester, now: ist(2016, 1, 1));

      expect(tester.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.chevron_left).first).onPressed, isNull);
    });
  });

  group('the grid (Delhi, October 2026)', () {
    testWidgets('starts its weeks on Sunday, so 1 Oct 2026 sits under Thursday', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      final weekdays = ['रवि', 'सोम', 'मंगल', 'बुध', 'गुरु', 'शुक्र', 'शनि'];
      final xs = [for (final w in weekdays) tester.getCenter(find.text(w)).dx];
      expect(xs, orderedEquals([...xs]..sort()));
      expect(tester.getCenter(cell(const CivilDate(2026, 10, 1))).dx, moreOrLessEquals(xs[4], epsilon: 1));
      expect(tester.getCenter(cell(const CivilDate(2026, 10, 4))).dx, moreOrLessEquals(xs[0], epsilon: 1));
    });

    testWidgets('each day shows its number and its Jain tithi', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      final tithis = jainTithis(october2026.first, october2026.last);

      expect(inCell(const CivilDate(2026, 10, 22), find.text('शु 11')), findsOneWidget);
      for (final d in october2026) {
        expect(inCell(d, find.text('${d.day}')), findsOneWidget, reason: '$d');
        expect(inCell(d, find.text(tithiShort(tithis[d]!, Lang.hi))), findsOneWidget, reason: '$d');
      }
    });

    testWidgets('each day draws the moon of its tithi at 11 dp, before the short tithi', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      final tithis = jainTithis(october2026.first, october2026.last);

      for (final d in october2026) {
        final moon = inCell(d, find.byType(MoonPhase));
        expect(tester.widget<MoonPhase>(moon).tithi, tithis[d], reason: '$d');
        expect(tester.getSize(moon), const Size.square(11));
        final short = inCell(d, find.text(tithiShort(tithis[d]!, Lang.hi)));
        expect(tester.getCenter(moon).dx, lessThan(tester.getTopLeft(short).dx), reason: '$d');
      }
    });

    testWidgets('a long short tithi stays on one line beside its moon', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      final amavas = inCell(const CivilDate(2026, 10, 10), find.text('अमावस'));

      expect(tester.getRect(amavas).height, lessThan(20));
      expect(tester.getRect(cell(const CivilDate(2026, 10, 10))).contains(tester.getRect(amavas).centerRight), isTrue);
    });

    testWidgets('flags क्ष exactly where the Jain tithi skips one, and वृ on both days of a repeat', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      final tithis = jainTithis(october2026.first, october2026.last);
      int after(int tithi) => tithi % 30 + 1;
      bool skips(CivilDate d) => tithis[d] == after(after(tithis[previousDay(d)]!));
      bool repeats(CivilDate d) => tithis[d] == tithis[previousDay(d)] || tithis[d] == tithis[d.next()];

      // The UI spec's test month: kshaya on the 3rd and 27th, vriddhi on the 18th-19th.
      expect(
        [
          for (final d in october2026)
            if (skips(d)) d.day,
        ],
        [3, 27],
      );
      expect(
        [
          for (final d in october2026)
            if (repeats(d)) d.day,
        ],
        [18, 19],
      );
      for (final d in october2026) {
        expect(inCell(d, find.text('क्ष')), skips(d) ? findsOneWidget : findsNothing, reason: '$d');
        expect(inCell(d, find.text('वृ')), repeats(d) ? findsOneWidget : findsNothing, reason: '$d');
      }
    });

    testWidgets('a legend under the grid explains the flags', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      expect(find.text('क्षय तिथि'), findsOneWidget);
      expect(find.text('वृद्धि तिथि'), findsOneWidget);
    });

    testWidgets('is in English on an English phone', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22), phone: const Locale('en', 'US'));

      expect(find.text('October 2026'), findsOneWidget);
      expect(find.text('Sun'), findsOneWidget);
      expect(inCell(const CivilDate(2026, 10, 22), find.text('S 11')), findsOneWidget);
    });
  });

  group('the day panel, docked under the grid', () {
    testWidgets('shows today until another day is tapped', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      expect(inPanel(find.text('गुरुवार, 22 अक्टूबर 2026')), findsOneWidget);
      expect(inPanel(find.text('शुक्ल एकादशी')), findsOneWidget);
      expect(inPanel(find.text('सूर्योदय')), findsOneWidget);
      expect(inPanel(find.text('सूर्यास्त')), findsOneWidget);
    });

    testWidgets('leads the tithi row with its moon and the sun rows with sunrise and sunset', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      Finder row(String name) => inPanel(find.ancestor(of: find.text(name), matching: find.byType(TimeRow)));

      final moon = find.descendant(of: row('शुक्ल एकादशी'), matching: find.byType(MoonPhase));
      expect(tester.widget<MoonPhase>(moon).tithi, 11);
      expect(tester.getSize(moon), const Size.square(24));
      for (final (name, glyph) in [('सूर्योदय', NavpadGlyph.sunrise), ('सूर्यास्त', NavpadGlyph.sunset)]) {
        final icon = find.descendant(of: row(name), matching: find.byType(NavpadIcon));
        expect(tester.widget<NavpadIcon>(icon).glyph, glyph);
      }
    });

    testWidgets('on a month without today, shows its first day', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      await tester.tap(nav('अगला माह'));
      await tester.pumpAndSettle();

      expect(inPanel(find.text('रविवार, 1 नवंबर 2026')), findsOneWidget);
    });

    testWidgets('explains a vriddhi with the rule that matches each of its days', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      await tapDay(tester, const CivilDate(2026, 10, 18));
      expect(inPanel(find.text('वृद्धि तिथि · पहला दिन')), findsOneWidget);

      await tapDay(tester, const CivilDate(2026, 10, 19));
      expect(inPanel(find.text('वृद्धि तिथि · दूसरा दिन')), findsOneWidget);
      expect(inPanel(find.text('वृद्धि तिथि · पहला दिन')), findsNothing);
    });

    testWidgets('explains a kshaya', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      await tapDay(tester, const CivilDate(2026, 10, 27));

      expect(inPanel(find.text('क्षय तिथि')), findsOneWidget);
    });

    testWidgets('choosing a day leaves Today on today', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      await tapDay(tester, const CivilDate(2026, 10, 19));
      await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text('आज')));
      await tester.pumpAndSettle();

      expect(find.text('गुरुवार, 22 अक्टूबर 2026'), findsOneWidget);
    });

    testWidgets('"पूरा दिन खोलें" opens Today at that day', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      await tapDay(tester, const CivilDate(2026, 10, 18));
      await tester.ensureVisible(find.text('पूरा दिन खोलें'));
      await tester.tap(find.text('पूरा दिन खोलें'));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('today-hero-tithi')), findsOneWidget);
      expect(find.text('रविवार, 18 अक्टूबर 2026'), findsOneWidget);
    });

    testWidgets('lays out at 1.3× text with nothing overflowing', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22), textScale: 1.3);

      expect(cell(const CivilDate(2026, 10, 31)), findsOneWidget);
      expect(panel, findsOneWidget);
    });
  });

  group('on a short screen (under 640 dp)', () {
    const short = Size(1080, 1600); // 582 dp at 2.75

    testWidgets('the day opens in a modal sheet instead of a docked panel', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22), screen: short);
      expect(panel, findsNothing);

      await tapDay(tester, const CivilDate(2026, 10, 18));

      expect(find.descendant(of: find.byType(BottomSheet), matching: panel), findsOneWidget);
      expect(inPanel(find.text('वृद्धि तिथि · पहला दिन')), findsOneWidget);
    });
  });
}
