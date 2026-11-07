/// The day as a picture for WhatsApp (mobile-ui-design.md §3.6, DESIGN.md
/// Display brand): the card's words, the card, and its PNG.
library;

import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../format/festival_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../shared/festival_mark.dart';
import '../../shared/panchang_section.dart';
import '../../shared/panchang_symbols.dart';
import '../../theme/navpad.dart';
import '../../theme/theme.dart';

/// The greeting stays in Devanagari on an English card too: it is the greeting itself.
const greeting = 'जय जिनेन्द्र';

typedef CardStrip = ({String title, String subtitle});

/// One element's words, after the zodiac signs (Rashi indices) drawn before them.
typedef CardPart = ({String text, List<int> rashis});

/// A line of the पंचांग box: an element and the one after it.
typedef CardLine = ({String key, String label, List<CardPart> parts});

typedef CardSlot = ({String name, String range});

/// Everything the card and its text say, already in the app's language.
final class ShareCardContent {
  const ShareCardContent({
    required this.lang,
    required this.date,
    required this.tithi,
    required this.month,
    required this.tithiEnds,
    required this.samvat,
    required this.parva,
    required this.vrat,
    required this.sunriseLabel,
    required this.sunrise,
    required this.sunsetLabel,
    required this.sunset,
    required this.samvats,
    required this.panchangTitle,
    required this.thenWord,
    required this.panchang,
    required this.festivalsTitle,
    required this.choghadiyaTitle,
    required this.dayLabel,
    required this.nightLabel,
    required this.dayChoghadiya,
    required this.nightChoghadiya,
    required this.place,
    required this.appName,
  });

  final Lang lang;
  final String date, tithi, month, tithiEnds, samvat, place, appName;
  final CardStrip? parva, vrat;
  final String sunriseLabel, sunsetLabel;
  final ({String period, String time}) sunrise, sunset;

  /// "वीर निर्वाण संवत 2552", then Vikram and Shaka.
  final List<String> samvats;
  final String panchangTitle,
      thenWord,
      festivalsTitle,
      choghadiyaTitle,
      dayLabel,
      nightLabel;
  final List<CardLine> panchang;

  /// Only Amrit, Shubh, Labh and Chal (the user's choice, 2026-11-07).
  final List<CardSlot> dayChoghadiya, nightChoghadiya;
}

