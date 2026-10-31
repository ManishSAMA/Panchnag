import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/festival_reading.dart';
import 'package:jainpanchang/features/festivals/festival_state.dart';
import 'package:jainpanchang/format/festival_text.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/shared/festival_mark.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

const tapagachchha = 'shwetambar_murtipujak_tapagachchha';

/// A year straight from the engine, apart from the screen.
List<FestivalOccurrence> engineYear(int year, {String profile = tapagachchha, SunriseRule rule = SunriseRule.modern}) =>
    readFestivals(
      FestivalRequest(year: year, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata', profile: profile, rule: rule),
      registry: testRegistry,
    );

Finder cell(CivilDate date) => find.byKey(Key('month-cell-${date.iso}'));
final panel = find.byKey(const Key('month-day-panel'));
Finder inPanel(Finder finder) => find.descendant(of: panel, matching: finder);
final parvaBand = find.byKey(const Key('today-band-parva'));
final vratBand = find.byKey(const Key('today-band-vrat'));
final upcoming = find.byKey(const Key('today-upcoming'));

List<FestivalKind> marksIn(WidgetTester tester, CivilDate date) => [
  for (final mark in tester.widgetList<FestivalMark>(
    find.descendant(of: cell(date), matching: find.byType(FestivalMark)),
  ))
    mark.kind,
];

Future<void> openMonth(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  FestivalReader festivals = realFestivals,
  Size screen = const Size(1080, 2400),
}) async {
  await openApp(tester, now: now, phone: phone, festivals: festivals, screen: screen);
  await openTab(tester, phone.languageCode == 'en' ? 'Month' : 'माह');
}

Future<void> tapDay(WidgetTester tester, CivilDate date) async {
  await tester.ensureVisible(cell(date));
  await tester.tap(cell(date));
  await tester.pumpAndSettle();
}

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

final october2026 = [for (var d = const CivilDate(2026, 10, 1); d.month == 10; d = d.next()) d];

