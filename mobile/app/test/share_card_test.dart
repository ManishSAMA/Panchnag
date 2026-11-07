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
import 'package:jainpanchang/shared/panchang_symbols.dart';
import 'package:panchang_engine/panchang_engine.dart';

import 'support/harness.dart';

const _delhi = (lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

DayRequest _request(CivilDate date) => DayRequest(
  date: date,
  lat: _delhi.lat,
  lon: _delhi.lon,
  timezone: _delhi.timezone,
);

PanchangDay _day(CivilDate date) => readDay(_request(date));

PanchangSection _section(CivilDate date) =>
    readSection(SectionRequest(_request(date)));

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
Future<ShareCardContent> _content(
  CivilDate date, {
  String locale = 'hi',
}) async {
  final reading = _day(date);
  final l10n = lookupAppLocalizations(Locale(locale));
  return shareCardContent(
    reading: reading,
    section: _section(date),
    month: reading.month,
    festivals: await _festivals(date.year),
    place: locale == 'hi' ? 'दिल्ली' : 'Delhi',
    timezone: _delhi.timezone,
    l10n: l10n,
  );
}

/// The card at its own size, in a window tall enough for a busy day.
Future<void> _pumpCard(WidgetTester tester, ShareCardContent content) async {
  tester.view
    ..physicalSize = const Size(1080, 7200)
    ..devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    Align(
      alignment: Alignment.topLeft,
      child: ShareCard(content: content),
    ),
  );
}

String _clock(DateTime utc, Lang lang) =>
    clockPhrase(cityWall(utc, _delhi.timezone), lang);

Finder _rich(String text) => find.textContaining(text, findRichText: true);

Finder _box(String name) => find.byKey(Key('share-box-$name'));

/// A line's words as the card shows them, glyphs left out, as written: times
/// are glued to their period word and तक with non-breaking spaces.
String _rawLine(WidgetTester tester, String name) => tester
    .widget<RichText>(
      find
          .descendant(
            of: find.byKey(Key('share-line-$name')),
            matching: find.byType(RichText),
          )
          .last,
    )
    .text
    .toPlainText(includePlaceholders: false);

String _line(WidgetTester tester, String name) =>
    _rawLine(tester, name).replaceAll('\u00A0', ' ');

/// "`name` `end` तक" with the end dated when it falls after [day].
String _until(String name, DateTime utc, CivilDate day, Lang lang) {
  final end = instantPhrase(
    cityWall(utc, _delhi.timezone),
    day: day,
    lang: lang,
  );
  return lang == Lang.hi ? '$name $end तक' : '$name until $end';
}

/// The card's real faces, so its height is what a phone lays out, not the test font's.
Future<void> _loadFonts() async {
  Future<void> load(String family, List<String> files) async {
    final loader = FontLoader(family);
    for (final file in files) {
      loader.addFont(
        Future.value(
          ByteData.sublistView(File('assets/fonts/$file').readAsBytesSync()),
        ),
      );
    }
    await loader.load();
  }

  await load('Mukta', [
    'Mukta-Regular.ttf',
    'Mukta-Medium.ttf',
    'Mukta-SemiBold.ttf',
    'Mukta-Bold.ttf',
  ]);
  await load('TiroDevanagariHindi', ['TiroDevanagariHindi-Regular.ttf']);
}

