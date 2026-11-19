import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/format/muhurat_text.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/shared/navpad_icons.dart';
import 'package:jainpanchang/shared/navpad_widgets.dart';
import 'package:jainpanchang/theme/navpad.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

DayRequest delhiOn(CivilDate date) => DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');
PanchangMuhurat muhuratOn(CivilDate date) => readMuhurat(MuhuratRequest(delhiOn(date)));
PanchangSection sectionOn(CivilDate date) => readSection(SectionRequest(delhiOn(date)));

DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, 'Asia/Kolkata'));
String range(DateTime start, DateTime end, [Lang lang = Lang.hi]) => glued(clockRange(wall(start), wall(end), lang));
/// A day's window as a tile or row reads it: the start as read on [day],
/// the end with its date when it falls on a later one.
String ending(DateTime start, DateTime end, CivilDate day) {
  final (from, to) = (wall(start), wall(end));
  if (CivilDate(to.year, to.month, to.day) == day) return range(start, end);
  return '${glued(instantPhrase(from, day: day, lang: Lang.hi))} – ${glued(instantPhrase(to, day: day, lang: Lang.hi))}';
}
String span((String, String) ends) => '${glued(ends.$1)} – ${glued(ends.$2)}';

Color? inkOf(WidgetTester tester, Finder text) => tester.widget<Text>(text).style?.color;
Navpad navpadOf(WidgetTester tester) => Theme.of(tester.element(find.byType(Scaffold).last)).extension<Navpad>()!;

/// The nearest fill behind [text]: a row's decoration or a tile's paper.
Color? fillOf(WidgetTester tester, Finder text) {
  Color? fill;
  tester.element(text).visitAncestorElements((element) {
    fill = switch (element.widget) {
      Container(decoration: BoxDecoration(color: final colour?)) => colour,
      Material(color: final colour?) => colour,
      _ => null,
    };
    return fill == null;
  });
  return fill;
}

Finder tile(String kind) => find.byKey(Key('muhurat-tile-$kind'));
Finder onTile(String kind, String text) => find.descendant(of: tile(kind), matching: find.text(text));

/// Every yoga name in the exported rules (shared/yoga_rules.json).
Iterable<String> yogaRuleNames() sync* {
  Iterable<String> walk(Object? node) sync* {
    switch (node) {
      case {'name': final String name}:
        yield name;
        for (final value in (node as Map).values) {
          yield* walk(value);
        }
      case final Map<String, Object?> map:
        for (final value in map.values) {
          yield* walk(value);
        }
      case final List<Object?> list:
        for (final value in list) {
          yield* walk(value);
        }
    }
  }

  yield* walk(jsonDecode(File('../../shared/yoga_rules.json').readAsStringSync())).toSet();
}

const kinds = ['rahu-kaal', 'abhijit', 'choghadiya', 'yoga', 'panchak', 'bhadra', 'gandmool', 'chandra-bal', 'agni-vaas'];

Future<void> openMuhurat(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  double textScale = 1,
}) async {
  await openApp(tester, now: now, phone: phone, textScale: textScale);
  final todayTile = find.byKey(const Key('tile-muhurat'));
  await tester.ensureVisible(todayTile);
  await tester.tap(todayTile);
  await tester.pumpAndSettle();
}

Future<void> openDetail(WidgetTester tester, String kind) async {
  await tester.ensureVisible(tile(kind));
  await tester.tap(tile(kind));
  await tester.pumpAndSettle();
}