void main() {
  group('Month marks', () {
    testWidgets('each cell carries the marks of the engine\'s festivals that day', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      final year = engineYear(2026);

      for (final date in october2026) {
        expect(marksIn(tester, date), cellMarks(festivalLines(festivalsOn(year, date), Lang.hi)), reason: date.iso);
      }
    });

    testWidgets('a kalyanak day has the ring and a festival-free day has none', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      // Shri Sheetalnath Ji's liberation kalyanak, Ashwin Shukla 8 (registry).
      expect(marksIn(tester, const CivilDate(2026, 10, 18)), contains(FestivalKind.kalyanak));
      expect(engineYear(2026).where((f) => festivalsOn([f], const CivilDate(2026, 10, 22)).isNotEmpty), isEmpty);
      expect(marksIn(tester, const CivilDate(2026, 10, 22)), isEmpty);
    });

    testWidgets('every day of a span carries its mark', (tester) async {
      await openMonth(tester, now: ist(2026, 11, 5));
      final ashtahnika = engineYear(2026).singleWhere((f) => f.id == 'ashtahnika_kartika_2026');

      for (var d = ashtahnika.start; d.compareTo(ashtahnika.end) <= 0; d = d.next()) {
        expect(marksIn(tester, d), contains(FestivalKind.mahaparva), reason: d.iso);
      }
    });

    testWidgets('red marks parva and kalyanak, green marks vrat', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      const date = CivilDate(2026, 10, 20);
      final n = Theme.of(tester.element(cell(date))).extension<Navpad>()!;
      Color colourOf(FestivalKind kind) {
        final mark = find.byWidgetPredicate((w) => w is FestivalMark && w.kind == kind);
        final box = find.descendant(of: find.descendant(of: cell(date), matching: mark), matching: find.byType(DecoratedBox));
        final decoration = tester.widget<DecoratedBox>(box).decoration as BoxDecoration;
        return decoration.color ?? (decoration.border! as Border).top.color;
      }

      expect(colourOf(FestivalKind.kalyanak), n.red);
      expect(colourOf(FestivalKind.vrat), n.green);
    });

    testWidgets('the cell\'s spoken label names its marks', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      expect(tester.getSemantics(cell(const CivilDate(2026, 10, 18))).label, contains('कल्याणक'));
    });

    testWidgets('the legend explains the four marks once festivals arrive', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));

      for (final kind in FestivalKind.values) {
        expect(find.byKey(Key('legend-${kind.name}')), findsOneWidget);
      }
      expect(find.text('महापर्व'), findsWidgets);
    });

    testWidgets('the grid paints before the festival year arrives, and the marks fill in after', (tester) async {
      final held = HeldFestivals();
      await openMonth(tester, now: ist(2026, 10, 22), festivals: held.call);

      expect(cell(const CivilDate(2026, 10, 18)), findsOneWidget);
      expect(find.byType(FestivalMark), findsNothing);
      expect(find.byKey(const Key('legend-kalyanak')), findsNothing);

      held.release();
      await tester.pumpAndSettle();
      expect(marksIn(tester, const CivilDate(2026, 10, 18)), contains(FestivalKind.kalyanak));
      expect(find.byKey(const Key('legend-kalyanak')), findsOneWidget);
    });

    testWidgets('asks for the saved tradition and sunrise rule', (tester) async {
      final held = HeldFestivals();
      await openApp(
        tester,
        now: ist(2026, 10, 22),
        saved: const {
          'location.city': 'delhi',
          'settings.tradition': 'shwetambar_terapanthi',
          'settings.sunriseRule': 'traditional',
        },
        festivals: held.call,
      );
      await openTab(tester, 'माह');

      expect(held.requests, isNotEmpty);
      expect(held.requests.map((r) => (r.year, r.profile, r.rule)).toSet(), {
        (2026, 'shwetambar_terapanthi', SunriseRule.traditional),
      });
    });
  });

  group('the Month day panel', () {
    testWidgets('on a short screen the sheet lists the day\'s festivals too', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22), screen: const Size(1080, 1500));
      await tapDay(tester, const CivilDate(2026, 10, 20));

      expect(
        find.descendant(of: find.byType(BottomSheet), matching: find.text('श्री नेमिनाथ जी — केवलज्ञान कल्याणक')),
        findsOneWidget,
      );
    });

    testWidgets('lists the day\'s festivals in Hindi with their kind', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22));
      await tapDay(tester, const CivilDate(2026, 10, 20));

      // Ashadhara's Ashwin Shukla 9 variant; both school variants are kept (mobile-ui-design.md §6).
      expect(inPanel(find.text('श्री नेमिनाथ जी — केवलज्ञान कल्याणक')), findsOneWidget);
      expect(inPanel(find.text('कल्याणक')), findsOneWidget);
    });

    testWidgets('uses the English names on an English phone', (tester) async {
      await openMonth(tester, now: ist(2026, 10, 22), phone: const Locale('en', 'US'));
      await tapDay(tester, const CivilDate(2026, 10, 20));

      expect(inPanel(find.text('Shri Neminath Ji - Omniscience Kalyanak')), findsOneWidget);
    });

    testWidgets('a span shows its dates', (tester) async {
      await openMonth(tester, now: ist(2026, 11, 5));
      await tapDay(tester, const CivilDate(2026, 11, 20));

      expect(inPanel(find.text('अष्टाह्निक महापर्व')), findsOneWidget);
      expect(inPanel(find.text('17–24 नवंबर')), findsOneWidget);
    });

    testWidgets('a name the engine gives several times is listed once', (tester) async {
      await openMonth(tester, now: ist(2026, 8, 20));
      final date = const CivilDate(2026, 8, 29);
      final name = 'भाद्रपद कृष्ण एकम बहुव्रत प्रारम्भ';
      expect(festivalsOn(engineYear(2026), date).where((f) => f.nameHindi == name).length, greaterThan(1));

      await tapDay(tester, date);

      expect(inPanel(find.text(name)), findsOneWidget);
    });
  });

  group('Today\'s bands', () {
    testWidgets('red names the kalyanak and green the vrat, in that order', (tester) async {
      await openApp(tester, now: ist(2026, 10, 20));

      expect(
        find.descendant(of: parvaBand, matching: find.text('श्री नेमिनाथ जी — केवलज्ञान कल्याणक')),
        findsOneWidget,
      );
      expect(find.descendant(of: parvaBand, matching: find.text('कल्याणक')), findsOneWidget);
      expect(find.descendant(of: vratBand, matching: find.text('णमोकार महामंत्र व्रत श्रृंखला')), findsOneWidget);
      expect(tester.getTopLeft(parvaBand).dy, lessThan(tester.getTopLeft(vratBand).dy));
    });

    testWidgets('come in red, yellow, green, navy order on today', (tester) async {
      await openApp(tester, now: ist(2026, 10, 20, 7, 0));
      final yellow = find.byKey(const Key('today-band-pachchakkhan'));

      expect(tester.getTopLeft(parvaBand).dy, lessThan(tester.getTopLeft(yellow).dy));
      expect(tester.getTopLeft(yellow).dy, lessThan(tester.getTopLeft(vratBand).dy));
    });

    testWidgets('a second red festival shows as "+1 और"', (tester) async {
      // 29 Oct 2026: a kalyanak and the Rohini parva.
      await openApp(tester, now: ist(2026, 10, 29));

      expect(
        find.descendant(of: parvaBand, matching: find.text('श्री संभवनाथ जी — केवलज्ञान कल्याणक')),
        findsOneWidget,
      );
      expect(find.descendant(of: parvaBand, matching: find.text('+1 और')), findsOneWidget);
    });

    testWidgets('a single-day festival\'s name has the band\'s width, with no empty value beside it', (tester) async {
      await openApp(tester, now: ist(2026, 10, 29));
      final title = find.descendant(of: parvaBand, matching: find.text('श्री संभवनाथ जी — केवलज्ञान कल्याणक'));

      expect(tester.getSize(title).width, greaterThan(tester.getSize(parvaBand).width / 2));
    });

    testWidgets('an ongoing span shows its dates', (tester) async {
      await openApp(tester, now: ist(2026, 11, 20));

      expect(find.descendant(of: parvaBand, matching: find.text('अष्टाह्निक महापर्व')), findsOneWidget);
      expect(find.descendant(of: parvaBand, matching: find.text('17–24 नवंबर')), findsOneWidget);
    });

    testWidgets('a day without festivals has neither band', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));

      expect(parvaBand, findsNothing);
      expect(vratBand, findsNothing);
    });

    testWidgets('follow the date shown, not only today', (tester) async {
      await openApp(tester, now: ist(2026, 10, 19));
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();

      expect(
        find.descendant(of: parvaBand, matching: find.text('श्री नेमिनाथ जी — केवलज्ञान कल्याणक')),
        findsOneWidget,
      );
    });

    testWidgets('a band opens the Month tab on its day, not on today', (tester) async {
      await openApp(tester, now: ist(2026, 10, 28));
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();

      await tester.tap(parvaBand);
      await tester.pumpAndSettle();

      expect(find.text('अक्टूबर 2026'), findsOneWidget);
      expect(inPanel(find.text('गुरुवार, 29 अक्टूबर 2026')), findsOneWidget);
    });

    testWidgets('the hero paints before the festival year arrives', (tester) async {
      final held = HeldFestivals();
      await openApp(tester, now: ist(2026, 10, 20), festivals: held.call);

      expect(find.byKey(const Key('today-hero-tithi')), findsOneWidget);
      expect(parvaBand, findsNothing);
      expect(upcoming, findsNothing);

      held.release();
      await tester.pumpAndSettle();
      expect(parvaBand, findsOneWidget);
    });
  });

  group('upcoming festivals on Today', () {
    testWidgets('list the next four dates after the one shown, without vrats', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));
      final expected = upcomingFestivals(engineYear(2026), after: const CivilDate(2026, 10, 22), lang: Lang.hi);
      expect(expected, hasLength(4));

      await tester.scrollUntilVisible(upcoming, 300);
      for (final day in expected) {
        expect(find.byKey(Key('upcoming-${day.date.iso}')), findsOneWidget);
      }
      expect(find.descendant(of: upcoming, matching: find.text('णमोकार महामंत्र व्रत श्रृंखला')), findsNothing);
    });

    testWidgets('reach into next year in late December', (tester) async {
      await openApp(tester, now: ist(2026, 12, 28));
      final next = upcomingFestivals(engineYear(2027), after: const CivilDate(2026, 12, 28), lang: Lang.hi);

      await tester.scrollUntilVisible(upcoming, 300);
      expect(find.byKey(Key('upcoming-${next.first.date.iso}')), findsOneWidget);
    });

    testWidgets('dates sit in a right-aligned column', (tester) async {
      // A long name that wraps, as Diwali's does.
      await openApp(tester, now: ist(2026, 10, 29));
      final row = find.byKey(const Key('upcoming-2026-11-08'));
      await tester.scrollUntilVisible(row, 300);

      final date = find.descendant(of: row, matching: find.text('8 नवंबर'));
      expect(tester.getTopRight(row).dx - tester.getTopRight(date).dx, lessThanOrEqualTo(18));
    });

    testWidgets('a row moves Today to its date', (tester) async {
      await openApp(tester, now: ist(2026, 10, 22));
      final first = find.byKey(const Key('upcoming-2026-10-25'));

      await tester.scrollUntilVisible(first, 300);
      await tester.tap(first);
      await tester.pumpAndSettle();

      expect(find.text('रविवार, 25 अक्टूबर 2026'), findsOneWidget);
    });
  });
}
