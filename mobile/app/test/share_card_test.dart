import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/engine/festival_reading.dart';
import 'package:jainpanchang/features/share/share_card.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/l10n/app_localizations.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:jainpanchang/settings/settings_store.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

const _delhi = (lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

PanchangDay _day(CivilDate date) =>
    readDay(DayRequest(date: date, lat: _delhi.lat, lon: _delhi.lon, timezone: _delhi.timezone));

Future<List<FestivalOccurrence>> _festivals(int year) => realFestivals(
  FestivalRequest(
    year: year,
    lat: _delhi.lat,
    lon: _delhi.lon,
    timezone: _delhi.timezone,
    profile: Tradition.tapagachchha.id,
  ),
);

/// The card for [date] in Delhi with the Tapagachchha festivals, in [locale].
Future<ShareCardContent> _content(CivilDate date, {String locale = 'hi'}) async {
  final reading = _day(date);
  final l10n = lookupAppLocalizations(Locale(locale));
  return shareCardContent(
    reading: reading,
    month: reading.month,
    festivals: await _festivals(date.year),
    place: locale == 'hi' ? 'दिल्ली' : 'Delhi',
    timezone: _delhi.timezone,
    l10n: l10n,
  );
}

Future<void> _pumpCard(WidgetTester tester, ShareCardContent content) async {
  await tester.pumpWidget(ShareCard(content: content));
}

String _clock(DateTime utc, Lang lang) => clockPhrase(cityWall(utc, _delhi.timezone), lang);

Finder _rich(String text) => find.textContaining(text, findRichText: true);

/// The card's real faces, so its height is what a phone lays out, not the test font's.
Future<void> _loadFonts() async {
  Future<void> load(String family, List<String> files) async {
    final loader = FontLoader(family);
    for (final file in files) {
      loader.addFont(Future.value(ByteData.sublistView(File('assets/fonts/$file').readAsBytesSync())));
    }
    await loader.load();
  }

  await load('Mukta', ['Mukta-Regular.ttf', 'Mukta-Medium.ttf', 'Mukta-SemiBold.ttf', 'Mukta-Bold.ttf']);
  await load('TiroDevanagariHindi', ['TiroDevanagariHindi-Regular.ttf']);
}

void main() {
  setUpAll(_loadFonts);

  group('the card', () {
    testWidgets('greets, then names the date, tithi, month, samvats, sun times, city and app', (tester) async {
      // 22 Oct 2026 has no festival in Delhi for Tapagachchha.
      const date = CivilDate(2026, 10, 22);
      final reading = _day(date);
      await _pumpCard(tester, await _content(date));

      expect(find.text('जय जिनेन्द्र'), findsOneWidget);
      expect(find.text('गुरुवार, 22 अक्टूबर 2026'), findsOneWidget);
      expect(find.text('शुक्ल एकादशी'), findsOneWidget);
      expect(_rich('आश्विन'), findsOneWidget);
      expect(_rich('फिर शुक्ल द्वादशी'), findsOneWidget);
      expect(_rich('वीर नि. सं. 2552 · वि. सं. 2083'), findsOneWidget);
      expect(find.text('सूर्योदय'), findsOneWidget);
      expect(_rich(_clock(reading.sunrise, Lang.hi)), findsOneWidget);
      expect(find.text('सूर्यास्त'), findsOneWidget);
      expect(_rich(_clock(reading.sunset, Lang.hi)), findsOneWidget);
      expect(find.text('दिल्ली'), findsOneWidget);
      expect(find.text('जैन पंचांग'), findsOneWidget);
    });

    testWidgets('has no festival strips on a day without festivals', (tester) async {
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 22)));

      expect(find.byKey(const Key('share-strip-parva')), findsNothing);
      expect(find.byKey(const Key('share-strip-vrat')), findsNothing);
    });

    testWidgets('shows a kalyanak in the red strip and a vrat in the green one', (tester) async {
      // 20 Oct 2026: Neminath's omniscience kalyanak and the Namokar chain.
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 20)));

      final parva = find.byKey(const Key('share-strip-parva'));
      expect(find.descendant(of: parva, matching: find.text('श्री नेमिनाथ जी — केवलज्ञान कल्याणक')), findsOneWidget);
      expect(find.descendant(of: parva, matching: find.text('कल्याणक')), findsOneWidget);
      final vrat = find.byKey(const Key('share-strip-vrat'));
      expect(find.descendant(of: vrat, matching: find.text('णमोकार महामंत्र व्रत श्रृंखला')), findsOneWidget);
      expect(find.descendant(of: vrat, matching: find.text('व्रत')), findsOneWidget);
    });

    testWidgets('names the first festival of a strip and counts the rest', (tester) async {
      // 25 Oct 2026: Pakhi Chaudas, plus two vrats.
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 25)));

      final parva = find.byKey(const Key('share-strip-parva'));
      expect(find.descendant(of: parva, matching: find.text('पाखी चौदस (शुक्ल)')), findsOneWidget);
      final vrat = find.byKey(const Key('share-strip-vrat'));
      expect(find.descendant(of: vrat, matching: find.text('भक्ताम्बर व्रत')), findsOneWidget);
      expect(find.descendant(of: vrat, matching: find.text('+1 और')), findsOneWidget);
    });

    testWidgets('is in English on an English phone, the greeting still in Devanagari', (tester) async {
      const date = CivilDate(2026, 10, 22);
      final reading = _day(date);
      await _pumpCard(tester, await _content(date, locale: 'en'));

      expect(find.text('जय जिनेन्द्र'), findsOneWidget);
      expect(find.text('Thursday, 22 October 2026'), findsOneWidget);
      expect(find.text('Shukla Ekadashi'), findsOneWidget);
      expect(_rich('VNS 2552 · VS 2083'), findsOneWidget);
      expect(find.text('Sunrise'), findsOneWidget);
      expect(_rich(_clock(reading.sunrise, Lang.en)), findsOneWidget);
      expect(find.text('Delhi'), findsOneWidget);
      expect(find.text('Jain Panchang'), findsOneWidget);
    });

    testWidgets('keeps the light Navpad ground on a dark phone', (tester) async {
      tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
      addTearDown(tester.platformDispatcher.clearAllTestValues);
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 22)));

      final ground = tester.widget<ColoredBox>(find.byKey(const Key('share-card')));
      expect(ground.color, const Color(0xFFFFFFFF));
    });
  });

  group('the text sent with the image', () {
    test('says the greeting, date and city, tithi and month, samvats, sun times and the app', () async {
      const date = CivilDate(2026, 10, 22);
      final reading = _day(date);
      final text = shareText(await _content(date));

      expect(
        text,
        [
          'जय जिनेन्द्र',
          'गुरुवार, 22 अक्टूबर 2026 · दिल्ली',
          'शुक्ल एकादशी · आश्विन',
          'वीर नि. सं. 2552 · वि. सं. 2083',
          'सूर्योदय ${_clock(reading.sunrise, Lang.hi)} · सूर्यास्त ${_clock(reading.sunset, Lang.hi)}',
          '— जैन पंचांग',
        ].join('\n'),
      );
    });

    test('lists the strips the card shows', () async {
      final lines = shareText(await _content(const CivilDate(2026, 10, 25))).split('\n');

      expect(lines, containsAll(['पाखी चौदस (शुक्ल) · पर्व', 'भक्ताम्बर व्रत · +1 और']));
      expect(lines.last, '— जैन पंचांग');
    });
  });

  group('the image', () {
    Future<ui.Image> render(WidgetTester tester, CivilDate date) async {
      final content = await _content(date);
      await tester.pumpWidget(const SizedBox());
      final png = (await tester.runAsync(() => renderShareCard(content, view: tester.view)))!;
      expect(png.sublist(0, 8), Uint8List.fromList([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]));
      return (await tester.runAsync(() async {
        final codec = await ui.instantiateImageCodec(png);
        return (await codec.getNextFrame()).image;
      }))!;
    }

    testWidgets('is a 1080 × 1350 PNG (4:5) on a quiet day', (tester) async {
      final image = await render(tester, const CivilDate(2026, 10, 22));

      expect((image.width, image.height), (1080, 1350));
    });

    testWidgets('grows taller, never wider, on a day with festivals', (tester) async {
      final image = await render(tester, const CivilDate(2026, 10, 25));

      expect(image.width, 1080);
      expect(image.height, greaterThanOrEqualTo(1350));
    });
  });
}