ShareCardContent shareCardContent({
  required PanchangDay reading,
  required PanchangSection section,
  required LunarMonth month,
  required List<FestivalOccurrence> festivals,
  required String place,
  required String timezone,
  required AppLocalizations l10n,
}) {
  final lang = l10n.localeName == 'en' ? Lang.en : Lang.hi;
  DateTime wall(DateTime utc) => cityWall(utc, timezone);
  final lines = festivalLines(festivalsOn(festivals, reading.date), lang);
  // As Today's bands say it: the first name, then its kind or how many more.
  CardStrip? strip(List<FestivalLine> shown) => switch (shown) {
    [] => null,
    [final first, ...final rest] => (
      title: first.name,
      subtitle: rest.isEmpty
          ? festivalKindLabel(first.kind, l10n)
          : l10n.festivalsMore(rest.length),
    ),
  };
  final ends = instantPhrase(
    wall(reading.jainTithi.endsAt),
    day: reading.date,
    lang: lang,
  );
  // Non-breaking spaces keep a date, a time, its period word and तक together:
  // a wrap never strands "AM" or "तक".
  String until(String name, DateTime utc) =>
      '$name ${l10n.until(instantPhrase(wall(utc), day: reading.date, lang: lang)).replaceAll(' ', '\u00A0')}';

  CardPart part(String text, [List<int> rashis = const []]) =>
      (text: text, rashis: rashis);
  final [yoga, nextYoga, ...] = section.yogas;
  final [karana, nextKarana, ...] = section.karanas;
  final [moon, nextMoon, ...] = section.moonRashis;
  final nakshatra = reading.nakshatra;
  List<CardSlot> slots({required bool night}) => [
    for (final slot in reading.choghadiya)
      if (slot.isNight == night &&
          slot.name.nature != ChoghadiyaNature.inauspicious)
        (
          name: choghadiyaName(slot.name, lang),
          range: clockRange(
            wall(slot.start),
            wall(slot.end),
            lang,
          ).replaceAll(' ', '\u00A0'),
        ),
  ];
  return ShareCardContent(
    lang: lang,
    date: longDate(reading.date, lang),
    tithi: tithiName(reading.jainTithi.index, lang),
    month: monthName(month, lang),
    tithiEnds: l10n.heroUntil(
      ends,
      tithiName(reading.jainTithi.index % 30 + 1, lang),
    ),
    samvat: samvatLine(
      viraNirvana: reading.viraNirvanaSamvat,
      vikram: reading.vikramSamvat,
      lang: lang,
    ),
    parva: strip([
      for (final l in lines)
        if (!l.kind.isVrat) l,
    ]),
    vrat: strip([
      for (final l in lines)
        if (l.kind.isVrat) l,
    ]),
    sunriseLabel: l10n.sunrise,
    sunrise: clockTime(wall(reading.sunrise), lang),
    sunsetLabel: l10n.sunset,
    sunset: clockTime(wall(reading.sunset), lang),
    samvats: [
      '${l10n.viraNirvanaSamvat} ${reading.viraNirvanaSamvat}',
      '${l10n.vikramSamvat} ${reading.vikramSamvat}',
      '${l10n.shakaSamvat} ${reading.shakaSamvat}',
    ],
    panchangTitle: l10n.panchangHeading,
    thenWord: l10n.thenWord,
    panchang: [
      (
        key: 'tithi',
        label: l10n.tithiLabel,
        parts: [
          part(
            until(
              tithiName(reading.jainTithi.index, lang),
              reading.jainTithi.endsAt,
            ),
          ),
          part(
            until(
              tithiName(section.nextTithi.index, lang),
              section.nextTithi.endsAt,
            ),
          ),
        ],
      ),
      (
        key: 'nakshatra',
        label: l10n.nakshatra,
        parts: [
          part(
            until(
              l10n.nakshatraWithPada(
                nakshatraName(nakshatra.index, lang),
                nakshatra.pada,
              ),
              nakshatra.endsAt,
            ),
            nakshatraRashis(nakshatra.index),
          ),
          part(
            until(
              nakshatraName(section.nextNakshatra.index, lang),
              section.nextNakshatra.endsAt,
            ),
            nakshatraRashis(section.nextNakshatra.index),
          ),
        ],
      ),
      (
        key: 'yoga',
        label: l10n.yogaLabel,
        parts: [
          part(until(yogaName(yoga.index, lang), yoga.endsAt)),
          part(until(yogaName(nextYoga.index, lang), nextYoga.endsAt)),
        ],
      ),
      (
        key: 'karana',
        label: l10n.karanaLabel,
        parts: [
          part(until(karanaName(karana.index, lang), karana.endsAt)),
          part(until(karanaName(nextKarana.index, lang), nextKarana.endsAt)),
        ],
      ),
      (
        key: 'moon-rashi',
        label: l10n.moonRashiLabel,
        parts: [
          part(until(rashiName(moon.index, lang), moon.endsAt)),
          part(rashiName(nextMoon.index, lang)),
        ],
      ),
    ],
    festivalsTitle: l10n.shareFestivalsHeading,
    choghadiyaTitle: l10n.shareChoghadiyaHeading,
    dayLabel: l10n.dayHeading,
    nightLabel: l10n.nightHeading,
    dayChoghadiya: slots(night: false),
    nightChoghadiya: slots(night: true),
    place: place,
    appName: l10n.appTitle,
  );
}

String _clock(({String period, String time}) clock, Lang lang) =>
    lang == Lang.hi
    ? '${clock.period} ${clock.time}'
    : '${clock.time} ${clock.period}';

/// The plain-text version WhatsApp shows as the image's caption.
String shareText(ShareCardContent c) => [
  greeting,
  '${c.date} · ${c.place}',
  '${c.tithi} · ${c.month}',
  c.samvat,
  for (final strip in [c.parva, c.vrat])
    if (strip != null) '${strip.title} · ${strip.subtitle}',
  '${c.sunriseLabel} ${_clock(c.sunrise, c.lang)} · ${c.sunsetLabel} ${_clock(c.sunset, c.lang)}',
  '— ${c.appName}',
].join('\n');

/// 360 dp wide and at least 450 tall (1080 × 1350 px at [_pixelRatio]); the whole day makes it
/// taller, up to [_maxHeight].
const _width = 360.0,
    _minHeight = 450.0,
    _maxHeight = 2400.0,
    _pixelRatio = 3.0;

/// The card in the light scheme whatever the phone's theme, at a fixed text
/// size: it is a picture for someone else's phone.
class ShareCard extends StatelessWidget {
  const ShareCard({super.key, required this.content});

  final ShareCardContent content;

