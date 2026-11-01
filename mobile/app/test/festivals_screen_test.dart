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

const delhi2026 = FestivalRequest(
  year: 2026,
  lat: 28.6139,
  lon: 77.2090,
  timezone: 'Asia/Kolkata',
  profile: 'shwetambar_murtipujak_tapagachchha',
);

final list = find.byKey(const Key('festivals-list'));
Finder dateRow(CivilDate date) => find.byKey(Key('festival-date-${date.iso}'));
Finder chip(String label) => find.widgetWithText(FilterChip, label);

Future<void> openFestivals(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  FestivalReader festivals = realFestivals,
  Map<String, Object> saved = const {'location.city': 'delhi'},
}) async {
  await openApp(tester, now: now, phone: phone, festivals: festivals, saved: saved);
  final tab = phone.languageCode == 'en' ? 'Festivals' : 'पर्व';
  await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text(tab)));
  // A held year keeps the spinner turning, so it never settles.
  await (festivals == realFestivals ? tester.pumpAndSettle() : tester.pump());
}

List<FestivalKind> marksInList(WidgetTester tester) => [
  for (final mark in tester.widgetList<FestivalMark>(find.descendant(of: list, matching: find.byType(FestivalMark))))
    mark.kind,
];

void main() {
  testWidgets('opens on today, with nothing from before it', (tester) async {
    await openFestivals(tester, now: ist(2026, 10, 29));
    final expected = festivalDates(await realFestivals(delhi2026), from: const CivilDate(2026, 10, 29), lang: Lang.hi);
    expect(expected.first.date, const CivilDate(2026, 10, 29));

    final first = tester.getTopLeft(dateRow(expected.first.date)).dy;
    for (final row in tester.widgetList(
      find.descendant(
        of: list,
        matching: find.byWidgetPredicate(
          (w) => w.key is ValueKey<String> && (w.key! as ValueKey<String>).value.startsWith('festival-date-'),
        ),
      ),
    )) {
      final iso = (row.key! as ValueKey<String>).value.substring('festival-date-'.length);
      expect(iso.compareTo('2026-10-29'), greaterThanOrEqualTo(0), reason: iso);
    }
    expect(tester.getTopLeft(find.byKey(const Key('festival-month-2026-10'))).dy, lessThan(first));
  });

  testWidgets('groups the dates under Gregorian month headings in Tiro', (tester) async {
    await openFestivals(
      tester,
      now: ist(2026, 10, 31),
      saved: {'location.city': 'delhi', 'festivals.filter': 'kalyanak'},
    );
    final november = find.byKey(const Key('festival-month-2026-11'));

    await tester.scrollUntilVisible(
      november,
      300,
      scrollable: find.descendant(of: list, matching: find.byType(Scrollable)),
    );
    final heading = find.descendant(of: november, matching: find.text('नवंबर 2026'));
    expect(heading, findsOneWidget);
    expect(tester.widget<Text>(heading).style!.fontFamily, 'TiroDevanagariHindi');
  });

  testWidgets('the five chips filter by mark, and all shows every mark', (tester) async {
    // 7–8 November 2026 carry all four marks.
    await openFestivals(tester, now: ist(2026, 11, 7));

    expect(find.byType(FilterChip), findsNWidgets(5));
    expect(marksInList(tester).toSet(), containsAll(FestivalKind.values));
    for (final (label, kind) in [
      ('महापर्व', FestivalKind.mahaparva),
      ('कल्याणक', FestivalKind.kalyanak),
      ('पर्व', FestivalKind.parva),
      ('व्रत', FestivalKind.vrat),
    ]) {
      await tester.tap(chip(label));
      await tester.pumpAndSettle();
      expect(tester.widget<FilterChip>(chip(label)).selected, isTrue, reason: label);
      expect(marksInList(tester), isNotEmpty, reason: label);
      expect(marksInList(tester).toSet(), {kind}, reason: label);
    }
  });

  testWidgets('remembers the chosen filter across a restart', (tester) async {
    await openFestivals(tester, now: ist(2026, 10, 31));
    await tester.tap(chip('कल्याणक'));
    await tester.pumpAndSettle();

    await restartApp(tester, now: ist(2026, 10, 31));
    await openTab(tester, 'पर्व');

    expect(tester.widget<FilterChip>(chip('कल्याणक')).selected, isTrue);
    expect(tester.widget<FilterChip>(chip('सभी')).selected, isFalse);
  });

  testWidgets('shows a loading state until the year arrives', (tester) async {
    final held = HeldFestivals();
    await openFestivals(tester, now: ist(2026, 10, 31), festivals: held.call);

    expect(find.byKey(const Key('festivals-loading')), findsOneWidget);
    expect(find.text('पर्व गिने जा रहे हैं…'), findsOneWidget);
    expect(find.byType(FilterChip), findsNWidgets(5));
    expect(list, findsNothing);

    held.release();
    await tester.pumpAndSettle();
    expect(find.text('पर्व गिने जा रहे हैं…'), findsNothing);
    expect(find.byKey(const Key('festivals-loading')), findsNothing);
    expect(list, findsOneWidget);
  });

  testWidgets('asks for the saved tradition and sunrise rule', (tester) async {
    final held = HeldFestivals();
    await openFestivals(
      tester,
      now: ist(2026, 10, 31),
      festivals: held.call,
      saved: {
        'location.city': 'delhi',
        'settings.tradition': 'shwetambar_terapanthi',
        'settings.sunriseRule': 'traditional',
      },
    );

    expect(
      held.requests.where(
        (r) => r.year == 2026 && r.profile == 'shwetambar_terapanthi' && r.rule == SunriseRule.traditional,
      ),
      isNotEmpty,
    );
  });

  testWidgets('a mahaparva line is a filled red row with a white mark', (tester) async {
    await openFestivals(
      tester,
      now: ist(2026, 11, 9),
      saved: {'location.city': 'delhi', 'festivals.filter': 'mahaparva'},
    );
    final row = dateRow(const CivilDate(2026, 11, 9));
    final name = find.descendant(of: row, matching: find.text('दीपावली (भगवान महावीर निर्वाण)'));
    final n = Theme.of(tester.element(row)).extension<Navpad>()!;

    expect(name, findsOneWidget);
    final fill = tester.widget<Container>(
      find.ancestor(of: name, matching: find.byKey(const Key('festival-line-mahaparva'))).first,
    );
    expect((fill.decoration! as BoxDecoration).color, n.red);
    expect(tester.widget<Text>(name).style!.color, n.onRed);
    final mark = find.descendant(
      of: find.byKey(const Key('festival-line-mahaparva')).first,
      matching: find.byType(FestivalMark),
    );
    final box = tester.widget<DecoratedBox>(find.descendant(of: mark, matching: find.byType(DecoratedBox)));
    expect((box.decoration as BoxDecoration).color, n.onRed);
  });

  testWidgets('Mahavir Nirvana is one line on 9 November', (tester) async {
    await openFestivals(
      tester,
      now: ist(2026, 11, 9),
      saved: {'location.city': 'delhi', 'festivals.filter': 'mahaparva'},
    );
    final row = dateRow(const CivilDate(2026, 11, 9));

    expect(find.descendant(of: row, matching: find.text('दीपावली (भगवान महावीर निर्वाण)')), findsOneWidget);
    expect(find.descendant(of: row, matching: find.text('महावीर स्वामी निर्वाण कल्याणक (दीपावली)')), findsNothing);
  });

  testWidgets('a span shows its dates', (tester) async {
    // Kartika Ashtahnika, 17–24 November 2026.
    await openFestivals(
      tester,
      now: ist(2026, 11, 17),
      saved: {'location.city': 'delhi', 'festivals.filter': 'mahaparva'},
    );

    expect(
      find.descendant(of: dateRow(const CivilDate(2026, 11, 17)), matching: find.textContaining('17–24 नवंबर')),
      findsOneWidget,
    );
  });

  testWidgets('a date opens the Month tab on that day', (tester) async {
    await openFestivals(
      tester,
      now: ist(2026, 11, 1),
      saved: {'location.city': 'delhi', 'festivals.filter': 'mahaparva'},
    );

    await tester.tap(dateRow(const CivilDate(2026, 11, 9)));
    await tester.pumpAndSettle();

    expect(find.text('नवंबर 2026'), findsOneWidget);
    expect(find.text('सोमवार, 9 नवंबर 2026'), findsOneWidget);
  });

  testWidgets('reads in English on an English phone', (tester) async {
    await openFestivals(tester, now: ist(2026, 11, 9), phone: const Locale('en', 'US'));

    expect(chip('All'), findsOneWidget);
    expect(
      find.descendant(
        of: dateRow(const CivilDate(2026, 11, 9)),
        matching: find.text('Diwali (Mahavir Nirvan & Gautam Swami Kevalgyan)'),
      ),
      findsOneWidget,
    );
  });
}