void main() {
  setUpAll(_loadFonts);

  group('the card', () {
    testWidgets(
      'greets, then names the date, tithi, month, sun times, city and app',
      (tester) async {
        // 22 Oct 2026 has no festival in Delhi for Tapagachchha.
        const date = CivilDate(2026, 10, 22);
        final reading = _day(date);
        await _pumpCard(tester, await _content(date));

        expect(find.text('जय जिनेन्द्र'), findsOneWidget);
        expect(find.text('गुरुवार, 22 अक्टूबर 2026'), findsOneWidget);
        expect(find.text('शुक्ल एकादशी'), findsOneWidget);
        expect(_rich('आश्विन'), findsOneWidget);
        expect(
          find.descendant(
            of: find.byKey(const Key('share-header')),
            matching: _rich('फिर शुक्ल द्वादशी'),
          ),
          findsOneWidget,
        );
        expect(find.text('सूर्योदय'), findsOneWidget);
        expect(
          find.descendant(
            of: _box('sun'),
            matching: _rich(_clock(reading.sunrise, Lang.hi)),
          ),
          findsOneWidget,
        );
        expect(find.text('सूर्यास्त'), findsOneWidget);
        expect(
          find.descendant(
            of: _box('sun'),
            matching: _rich(_clock(reading.sunset, Lang.hi)),
          ),
          findsOneWidget,
        );
        expect(find.text('दिल्ली'), findsOneWidget);
        expect(find.text('जैन पंचांग'), findsOneWidget);
      },
    );

    testWidgets('has no festival box on a day without festivals', (
      tester,
    ) async {
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 22)));

      expect(_box('festivals'), findsNothing);
      expect(find.byKey(const Key('share-strip-parva')), findsNothing);
      expect(find.byKey(const Key('share-strip-vrat')), findsNothing);
    });

    testWidgets(
      'pairs sunrise and sunset with the three samvats in the first box',
      (tester) async {
        const date = CivilDate(2026, 10, 22);
        final reading = _day(date);
        await _pumpCard(tester, await _content(date));

        final box = _box('sun');
        for (final text in [
          'सूर्योदय',
          'सूर्यास्त',
          'वीर निर्वाण संवत ${reading.viraNirvanaSamvat}',
          'विक्रम संवत ${reading.vikramSamvat}',
          'शक संवत ${reading.shakaSamvat}',
        ]) {
          expect(
            find.descendant(of: box, matching: find.text(text)),
            findsOneWidget,
            reason: text,
          );
        }
      },
    );

    testWidgets(
      'gives the tithi, nakshatra, yoga and karana each with the next, and the Moon sign, in a पंचांग box',
      (tester) async {
        const date = CivilDate(2026, 10, 22);
        final day = _day(date);
        final section = _section(date);
        await _pumpCard(tester, await _content(date));
        String until(String name, DateTime utc) =>
            _until(name, utc, date, Lang.hi);

        expect(
          find.descendant(of: _box('panchang'), matching: find.text('पंचांग')),
          findsOneWidget,
        );
        expect(
          _line(tester, 'tithi'),
          '${until(tithiName(day.jainTithi.index, Lang.hi), day.jainTithi.endsAt)}, फिर '
          '${until(tithiName(section.nextTithi.index, Lang.hi), section.nextTithi.endsAt)}',
        );
        expect(
          _line(tester, 'nakshatra'),
          '${until('${nakshatraName(day.nakshatra.index, Lang.hi)} (चरण ${day.nakshatra.pada})', day.nakshatra.endsAt)}, फिर '
          '${until(nakshatraName(section.nextNakshatra.index, Lang.hi), section.nextNakshatra.endsAt)}',
        );
        expect(
          find.descendant(
            of: find.byKey(const Key('share-line-nakshatra')),
            matching: find.byType(PanchangSymbol),
          ),
          findsNWidgets(
            nakshatraRashis(day.nakshatra.index).length +
                nakshatraRashis(section.nextNakshatra.index).length,
          ),
        );
        final [yoga, nextYoga] = section.yogas;
        expect(
          _line(tester, 'yoga'),
          '${until(yogaName(yoga.index, Lang.hi), yoga.endsAt)}, फिर ${until(yogaName(nextYoga.index, Lang.hi), nextYoga.endsAt)}',
        );
        final [karana, nextKarana, ...] = section.karanas;
        expect(
          _line(tester, 'karana'),
          '${until(karanaName(karana.index, Lang.hi), karana.endsAt)}, फिर '
          '${until(karanaName(nextKarana.index, Lang.hi), nextKarana.endsAt)}',
        );
        final [moon, nextMoon] = section.moonRashis;
        expect(
          _line(tester, 'moon-rashi'),
          '${until(rashiName(moon.index, Lang.hi), moon.endsAt)}, फिर ${rashiName(nextMoon.index, Lang.hi)}',
        );
      },
    );

    testWidgets('never wraps a time apart from its period word or तक', (
      tester,
    ) async {
      const date = CivilDate(2026, 10, 20);
      final day = _day(date);
      await _pumpCard(tester, await _content(date));

      final end = instantPhrase(
        cityWall(day.jainTithi.endsAt, _delhi.timezone),
        day: date,
        lang: Lang.hi,
      );
      expect(
        _rawLine(tester, 'tithi'),
        contains('${end.replaceAll(' ', '\u00A0')}\u00A0तक'),
      );
    });

    testWidgets(
      'lists only Amrit, Shubh, Labh and Chal, by day and by night, in a शुभ चौघड़िया box',
      (tester) async {
        const date = CivilDate(2026, 10, 22);
        final day = _day(date);
        await _pumpCard(tester, await _content(date));

        final box = _box('choghadiya');
        expect(
          find.descendant(of: box, matching: find.text('शुभ चौघड़िया')),
          findsOneWidget,
        );
        for (final (half, night) in [('day', false), ('night', true)]) {
          final column = find.byKey(Key('share-choghadiya-$half'));
          final shown = [
            for (final slot in day.choghadiya)
              if (slot.isNight == night &&
                  slot.name.nature != ChoghadiyaNature.inauspicious)
                slot,
          ];
          expect(shown, isNotEmpty);
          for (final slot in shown) {
            final range = clockRange(
              cityWall(slot.start, _delhi.timezone),
              cityWall(slot.end, _delhi.timezone),
              Lang.hi,
            ).replaceAll(' ', '\u00A0');
            expect(
              find.descendant(of: column, matching: find.text(range)),
              findsOneWidget,
              reason: range,
            );
          }
          expect(
            find.descendant(
              of: column,
              matching: find.byWidgetPredicate(
                (w) =>
                    w.key is ValueKey<String> &&
                    (w.key! as ValueKey<String>).value.startsWith(
                      'share-choghadiya-slot-',
                    ),
              ),
            ),
            findsNWidgets(shown.length),
          );
          for (final slot in day.choghadiya.where((s) => s.isNight == night)) {
            if (slot.name.nature == ChoghadiyaNature.inauspicious) {
              expect(
                find.descendant(
                  of: column,
                  matching: find.text(choghadiyaName(slot.name, Lang.hi)),
                ),
                findsNothing,
              );
            }
          }
        }
      },
    );

    testWidgets(
      'shows a kalyanak in the red strip and a vrat in the green one',
      (tester) async {
        // 20 Oct 2026: Neminath's omniscience kalyanak and the Namokar chain.
        await _pumpCard(tester, await _content(const CivilDate(2026, 10, 20)));

        expect(
          find.descendant(
            of: _box('festivals'),
            matching: find.text('पर्व और व्रत'),
          ),
          findsOneWidget,
        );
        final parva = find.descendant(
          of: _box('festivals'),
          matching: find.byKey(const Key('share-strip-parva')),
        );
        expect(
          find.descendant(
            of: parva,
            matching: find.text('श्री नेमिनाथ जी — केवलज्ञान कल्याणक'),
          ),
          findsOneWidget,
        );
        expect(
          find.descendant(of: parva, matching: find.text('कल्याणक')),
          findsOneWidget,
        );
        final vrat = find.byKey(const Key('share-strip-vrat'));
        expect(
          find.descendant(
            of: vrat,
            matching: find.text('णमोकार महामंत्र व्रत श्रृंखला'),
          ),
          findsOneWidget,
        );
        expect(
          find.descendant(of: vrat, matching: find.text('व्रत')),
          findsOneWidget,
        );
      },
    );

    testWidgets('names the first festival of a strip and counts the rest', (
      tester,
    ) async {
      // 25 Oct 2026: Pakhi Chaudas, plus two vrats.
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 25)));

      final parva = find.byKey(const Key('share-strip-parva'));
      expect(
        find.descendant(of: parva, matching: find.text('पाखी चौदस (शुक्ल)')),
        findsOneWidget,
      );
      final vrat = find.byKey(const Key('share-strip-vrat'));
      expect(
        find.descendant(of: vrat, matching: find.text('भक्ताम्बर व्रत')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: vrat, matching: find.text('+1 और')),
        findsOneWidget,
      );
    });

    testWidgets(
      'is in English on an English phone, the greeting still in Devanagari',
      (tester) async {
        const date = CivilDate(2026, 10, 22);
        final reading = _day(date);
        await _pumpCard(tester, await _content(date, locale: 'en'));

        expect(find.text('जय जिनेन्द्र'), findsOneWidget);
        expect(find.text('Thursday, 22 October 2026'), findsOneWidget);
        expect(find.text('Shukla Ekadashi'), findsOneWidget);
        expect(find.text('Vira Nirvana Samvat 2552'), findsOneWidget);
        expect(find.text('Tithi'), findsOneWidget);
        expect(_line(tester, 'tithi'), contains(', then '));
        expect(find.text('Auspicious Choghadiya'), findsOneWidget);
        expect(find.text('Sunrise'), findsOneWidget);
        expect(
          find.descendant(
            of: _box('sun'),
            matching: _rich(_clock(reading.sunrise, Lang.en)),
          ),
          findsOneWidget,
        );
        expect(find.text('Delhi'), findsOneWidget);
        expect(find.text('Jain Panchang'), findsOneWidget);
      },
    );

    testWidgets('keeps the light Navpad ground on a dark phone', (
      tester,
    ) async {
      tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
      addTearDown(tester.platformDispatcher.clearAllTestValues);
      await _pumpCard(tester, await _content(const CivilDate(2026, 10, 22)));

      final ground = tester.widget<ColoredBox>(
        find.byKey(const Key('share-card')),
      );
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
      final lines = shareText(await _content(const CivilDate(2026, 10, 25)))
          .split('\n');

      expect(
        lines,
        containsAll(['पाखी चौदस (शुक्ल) · पर्व', 'भक्ताम्बर व्रत · +1 और']),
      );
      expect(lines.last, '— जैन पंचांग');
    });
  });

  group('the image', () {
    Future<ui.Image> render(WidgetTester tester, CivilDate date) async {
      final content = await _content(date);
      await tester.pumpWidget(const SizedBox());
      final png = (await tester.runAsync(
        () => renderShareCard(content, view: tester.view),
      ))!;
      expect(
        png.sublist(0, 8),
        Uint8List.fromList([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
      );
      return (await tester.runAsync(() async {
        final codec = await ui.instantiateImageCodec(png);
        return (await codec.getNextFrame()).image;
      }))!;
    }

    testWidgets('is a PNG 1080 wide and at least 1350 tall on a quiet day', (
      tester,
    ) async {
      final image = await render(tester, const CivilDate(2026, 10, 22));

      expect(image.width, 1080);
      expect(image.height, greaterThanOrEqualTo(1350));
    });

    testWidgets('grows taller, never wider, on a day with festivals', (
      tester,
    ) async {
      final quiet = await render(tester, const CivilDate(2026, 10, 22));
      final busy = await render(tester, const CivilDate(2026, 10, 25));

      expect(busy.width, 1080);
      expect(busy.height, greaterThan(quiet.height));
    });
  });
}
