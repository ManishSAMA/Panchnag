import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/features/share/share_button.dart';

import 'support/harness.dart';

/// Opens the app with a share sheet that records what it was handed.
Future<List<SharedDay>> _openRecording(
  WidgetTester tester, {
  required DateTime now,
  Locale phone = const Locale('hi', 'IN'),
  Map<String, Object> settings = const {},
}) async {
  final shared = <SharedDay>[];
  await openApp(
    tester,
    now: now,
    phone: phone,
    saved: {'location.city': 'delhi', ...settings},
    sharer: (day) async => shared.add(day),
  );
  return shared;
}

Future<void> _tapShare(WidgetTester tester, String tooltip) async {
  await tester.tap(find.byTooltip(tooltip));
  // The card paints and encodes on the real event loop.
  await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 500)));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('sits in Today\'s top bar before the gear, 48 dp and labelled', (tester) async {
    await openApp(tester, now: ist(2026, 10, 22));

    final share = find.ancestor(of: find.byTooltip('साझा करें'), matching: find.byType(IconButton));
    expect(share, findsOneWidget);
    expect(tester.getSize(share), const Size(48, 48));
    expect(tester.getCenter(share).dx, lessThan(tester.getCenter(find.byTooltip('सेटिंग्स')).dx));
  });

  testWidgets('hands the share sheet a PNG of the card and its text', (tester) async {
    final shared = await _openRecording(tester, now: ist(2026, 10, 22));

    await _tapShare(tester, 'साझा करें');

    expect(shared, hasLength(1));
    expect(shared.single.png.sublist(0, 4), [0x89, 0x50, 0x4E, 0x47]);
    expect(shared.single.text, startsWith('जय जिनेन्द्र\nगुरुवार, 22 अक्टूबर 2026 · दिल्ली\nशुक्ल एकादशी'));
    expect(shared.single.fileName, 'jain-panchang-2026-10-22.png');
  });

  testWidgets('shares the date Today shows, not the current date', (tester) async {
    final shared = await _openRecording(tester, now: ist(2026, 10, 22));

    await tester.tap(nav('अगला दिन'));
    await tester.pumpAndSettle();
    await _tapShare(tester, 'साझा करें');

    expect(shared.single.text, contains('शुक्रवार, 23 अक्टूबर 2026'));
    expect(shared.single.fileName, 'jain-panchang-2026-10-23.png');
  });

  testWidgets('includes the date\'s festivals', (tester) async {
    final shared = await _openRecording(tester, now: ist(2026, 10, 20));

    await _tapShare(tester, 'साझा करें');

    expect(shared.single.text, contains('श्री नेमिनाथ जी — केवलज्ञान कल्याणक · कल्याणक'));
  });

  testWidgets('names the month in the chosen month system', (tester) async {
    // 31 Oct 2026 is Krishna Shashthi: Kartika when months end at Purnima, Ashwin when they end at Amavasya.
    final purnimanta = await _openRecording(tester, now: ist(2026, 10, 31));
    await _tapShare(tester, 'साझा करें');
    expect(purnimanta.single.text, contains('कृष्ण षष्ठी · कार्तिक'));

    final amanta = await _openRecording(tester, now: ist(2026, 10, 31), settings: {'settings.monthSystem': 'amanta'});
    await _tapShare(tester, 'साझा करें');
    expect(amanta.single.text, contains('कृष्ण षष्ठी · आश्विन'));
  });

  testWidgets('uses the chosen sunrise rule', (tester) async {
    String sunriseLine(List<SharedDay> shared) =>
        shared.single.text.split('\n').firstWhere((l) => l.startsWith('सूर्योदय'));
    final modern = await _openRecording(tester, now: ist(2026, 10, 22));
    await _tapShare(tester, 'साझा करें');
    final traditional = await _openRecording(
      tester,
      now: ist(2026, 10, 22),
      settings: {'settings.sunriseRule': 'traditional'},
    );
    await _tapShare(tester, 'साझा करें');

    expect(sunriseLine(traditional), isNot(sunriseLine(modern)));
  });

  testWidgets('is in English on an English phone', (tester) async {
    final shared = await _openRecording(tester, now: ist(2026, 10, 22), phone: const Locale('en', 'US'));

    await _tapShare(tester, 'Share');

    expect(shared.single.text, contains('Thursday, 22 October 2026 · Delhi'));
    expect(shared.single.text, endsWith('— Jain Panchang'));
  });
}