  @override
  Widget build(BuildContext context) {
    final theme = navpadTheme(Brightness.light);
    final n = theme.extension<Navpad>()!;
    final text = theme.textTheme;
    final c = content;
    return Directionality(
      textDirection: TextDirection.ltr,
      child: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.noScaling),
        child: Theme(
          data: theme,
          child: ColoredBox(
            key: const Key('share-card'),
            color: n.ground,
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                minWidth: _width,
                maxWidth: _width,
                minHeight: _minHeight,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Padding(
                    key: const Key('share-header'),
                    padding: const EdgeInsets.fromLTRB(18, 22, 18, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        CustomPaint(
                          size: const Size(28, 22),
                          painter: _Siddhashila(n.ink),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          greeting,
                          style: NavpadType.displayBrand.copyWith(color: n.ink),
                        ),
                        Text(
                          c.date,
                          style: text.bodyLarge!.copyWith(color: n.ink2),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          c.tithi,
                          style: NavpadType.displayHero.copyWith(color: n.ink),
                        ),
                        const SizedBox(height: 4),
                        Text.rich(
                          TextSpan(
                            style: text.bodyLarge!.copyWith(
                              color: n.ink2,
                              height: 1.4,
                            ),
                            children: [
                              TextSpan(
                                text: c.month,
                                style: TextStyle(
                                  color: n.ink,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              TextSpan(text: ' · ${c.tithiEnds}'),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  _Box(
                    key: const Key('share-box-sun'),
                    child: IntrinsicHeight(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Expanded(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                _SunLine(
                                  label: c.sunriseLabel,
                                  clock: c.sunrise,
                                  lang: c.lang,
                                ),
                                _SunLine(
                                  label: c.sunsetLabel,
                                  clock: c.sunset,
                                  lang: c.lang,
                                ),
                              ],
                            ),
                          ),
                          Container(
                            width: 1,
                            color: n.hair,
                            margin: const EdgeInsets.symmetric(horizontal: 10),
                          ),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                for (final samvat in c.samvats)
                                  Text(
                                    samvat,
                                    textAlign: TextAlign.end,
                                    style: text.labelMedium!.copyWith(
                                      color: n.ink,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  _Box(
                    key: const Key('share-box-panchang'),
                    title: c.panchangTitle,
                    child: Column(
                      children: [
                        for (final line in c.panchang)
                          _CardLineView(line: line, thenWord: c.thenWord),
                      ],
                    ),
                  ),
                  if (c.parva != null || c.vrat != null)
                    _Box(
                      key: const Key('share-box-festivals'),
                      title: c.festivalsTitle,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          if (c.parva case final strip?)
                            _FestivalLine(
                              key: const Key('share-strip-parva'),
                              strip: strip,
                              colour: n.red,
                            ),
                          if (c.vrat case final strip?)
                            _FestivalLine(
                              key: const Key('share-strip-vrat'),
                              strip: strip,
                              colour: n.green,
                            ),
                        ],
                      ),
                    ),
                  _Box(
                    key: const Key('share-box-choghadiya'),
                    title: c.choghadiyaTitle,
                    child: IntrinsicHeight(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Expanded(
                            child: _ChoghadiyaColumn(
                              key: const Key('share-choghadiya-day'),
                              label: c.dayLabel,
                              slots: c.dayChoghadiya,
                            ),
                          ),
                          Container(
                            width: 1,
                            color: n.hair,
                            margin: const EdgeInsets.symmetric(horizontal: 8),
                          ),
                          Expanded(
                            child: _ChoghadiyaColumn(
                              key: const Key('share-choghadiya-night'),
                              label: c.nightLabel,
                              slots: c.nightChoghadiya,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Divider(height: 1, thickness: 1, color: n.hair),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 10, 18, 14),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            c.place,
                            style: text.labelMedium!.copyWith(color: n.ink3),
                          ),
                        ),
                        Text(
                          c.appName,
                          style: text.labelMedium!.copyWith(color: n.ink3),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// A part of the card in its own rounded box, its title on a red tab across
/// the top edge, as in the WhatsApp Panchang cards the user modelled it on.
class _Box extends StatelessWidget {
  const _Box({super.key, this.title, required this.child});

  final String? title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    return Padding(
      padding: EdgeInsets.fromLTRB(14, title == null ? 14 : 22, 14, 0),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(
            padding: EdgeInsets.fromLTRB(12, title == null ? 10 : 18, 12, 10),
            decoration: BoxDecoration(
              color: n.surface,
              border: Border.all(color: n.hair),
              borderRadius: BorderRadius.circular(12),
            ),
            child: child,
          ),
          if (title case final title?)
            Positioned(
              top: -11,
              left: 0,
              right: 0,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: n.red,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.labelMedium!
                        .copyWith(color: n.onRed, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// A label, then its element and the one after it: "द्वितीया … तक, फिर तृतीया … तक".
class _CardLineView extends StatelessWidget {
  const _CardLineView({required this.line, required this.thenWord});

  final CardLine line;
  final String thenWord;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final style = Theme.of(context).textTheme.bodyMedium!
        .copyWith(color: n.ink, height: 1.35);
    return Padding(
      key: Key('share-line-${line.key}'),
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 78,
            child: Text(
              line.label,
              style: style.copyWith(color: n.red, fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(
            child: Text.rich(
              TextSpan(
                style: style,
                children: [
                  for (final (k, part) in line.parts.indexed) ...[
                    if (k > 0) TextSpan(text: ', $thenWord '),
                    for (final (g, rashi) in part.rashis.indexed)
                      WidgetSpan(
                        alignment: PlaceholderAlignment.middle,
                        child: Padding(
                          padding: EdgeInsets.only(
                            right: g == part.rashis.length - 1 ? 4 : 1,
                          ),
                          child: PanchangSymbol(
                            zodiacGlyph(rashi),
                            size: style.fontSize! * glyphScale,
                            color: n.ink,
                          ),
                        ),
                      ),
                    TextSpan(text: part.text),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// A festival line in the box: the first name in its band colour, then its kind or how many more.
class _FestivalLine extends StatelessWidget {
  const _FestivalLine({super.key, required this.strip, required this.colour});

  final CardStrip strip;
  final Color colour;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            strip.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: text.bodyMedium!.copyWith(
              color: colour,
              fontWeight: FontWeight.w600,
            ),
          ),
          Text(
            strip.subtitle,
            style: text.labelMedium!.copyWith(color: n.ink2),
          ),
        ],
      ),
    );
  }
}

/// Day or night: the auspicious Choghadiya, each with its time.
class _ChoghadiyaColumn extends StatelessWidget {
  const _ChoghadiyaColumn({
    super.key,
    required this.label,
    required this.slots,
  });

  final String label;
  final List<CardSlot> slots;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final style = Theme.of(context).textTheme.labelMedium!
        .copyWith(color: n.ink);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          label,
          style: style.copyWith(color: n.ink2, fontWeight: FontWeight.w600),
        ),
        for (final (i, slot) in slots.indexed)
          Padding(
            key: Key('share-choghadiya-slot-$i'),
            padding: const EdgeInsets.only(top: 3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  slot.name,
                  style: style.copyWith(
                    color: n.green,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    slot.range,
                    textAlign: TextAlign.end,
                    style: style,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _SunLine extends StatelessWidget {
  const _SunLine({
    required this.label,
    required this.clock,
    required this.lang,
  });

  final String label;
  final ({String period, String time}) clock;
  final Lang lang;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final period = TextSpan(
      text: clock.period,
      style: TextStyle(color: n.ink2, fontWeight: FontWeight.w400),
    );
    final time = TextSpan(
      text: clock.time,
      style: const TextStyle(fontWeight: FontWeight.w600),
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Expanded(
            child: Text(label, style: text.bodyMedium!.copyWith(color: n.ink)),
          ),
          // DESIGN.md's Time Column Rule: the period word lighter, before the value in Hindi.
          // Flexible: in half the box a long period word wraps rather than overflows.
          Flexible(
            child: Text.rich(
              TextSpan(
                style: text.bodyMedium!.copyWith(color: n.ink),
                children: lang == Lang.hi
                    ? [period, const TextSpan(text: ' '), time]
                    : [time, const TextSpan(text: ' '), period],
              ),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }
}

/// The siddhashila mark: the crescent of the abode of the liberated, with a soul above it.
class _Siddhashila extends CustomPainter {
  const _Siddhashila(this.colour);

  final Color colour;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = colour;
    canvas.drawCircle(
      Offset(size.width / 2, size.height * 0.23),
      size.width * 0.115,
      paint,
    );
    final crescent = Path()
      ..moveTo(size.width * 0.1, size.height * 0.45)
      ..quadraticBezierTo(
        size.width / 2,
        size.height * 1.1,
        size.width * 0.9,
        size.height * 0.45,
      );
    canvas.drawPath(
      crescent,
      paint
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.4
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(_Siddhashila old) => old.colour != colour;
}

/// Paints the card away from the screen, in its own pipeline, and encodes it as a PNG.
Future<Uint8List> renderShareCard(
  ShareCardContent content, {
  required ui.FlutterView view,
}) async {
  final boundary = RenderRepaintBoundary();
  final renderView = RenderView(
    view: view,
    child: RenderPositionedBox(alignment: Alignment.topLeft, child: boundary),
    configuration: const ViewConfiguration(
      logicalConstraints: BoxConstraints(
        maxWidth: _width,
        maxHeight: _maxHeight,
      ),
    ),
  );
  final pipeline = PipelineOwner()..rootNode = renderView;
  renderView.prepareInitialFrame();
  final build = BuildOwner(focusManager: FocusManager());
  final root = RenderObjectToWidgetAdapter<RenderBox>(
    container: boundary,
    child: ShareCard(content: content),
  ).attachToRenderTree(build);
  build
    ..buildScope(root)
    ..finalizeTree();
  pipeline
    ..flushLayout()
    ..flushCompositingBits()
    ..flushPaint();
  final image = await boundary.toImage(pixelRatio: _pixelRatio);
  try {
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    return bytes!.buffer.asUint8List();
  } finally {
    image.dispose();
  }
}