/// Delhi. 7 Nov 2026 (Saturday): no Panchak or Gandmool, Bhadra in Patal
/// across a Moon Rashi change, Agni in Prithvi. 17 Nov: Panchak, and a Bhadra
/// on Earth. 3 Nov: Gandmool in Magha. (Read from the engine, which matches
/// muhurat_day.py through the parity fixtures.)
void main() {
  const nov7 = CivilDate(2026, 11, 7);
  const nov17 = CivilDate(2026, 11, 17);
  const nov3 = CivilDate(2026, 11, 3);

  group('a window running now', () {
    testWidgets('fills its detail row light green; the others stay on the page', (tester) async {
      final m = muhuratOn(nov7);
      await openMuhurat(tester, now: m.gulika.start.add(const Duration(minutes: 5)));
      await openDetail(tester, 'rahu-kaal');
      final n = navpadOf(tester);

      expect(fillOf(tester, find.text(range(m.gulika.start, m.gulika.end))), n.nowFill);
      expect(fillOf(tester, find.text(range(m.rahuKaal.start, m.rahuKaal.end))), n.ground);
      expect(fillOf(tester, find.text(range(m.yamaganda.start, m.yamaganda.end))), n.ground);
    });

    testWidgets('fills its tile light green and says अभी', (tester) async {
      final m = muhuratOn(nov7);
      await openMuhurat(tester, now: m.rahuKaal.start.add(const Duration(minutes: 5)));
      final n = navpadOf(tester);

      expect(fillOf(tester, onTile('rahu-kaal', '✕ टालें')), n.nowFill);
      expect(onTile('rahu-kaal', 'अभी'), findsOneWidget);
      expect(fillOf(tester, onTile('abhijit', '✓ अच्छा')), n.surface);
      expect(onTile('abhijit', 'अभी'), findsNothing);
    });

    testWidgets('a Bhadra window running now is light green', (tester) async {
      final m = muhuratOn(nov17);
      final w = m.bhadra.first;
      await openMuhurat(tester, now: w.start.add(const Duration(minutes: 5)));
      await openDetail(tester, 'bhadra');

      expect(fillOf(tester, find.text(ending(w.start, w.end, nov17))), navpadOf(tester).nowFill);
      expect(find.bySemanticsLabel(RegExp(r', अभी$')), findsOneWidget);
    });

    testWidgets('a Gandmool window running now is light green', (tester) async {
      final m = muhuratOn(nov3);
      final w = m.gandmool.first;
      await openMuhurat(tester, now: w.start.add(const Duration(minutes: 5)));
      await openDetail(tester, 'gandmool');

      expect(fillOf(tester, find.text(nakshatraName(w.nakshatra, Lang.hi))), navpadOf(tester).nowFill);
    });

    testWidgets('a day yoga running now is light green', (tester) async {
      final m = muhuratOn(nov7);
      final y = m.yogas.first;
      await openMuhurat(tester, now: y.start.add(const Duration(minutes: 1)));
      await openDetail(tester, 'yoga');
      final name = find.text(dayYogaName(y.name, Lang.hi)).first;
      await tester.ensureVisible(name);

      expect(fillOf(tester, name), navpadOf(tester).nowFill);
    });
  });

  group('the marks', () {
    testWidgets('on the tiles, ✕ is red, ✓ is green and – stays quiet', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 7, 10, 52));
      final n = navpadOf(tester);

      expect(inkOf(tester, onTile('rahu-kaal', '✕ टालें')), n.markAvoid);
      expect(inkOf(tester, onTile('abhijit', '✓ अच्छा')), n.markGood);
      expect(inkOf(tester, onTile('panchak', '–')), n.ink2);
    });

    testWidgets('on the detail screens, each mark has its own colour', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 17));
      await openDetail(tester, 'bhadra');
      final n = navpadOf(tester);

      expect(inkOf(tester, find.text('✕ टालें')), n.markAvoid, reason: 'Bhadra on Earth');
      expect(inkOf(tester, find.text('–')), n.ink2, reason: 'Bhadra in Patal');
    });

    testWidgets('Rahu Kaal, Yamaganda and Gulika each carry a red ✕', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'rahu-kaal');
      final n = navpadOf(tester);

      final crosses = find.text('✕ टालें');
      expect(crosses, findsNWidgets(3));
      for (final cross in crosses.evaluate()) {
        expect((cross.widget as Text).style?.color, n.markAvoid);
      }
    });

    testWidgets('a havan-friendly Agni Vaas carries a green ✓', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'agni-vaas');

      expect(inkOf(tester, find.text('✓ अच्छा')), navpadOf(tester).markGood);
    });
  });

  group('the Muhurat grid', () {
    testWidgets("opens from Today's मुहूर्त tile, which took the Choghadiya tile's place", (tester) async {
      await openApp(tester, now: ist(2026, 11, 7));
      expect(find.byKey(const Key('tile-choghadiya')), findsNothing);
      final glyph = tester
          .widget<NavpadIcon>(find.descendant(of: find.byKey(const Key('tile-muhurat')), matching: find.byType(NavpadIcon)))
          .glyph;
      expect(glyph, NavpadGlyph.abhijit);

      await openMuhurat(tester, now: ist(2026, 11, 7));
      expect(find.widgetWithText(AppBar, 'मुहूर्त'), findsOneWidget);
      for (final kind in kinds) {
        expect(tile(kind), findsOneWidget, reason: kind);
      }
    });

    testWidgets('sets its nine tiles two to a row, in reading order', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 7));
      for (var i = 0; i + 1 < kinds.length; i += 2) {
        final (left, right) = (tester.getRect(tile(kinds[i])), tester.getRect(tile(kinds[i + 1])));
        expect(left.top, right.top, reason: '${kinds[i]} beside ${kinds[i + 1]}');
        expect(left.left, lessThan(right.left));
      }
      expect(tester.getRect(tile('agni-vaas')).left, tester.getRect(tile('rahu-kaal')).left);
      expect(tester.getRect(tile('agni-vaas')).top, greaterThan(tester.getRect(tile('chandra-bal')).top));
    });

    testWidgets("each tile's face shows the engine's reading for the day and a mark", (tester) async {
      final m = muhuratOn(nov7);
      final section = sectionOn(nov7);
      await openMuhurat(tester, now: ist(2026, 11, 7, 10, 52));

      expect(onTile('rahu-kaal', range(m.rahuKaal.start, m.rahuKaal.end)), findsOneWidget);
      expect(onTile('rahu-kaal', '✕ टालें'), findsOneWidget);
      expect(onTile('abhijit', range(m.abhijit.start, m.abhijit.end)), findsOneWidget);
      expect(onTile('abhijit', '✓ अच्छा'), findsOneWidget);
      expect(onTile('yoga', yogaName(section.yogas.first.index, Lang.hi)), findsOneWidget);
      expect(onTile('panchak', 'आज नहीं'), findsOneWidget);
      expect(onTile('panchak', '–'), findsOneWidget);
      expect(onTile('bhadra', range(m.bhadra.first.start, m.bhadra.last.end)), findsOneWidget);
      expect(onTile('bhadra', '–'), findsOneWidget, reason: 'Bhadra in Patal does not harm the earth');
      expect(onTile('gandmool', 'आज नहीं'), findsOneWidget);
      expect(onTile('chandra-bal', 'चंद्र: ${rashiName(m.chandraBal.first.moonRashi, Lang.hi)}'), findsOneWidget);
      expect(onTile('chandra-bal', '6 राशियाँ'), findsOneWidget);
      expect(onTile('agni-vaas', 'पृथ्वी'), findsOneWidget);
      expect(onTile('agni-vaas', '✓ अच्छा'), findsOneWidget);
    });

    testWidgets('the Choghadiya tile shows the slot running now and its end, and opens Choghadiya', (tester) async {
      final now = ist(2026, 11, 7, 10, 52);
      final day = readDay(delhiOn(nov7));
      final slot = day.choghadiya.firstWhere((s) => !now.isBefore(s.start) && now.isBefore(s.end));
      await openMuhurat(tester, now: now);

      final face = '${choghadiyaName(slot.name, Lang.hi)} · ${glued('${clockPhrase(wall(slot.end), Lang.hi)} तक')}';
      expect(onTile('choghadiya', face), findsOneWidget);
      expect(onTile('choghadiya', '${natureGlyph(slot.name.nature)} ${switch (slot.name.nature) {
        ChoghadiyaNature.auspicious => 'अच्छा',
        ChoghadiyaNature.neutral => 'सामान्य',
        ChoghadiyaNature.inauspicious => 'टालें',
      }}'), findsOneWidget);

      await openDetail(tester, 'choghadiya');
      expect(find.byKey(const Key('choghadiya-hero')), findsOneWidget);
    });

    testWidgets('marks a Panchak day and an earthly Bhadra to avoid', (tester) async {
      final m = muhuratOn(nov17);
      await openMuhurat(tester, now: ist(2026, 11, 17));

      // Panchak begins in the afternoon and runs past midnight to the next sunrise.
      expect(onTile('panchak', ending(m.panchak.window!.start, m.panchak.window!.end, nov17)), findsOneWidget);
      expect(onTile('panchak', '✕ टालें'), findsOneWidget);
      expect(onTile('bhadra', '✕ टालें'), findsOneWidget);
    });

    testWidgets('a Panchak from sunrise to the next sunrise reads पूरे दिन, on the tile and its screen', (tester) async {
      // 19 Nov 2026: the Moon stays in Panchak (17 Nov 3:30 PM – 22 Nov) all day.
      const nov19 = CivilDate(2026, 11, 19);
      final day = readDay(delhiOn(nov19));
      final w = muhuratOn(nov19).panchak.window!;
      expect((w.start, w.end), (day.sunrise, day.choghadiya.last.end));
      await openMuhurat(tester, now: ist(2026, 11, 19));

      expect(onTile('panchak', 'पूरे दिन'), findsOneWidget);
      await openDetail(tester, 'panchak');
      expect(find.text('पूरे दिन'), findsOneWidget);
    });

    testWidgets('is in English on an English phone', (tester) async {
      final m = muhuratOn(nov7);
      await openMuhurat(tester, now: ist(2026, 11, 7), phone: const Locale('en', 'US'));

      expect(find.widgetWithText(AppBar, 'Muhurat'), findsOneWidget);
      expect(onTile('rahu-kaal', 'Rahu Kaal'), findsOneWidget);
      expect(onTile('rahu-kaal', range(m.rahuKaal.start, m.rahuKaal.end, Lang.en)), findsOneWidget);
      expect(onTile('rahu-kaal', '✕ Avoid'), findsOneWidget);
      expect(onTile('panchak', 'None today'), findsOneWidget);
      expect(onTile('chandra-bal', 'Moon: ${rashiName(m.chandraBal.first.moonRashi, Lang.en)}'), findsOneWidget);
      expect(onTile('chandra-bal', '6 Rashis'), findsOneWidget);
      expect(onTile('agni-vaas', 'Earth'), findsOneWidget);
    });

    testWidgets('follows the date navigator', (tester) async {
      final m = muhuratOn(const CivilDate(2026, 11, 8));
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await tester.tap(find.byTooltip('अगला दिन'));
      await tester.pumpAndSettle();

      expect(onTile('rahu-kaal', range(m.rahuKaal.start, m.rahuKaal.end)), findsOneWidget);
    });

    for (final scale in [1.3, 1.6, 2.0]) {
      testWidgets('nothing overflows at ${scale}x text', (tester) async {
        await openMuhurat(tester, now: ist(2026, 11, 17), textScale: scale);
        expect(tester.takeException(), isNull);
        for (final kind in kinds) {
          await openDetail(tester, kind);
          expect(tester.takeException(), isNull, reason: kind);
          await tester.tap(find.byType(BackButton));
          await tester.pumpAndSettle();
        }
      });
    }

    testWidgets('every tile is at least 48 dp and named with its face', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
      await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
      expect(find.bySemanticsLabel(RegExp(r'^पंचक, आज नहीं')), findsOneWidget);
    });
  });

  group('the detail screens', () {
    testWidgets('Rahu Kaal lists Rahu Kaal, Yamaganda and Gulika, and marks the one running now', (tester) async {
      final m = muhuratOn(nov7);
      // Saturday: Gulika is the 1st eighth, Rahu Kaal the 3rd, Yamaganda the
      // 6th, so the two still to come must not read "अभी".
      final now = m.gulika.start.add(const Duration(minutes: 5));
      await openMuhurat(tester, now: now);
      await openDetail(tester, 'rahu-kaal');

      for (final (name, w) in [('राहु काल', m.rahuKaal), ('यमगंड', m.yamaganda), ('गुलिक', m.gulika)]) {
        final row = find.ancestor(of: find.text(range(w.start, w.end)), matching: find.byType(TimeRow));
        expect(find.descendant(of: row, matching: find.text(name)), findsOneWidget, reason: name);
      }
      expect(find.bySemanticsLabel(RegExp(r'^गुलिक .*, अभी$')), findsOneWidget);
      expect(find.bySemanticsLabel(RegExp(r', अभी$')), findsOneWidget);
    });

    testWidgets("Abhijit shows the 8th muhurta of the daylight", (tester) async {
      final m = muhuratOn(nov7);
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'abhijit');

      expect(find.text(range(m.abhijit.start, m.abhijit.end)), findsOneWidget);
    });

    testWidgets("Panchak shows today's part and the whole period", (tester) async {
      final m = muhuratOn(nov17);
      final (from, to) = spanPhrases(wall(m.panchak.period!.start), wall(m.panchak.period!.end), day: nov17, lang: Lang.hi);
      await openMuhurat(tester, now: ist(2026, 11, 17));
      await openDetail(tester, 'panchak');

      expect(find.text(ending(m.panchak.window!.start, m.panchak.window!.end, nov17)), findsOneWidget);
      expect(find.text(span((from, to))), findsOneWidget);
    });

    testWidgets('Panchak shows the next period on a day without it', (tester) async {
      final m = muhuratOn(nov7);
      final (from, to) = spanPhrases(wall(m.panchak.nextPeriod!.start), wall(m.panchak.nextPeriod!.end), day: nov7, lang: Lang.hi);
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'panchak');

      expect(find.text('आज नहीं'), findsOneWidget);
      expect(find.text(span((from, to))), findsOneWidget);
    });

    testWidgets('Bhadra lists each window with its residence', (tester) async {
      final m = muhuratOn(nov17);
      await openMuhurat(tester, now: ist(2026, 11, 17));
      await openDetail(tester, 'bhadra');

      for (final w in m.bhadra) {
        expect(find.text(ending(w.start, w.end, nov17)), findsOneWidget);
      }
      expect(find.text('पृथ्वी पर'), findsOneWidget);
      expect(find.text('पाताल में'), findsOneWidget);
      expect(find.text('✕ टालें'), findsOneWidget);
      expect(find.text('–'), findsOneWidget);
    });

    testWidgets('Gandmool names the nakshatra of each window', (tester) async {
      final m = muhuratOn(nov3);
      await openMuhurat(tester, now: ist(2026, 11, 3));
      await openDetail(tester, 'gandmool');

      for (final w in m.gandmool) {
        expect(find.text(nakshatraName(w.nakshatra, Lang.hi)), findsOneWidget);
      }
    });

    testWidgets('a Gandmool day is marked to avoid on its tile', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 3));
      expect(onTile('gandmool', '✕ टालें'), findsOneWidget);
    });

    testWidgets('Chandra Bal lists the six Rashis for each Moon Rashi of the day', (tester) async {
      final m = muhuratOn(nov7);
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'chandra-bal');

      expect(m.chandraBal, hasLength(2));
      for (final span in m.chandraBal) {
        expect(find.text('चंद्र ${rashiName(span.moonRashi, Lang.hi)}'), findsOneWidget);
        expect(find.text(span.rashis.map((r) => rashiName(r, Lang.hi)).join(', ')), findsOneWidget);
      }
    });

    testWidgets('Agni Vaas names the residence and whether a havan suits it', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 9));
      await openDetail(tester, 'agni-vaas');

      expect(find.text('आकाश'), findsOneWidget);
      expect(find.text('✕ टालें'), findsOneWidget);
    });

    testWidgets('Agni in Prithvi suits a havan, on the screen and on the tile', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'agni-vaas');
      expect(find.text('पृथ्वी'), findsOneWidget);
      expect(find.text('✓ अच्छा'), findsOneWidget);
    });

    testWidgets('Agni in Aakash is marked to avoid on its tile', (tester) async {
      await openMuhurat(tester, now: ist(2026, 11, 9));
      expect(onTile('agni-vaas', '✕ टालें'), findsOneWidget);
    });

    testWidgets('Yoga shows the nitya yoga first, then the good and the bad yogas of the day', (tester) async {
      final m = muhuratOn(nov7);
      final section = sectionOn(nov7);
      await openMuhurat(tester, now: ist(2026, 11, 7));
      await openDetail(tester, 'yoga');

      final nitya = find.text(yogaName(section.yogas.first.index, Lang.hi));
      expect(nitya, findsOneWidget);
      expect(find.text('नित्य योग'), findsOneWidget);
      final good = find.text('शुभ योग'), bad = find.text('अशुभ योग');
      expect(tester.getTopLeft(nitya).dy, lessThan(tester.getTopLeft(good).dy));
      expect(tester.getTopLeft(good).dy, lessThan(tester.getTopLeft(bad).dy));
      for (final y in m.yogas) {
        expect(find.text(dayYogaName(y.name, Lang.hi)), findsWidgets, reason: y.name);
      }
      expect(find.text('सर्वार्थ सिद्धि'), findsOneWidget);
    });
  });

  test('a time phrase keeps its words on one line', () {
    expect(glued('8 नवंबर, सुबह 5:52 तक'), '8 नवंबर, सुबह 5:52 तक');
  });

  group('the nitya yogas', () {
    // The nine inauspicious ones of the 27, as the user confirmed on
    // 2026-11-18: Vishkambha 1, Atiganda 6, Shula 9,
    // Ganda 10, Vyaghata 13, Vajra 15, Vyatipata 17, Parigha 19, Vaidhriti 27.
    const bad = {1, 6, 9, 10, 13, 15, 17, 19, 27};

    test('are good except the nine', () {
      for (var i = 1; i <= 27; i++) {
        expect(nityaYogaIsAuspicious(i), !bad.contains(i), reason: '$i');
      }
    });

    testWidgets('a bad nitya yoga is marked to avoid on the Yoga tile', (tester) async {
      final date = [
        for (var d = 1; d <= 30; d++) CivilDate(2026, 11, d),
      ].firstWhere((date) => bad.contains(sectionOn(date).yogas.first.index));
      await openMuhurat(tester, now: ist(date.year, date.month, date.day));
      expect(onTile('yoga', '✕ टालें'), findsOneWidget);
    });
  });

  group('the Hindi yoga names', () {
    test('every yoga the engine can name has one', () {
      for (final name in [...yogaRuleNames(), 'Ravi Yoga', 'Jwalamukhi', 'Ravi Yoga (Vajra Yog)', 'Ravi Yoga (Mudgar Yog)']) {
        expect(dayYogaName(name, Lang.hi), isNot(name), reason: name);
        expect(dayYogaName(name, Lang.en), name);
      }
    });
  });

  testWidgets('Full Panchang has the Muhurat grid in a group of its own', (tester) async {
    await openApp(tester, now: ist(2026, 11, 7));
    final open = find.text('पूरा पंचांग देखें');
    await tester.ensureVisible(open);
    await tester.tap(open);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(TextButton, 'मुहूर्त'));
    await tester.pumpAndSettle();

    expect(tile('rahu-kaal'), findsOneWidget);
  });
}
