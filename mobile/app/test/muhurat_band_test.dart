import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/features/muhurat/muhurat_band.dart';
import 'package:jainpanchang/format/muhurat_text.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/shared/navpad_icons.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

DayRequest delhiOn(CivilDate date) => DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');
PanchangMuhurat muhuratOn(CivilDate date) => readMuhurat(MuhuratRequest(delhiOn(date)));
PanchangDay dayOn(CivilDate date) => readDay(delhiOn(date));

DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, 'Asia/Kolkata'));
String hm(DateTime utc) => clockTime(wall(utc), Lang.hi).time;
String range(DateTime start, DateTime end, [Lang lang = Lang.hi]) => glued(clockRange(wall(start), wall(end), lang));
bool inside(DateTime now, TimeWindow w) => runsAt(now, start: w.start, end: w.end);

final title = find.textContaining(RegExp(r'^(चौघड़िया|Choghadiya): | · ✕ (टालें|Avoid)$'));

/// Delhi. 22 Oct 2026 (Thursday): Char, Labh, Amrit are the 4th to 6th day
/// slots (choghadiya_service.py); 21 Oct ends with a Bhadra on Earth in the
/// night. 7 Nov (Saturday): Bhadra in Patal only, so Abhijit is free of bad
/// windows. 17 Nov (Tuesday): Panchak and a Bhadra on Earth from 3:30 PM,
/// inside Tuesday's Rahu Kaal; the Panchak runs into 18 Nov. 3 Nov: Gandmool.
void main() {
  const oct22 = CivilDate(2026, 10, 22);
  const nov7 = CivilDate(2026, 11, 7);
  const nov17 = CivilDate(2026, 11, 17);
  const nov3 = CivilDate(2026, 11, 3);

  group('the bad window running now', () {
    test('is Rahu Kaal inside Rahu Kaal, ending with it', () {
      final m = muhuratOn(nov7);
      final now = m.rahuKaal.start.add(const Duration(minutes: 1));

      expect(badWindowAt(m, now), (kind: BadWindow.rahuKaal, end: m.rahuKaal.end));
    });

    test('is Yamaganda, then Gulika, each in its own eighth', () {
      final m = muhuratOn(nov7);

      expect(badWindowAt(m, m.yamaganda.start)?.kind, BadWindow.yamaganda);
      expect(badWindowAt(m, m.gulika.start)?.kind, BadWindow.gulika);
    });

    test('is none at Abhijit on a day whose Bhadra is in Patal', () {
      final m = muhuratOn(nov7);
      final now = m.abhijit.start.add(m.abhijit.end.difference(m.abhijit.start) ~/ 2);
      expect([m.rahuKaal, m.yamaganda, m.gulika].any((w) => inside(now, w)), isFalse);

      expect(badWindowAt(m, now), isNull);
    });

    test('is Bhadra on Earth once Rahu Kaal is over, before the Panchak', () {
      final m = muhuratOn(nov17);
      final w = m.bhadra.firstWhere((w) => w.residence == BhadraResidence.earth);
      final now = m.rahuKaal.end;
      expect(inside(now, (start: w.start, end: w.end)), isTrue);
      expect(inside(now, m.panchak.window!), isTrue);

      expect(badWindowAt(m, now), (kind: BadWindow.bhadra, end: w.end));
    });

    test('skips a Bhadra in Patal', () {
      final m = muhuratOn(nov17);
      final patal = m.bhadra.firstWhere((w) => w.residence == BhadraResidence.underworld);
      final now = patal.start.add(const Duration(minutes: 1));
      expect([m.rahuKaal, m.yamaganda, m.gulika].any((r) => inside(now, r)), isFalse);

      expect(badWindowAt(m, now), isNull);
    });

    test('puts Rahu Kaal before a Panchak running at the same time', () {
      final m = muhuratOn(nov17);
      final now = m.panchak.window!.start.add(const Duration(minutes: 1));
      expect(inside(now, m.rahuKaal), isTrue, reason: "the Panchak begins in Tuesday's Rahu Kaal");

      expect(badWindowAt(m, now)?.kind, BadWindow.rahuKaal);
    });

    test('is none in a Panchak: it runs for days, so the band keeps to the choghadiya', () {
      final m = muhuratOn(nov17);
      final now = m.bhadra.last.end;
      expect(inside(now, m.panchak.window!), isTrue);

      expect(badWindowAt(m, now), isNull);
    });

    test('is none in a Gandmool, for the same reason', () {
      final m = muhuratOn(nov3);
      final w = m.gandmool.first;
      final now = [for (var t = w.start; t.isBefore(w.end); t = t.add(const Duration(minutes: 10))) t].firstWhere(
        (t) =>
            ![m.rahuKaal, m.yamaganda, m.gulika].any((r) => inside(t, r)) &&
            !m.bhadra.any((b) => b.residence == BhadraResidence.earth && inside(t, (start: b.start, end: b.end))),
      );

      expect(badWindowAt(m, now), isNull);
    });
  });

  group('the next good choghadiya', () {
    final slots = dayOn(oct22).choghadiya;

    test('is the next Amrit, Shubh or Labh slot that starts after now', () {
      expect(nextGoodChoghadiya(slots, ist(2026, 10, 22, 10, 52)), slots[4], reason: 'Labh follows Char');
    });

    test('skips the good slot running now', () {
      expect(nextGoodChoghadiya(slots, slots[4].start), slots[5], reason: 'Amrit follows Labh');
    });

    test('is none after the last good slot', () {
      expect(nextGoodChoghadiya(slots, slots.last.end), isNull);
    });
  });

  group('the मुहूर्त band on Today', () {
    testWidgets('shows the choghadiya slot when no bad window runs, then the next good slot', (tester) async {
      final m = muhuratOn(nov7);
      final now = m.abhijit.start.add(m.abhijit.end.difference(m.abhijit.start) ~/ 2);
      final slots = dayOn(nov7).choghadiya;
      final slot = slots.firstWhere((s) => runsAt(now, start: s.start, end: s.end));
      final next = nextGoodChoghadiya(slots, now)!;
      await openApp(tester, now: now);

      expect(find.textContaining('चौघड़िया: ${choghadiyaName(slot.name, Lang.hi)} · '), findsOneWidget);
      expect(find.text('अगला शुभ: ${choghadiyaName(next.name, Lang.hi)} · ${range(next.start, next.end)}'), findsOneWidget);
      expect(find.text('${hm(slot.end)} तक · ${durationText(slot.end.difference(now), Lang.hi)}'), findsOneWidget);
    });

    testWidgets('during a Panchak it shows the choghadiya slot', (tester) async {
      final m = muhuratOn(nov17);
      final now = m.bhadra.last.end;
      expect(inside(now, m.panchak.window!), isTrue);
      await openApp(tester, now: now);

      expect(find.text('पंचक · ✕ टालें'), findsNothing);
      expect(find.textContaining('चौघड़िया: '), findsOneWidget);
    });

    testWidgets('a slot ending after midnight shows the date of its end', (tester) async {
      final slots = dayOn(nov7).choghadiya;
      final slot = slots.firstWhere((s) => wall(s.start).day == 7 && wall(s.end).day == 8);
      final now = slot.start.add(const Duration(minutes: 1));
      await openApp(tester, now: now);

      expect(
        find.text(
          '${glued(instantPhrase(wall(slot.end), day: nov7, lang: Lang.hi))} तक · '
          '${durationText(slot.end.difference(now), Lang.hi)}',
        ),
        findsOneWidget,
      );
    });

    testWidgets('leads with Rahu Kaal while it runs, and counts down to its end', (tester) async {
      final m = muhuratOn(nov7);
      final now = m.rahuKaal.start.add(const Duration(minutes: 5));
      await openApp(tester, now: now);

      expect(find.text('राहु काल · ✕ टालें'), findsOneWidget);
      expect(
        find.text('${hm(m.rahuKaal.end)} तक · ${durationText(m.rahuKaal.end.difference(now), Lang.hi)}'),
        findsOneWidget,
      );
    });

    testWidgets('is in English on an English phone', (tester) async {
      final m = muhuratOn(nov7);
      await openApp(tester, now: m.rahuKaal.start.add(const Duration(minutes: 5)), phone: const Locale('en', 'US'));

      expect(find.text('Rahu Kaal · ✕ Avoid'), findsOneWidget);
      expect(find.textContaining(RegExp(r'^Next good: ')), findsOneWidget);
    });

    testWidgets("before sunrise it reads the night's windows from the day before", (tester) async {
      final now = ist(2026, 10, 22, 5, 0);
      final night = muhuratOn(const CivilDate(2026, 10, 21));
      expect(badWindowAt(night, now)?.kind, BadWindow.bhadra, reason: '21 Oct ends with a Bhadra on Earth');
      await openApp(tester, now: now);

      expect(find.text('भद्रा · ✕ टालें'), findsOneWidget);
    });

    testWidgets('is not shown on another day', (tester) async {
      await openApp(tester, now: muhuratOn(nov7).rahuKaal.start);
      expect(title, findsOneWidget);
      await tester.tap(nav('अगला दिन'));
      await tester.pumpAndSettle();

      expect(title, findsNothing);
    });

    testWidgets('leads with the Muhurat icon and opens the Muhurat grid', (tester) async {
      await openApp(tester, now: muhuratOn(nov7).rahuKaal.start);
      final icon = find.descendant(
        of: find.ancestor(of: title, matching: find.byType(InkWell)).first,
        matching: find.byType(NavpadIcon),
      );
      expect(tester.widget<NavpadIcon>(icon).glyph, NavpadGlyph.abhijit);

      await tester.ensureVisible(title);
      await tester.tap(title);
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('muhurat-tile-rahu-kaal')), findsOneWidget);
    });

    for (final scale in [1.3, 1.6, 2.0]) {
      testWidgets('nothing overflows on Today at ${scale}x text', (tester) async {
        final m = muhuratOn(nov7);
        await openApp(tester, now: m.rahuKaal.start.add(const Duration(minutes: 5)), textScale: scale);

        expect(tester.takeException(), isNull);
        expect(title, findsOneWidget);
      });
    }
  });
}
